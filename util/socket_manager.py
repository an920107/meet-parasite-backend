import asyncio
from datetime import datetime

from fastapi import WebSocket
from pydantic import BaseModel, Field, field_serializer

from util.token import JwtPayload, Token


class Connection:
    def __init__(self, websocket: WebSocket, *, room: str, name: str):
        self.websocket = websocket
        self.name = name
        self.room = room
        self.created_time = datetime.now().astimezone()


class Message(BaseModel):
    event: str
    room: str
    sender_id: int
    sender_name: str
    data: BaseModel | None
    created_time: datetime = Field(
        ..., default_factory=lambda: datetime.now().astimezone()
    )

    @field_serializer("data")
    def serializer_data(self, data: BaseModel, _info):
        return None if data is None else data.model_dump()


class SocketManager:
    def __init__(self):
        self.connections: dict[int, Connection] = {}
        self.queue = asyncio.Queue()

    async def connect(
        self, websocket: WebSocket, *, room: str, name: str
    ) -> Connection:
        await websocket.accept()
        connection = Connection(websocket, room=room, name=name)
        jwt_token = Token.generate_jwt(
            JwtPayload(
                id=id(connection),
                name=name,
                room=room,
                created_time=connection.created_time,
            )
        )
        await websocket.send_json({"id": id(connection), "token": jwt_token})
        self.connections[id(connection)] = connection
        return connection

    def disconnect(self, connection: Connection) -> None:
        self.connections.pop(id(connection))

    async def broadcast(self, message: Message) -> None:
        for connection in self.connections.values():
            if connection.room == message.room:
                await connection.websocket.send_text(message.model_dump_json())

    async def send_from_queue(self) -> None:
        """
        Broadcast message to all connections in the room when the queue is not empty.
        """
        while True:
            message = await self.queue.get()
            await self.broadcast(message)

    async def add_message(
        self,
        *,
        sender_id: str,
        event: str,
        data: object | None,
        recipients: list[int] = [],
    ) -> None:
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

    def get_connection(
        self,
        id: int,
        *,
        created_time: datetime | None = None,
    ) -> Connection | None:
        connection = self.connections.setdefault(id, None)
        if connection is None:
            return None
        if created_time is None:
            return connection
        return (
            None
            if connection.created_time.timestamp() != created_time.timestamp()
            else connection
        )
