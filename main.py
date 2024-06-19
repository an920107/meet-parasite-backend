import asyncio
import ctypes
from datetime import datetime
from typing import Annotated
from fastapi import Body, FastAPI, Response, WebSocket, WebSocketDisconnect
from fastapi.concurrency import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware


class Connection:
    def __init__(self, websocket: WebSocket, *, room: str, name: str):
        self.websocket = websocket
        self.name = name
        self.room = room


class Message:
    def __init__(self, room: str, sender: str, message: str):
        self.room = room
        self.sender = sender
        self.content = message


class SocketManager:
    def __init__(self):
        self.connections: dict[str, list[Connection]] = {}
        self.queue = asyncio.Queue()

    async def connect(
        self, websocket: WebSocket, *, room: str, name: str
    ) -> Connection:
        await websocket.accept()
        connection = Connection(websocket, room=room, name=name)
        await websocket.send_json({"id": id(connection)})
        self.connections.setdefault(room, []).append(connection)
        return connection

    def disconnect(self, connection: Connection) -> None:
        self.connections.get(connection.room).remove(connection)

    async def broadcast(self, message: Message) -> None:
        for connection in self.connections.setdefault(message.room, []):
            await connection.websocket.send_json({
                "id": id(connection),
                "datetime": datetime.now().isoformat(),
                "sender": message.sender,
                "data": message.content,
            })

    async def send_from_queue(self) -> None:
        while True:
            message = await self.queue.get()
            await self.broadcast(message)

    async def add_message(self, message: Message) -> None:
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
    try:
        connection = await manager.connect(websocket, room=room, name=name)
        await manager.add_message(Message(room, name, f"[{name} has joined]"))
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(connection)
        await manager.add_message(Message(room, name, f"[{name} has left]"))


@app.post("/broadcast")
async def broadcast(id: int, message: Annotated[str, Body(embed=True)]):
    try:
        connection: Connection = ctypes.cast(id, ctypes.py_object).value
        await manager.add_message(Message(connection.room, connection.name, message))
    except AttributeError | ValueError:
        return Response(content=None, status_code=404)
    return Response(content=None, status_code=201)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
