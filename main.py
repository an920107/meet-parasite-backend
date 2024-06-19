import asyncio
from fastapi import FastAPI, Response, WebSocket
from fastapi.concurrency import asynccontextmanager


class SocketManager:
    def __init__(self):
        self.connections: list[WebSocket] = []
        self.queue = asyncio.Queue()

    async def connect(self, websocket: WebSocket):
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


@app.get("/")
def index():
    return Response(content="Hello world!")


@app.websocket("/socket")
async def create_websocket(websocket: WebSocket, id: str):
    print(id)
    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except:
        manager.disconnect(websocket)


@app.post("/yield")
async def post_yield(message: str):
    await manager.add_message(message)
    return Response(content=None, status_code=201)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
