import asyncio
import ctypes
import json
from datetime import datetime
from typing import Annotated

from fastapi import Body, FastAPI, Response, WebSocket, WebSocketDisconnect
from fastapi.concurrency import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware

from model.broadcast import Broadcast
from util.socket_manager import SocketManager

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
        await manager.add_message(
            sender_id=id(connection),
            event="info",
            data=Broadcast(
                message=f"{name} has joined the room.",
            ),
        )
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        await manager.add_message(
            sender_id=id(connection),
            event="info",
            data=Broadcast(
                message=f"{name} has joined the room.",
            ),
        )
        manager.disconnect(connection)


@app.post("/broadcast")
async def broadcast(id: int, message: Annotated[str, Body(embed=True)]):
    try:
        await manager.add_message(
            sender_id=id,
            event="broadcast",
            data=Broadcast(message=message),
        )
    except KeyError:
        return Response(content=None, status_code=404)
    return Response(content=None, status_code=201)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
