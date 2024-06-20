import asyncio
from datetime import datetime

from fastapi import WebSocket
from pydantic import BaseModel, Field, field_serializer


class Connection:
    def __init__(self, websocket: WebSocket, *, room: str, name: str):
        self.websocket = websocket
        self.name = name
        self.room = room


class Message(BaseModel):
    event: str
    room: str
    sender_id: int
    sender_name: str
    data: BaseModel
    created_time: datetime = Field(..., default_factory=lambda: datetime.now().astimezone())
    
    @field_serializer("data")
    def serializer_data(self, data: BaseModel, _info):
        return data.model_dump()


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
                await connection.websocket.send_text(message.model_dump_json())

    async def send_from_queue(self) -> None:
        while True:
            message = await self.queue.get()
            await self.broadcast(message)

    async def add_message(self, *, sender_id: str, event: str, data: object) -> None:
        connection = self.connections[sender_id]
        await self.queue.put(
            Message(
                event=event,
                room=connection.room,
                sender_id=sender_id,
                sender_name=connection.name,
                data=data,
            )
        )
