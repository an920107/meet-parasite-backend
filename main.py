import asyncio
import ctypes
from datetime import datetime
import json
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
    def __init__(self, *, sender_id: int, room: str, sender: str, data: object):
        self.room = room
        self.sender_id = sender_id
        self.sender = sender
        self.content = data


class SocketManager:
    def __init__(self):
        self.connections: dict[int, Connection] = {}
        self.queue = asyncio.Queue()

    async def connect(
        self, websocket: WebSocket, *, room: str, name: str
    ) -> Connection:
        await websocket.accept()
        connection = Connection(websocket, room=room, name=name)
        await websocket.send_json({"id": id(connection)})
        self.connections[id(connection)] = connection
        return connection

    def disconnect(self, connection: Connection) -> None:
        self.connections.pop(id(connection))

    async def broadcast(self, message: Message) -> None:
        for connection in self.connections.values():
            if connection.room == message.room:
                await connection.websocket.send_json(
                    {
                        "id": message.sender_id,
                        "datetime": datetime.now().isoformat(),
                        "sender": message.sender,
                        "data": (
                            message.content
                            if type(message.content) is str
                            else json.loads(json.dumps(message.content))
                        ),
                    }
                )

    async def send_from_queue(self) -> None:
        while True:
            message = await self.queue.get()
            await self.broadcast(message)

    async def add_message(self, sender_id: str, data: object) -> None:
        connection = self.connections[sender_id]
        await self.queue.put(
            Message(
                sender_id=sender_id,
                room=connection.room,
                sender=connection.name,
                data=data,
            )
        )


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
        await manager.add_message(id(connection), {
            "event": "info",
            "message": f"{name} has joined the room.",
        })
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        await manager.add_message(id(connection), {
            "event": "info",
            "message": f"{name} is leaving the room."
        })
        manager.disconnect(connection)


@app.post("/broadcast")
async def broadcast(id: int, message: Annotated[str, Body(embed=True)]):
    try:
        await manager.add_message(
            id,
            {
                "event": "broadcast",
                "message": message,
            },
        )
    except KeyError:
        return Response(content=None, status_code=404)
    return Response(content=None, status_code=201)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
