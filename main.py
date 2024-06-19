import asyncio
from typing import Annotated
from fastapi import Body, FastAPI, Response, WebSocket
from fastapi.concurrency import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware


class SocketManager:
    def __init__(self):
        self.connections: list[WebSocket] = []
        self.queue = asyncio.Queue()

    async def connect(self, websocket: WebSocket, *, room: str, name: str):
        await websocket.accept()
        self.connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.connections.remove(websocket)

    async def broadcast(self, message: str):
        for connection in self.connections:
            await connection.send_text(message)

    async def send_from_queue(self):
        while True:
            message = await self.queue.get()
            await self.broadcast(message)

    async def add_message(self, message: str):
        await self.queue.put(message)


manager = SocketManager()


@asynccontextmanager
async def lifespan(app: FastAPI):
    asyncio.create_task(manager.send_from_queue())
    yield


app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def index():
    return Response(content="Hello world!")


@app.websocket("/socket")
async def create_websocket(websocket: WebSocket, room: str, name: str):
    print(room, name)
    await manager.connect(websocket, room=room, name=name)
    try:
        while True:
            await websocket.receive_text()
    except:
        manager.disconnect(websocket)


@app.post("/broadcast")
async def broadcast(message: Annotated[str, Body(embed=True)]):
    await manager.add_message(message)
    return Response(content=None, status_code=201)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
