import asyncio
from datetime import datetime
import json
from fastapi import WebSocket


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
        self.created_time = datetime.now()


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
                        "sender_id": message.sender_id,
                        "sender": message.sender,
                        "server_received_time": message.created_time.isoformat(),
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