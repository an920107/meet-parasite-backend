import asyncio
from typing import Annotated
from wsgiref.headers import Headers

from fastapi import (
    Depends,
    FastAPI,
    HTTPException,
    Header,
    Response,
    WebSocket,
    WebSocketDisconnect,
)
from fastapi.concurrency import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
import jwt
from pydantic import BaseModel

from model.broadcast import Broadcast
from model.bullet_comment import BulletComment
from model.pin import Pin
from model.timer import Timer
from util.socket_manager import SocketManager
from util.token import JwtPayload, Token

manager = SocketManager()


@asynccontextmanager
async def lifespan(app: FastAPI):
    asyncio.create_task(manager.send_from_queue())
    yield


app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

security = HTTPBearer()


async def verify_credential(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)]
) -> JwtPayload:

    splitted_credentials = credentials.credentials.strip(" ").split(" ")
    if credentials.scheme != "Bearer" or len(splitted_credentials) != 1:
        raise HTTPException(status_code=403, detail="Unknown credential scheme")

    try:
        jwt_payload = Token.decode_jwt(splitted_credentials[0])
    except jwt.exceptions.DecodeError:
        raise HTTPException(status_code=401, detail="Invalid credential")

    if (
        manager.get_connection(
            jwt_payload.id,
            created_time=jwt_payload.created_time,
        )
        is None
    ):
        raise HTTPException(status_code=401, detail="Invalid credential")

    return jwt_payload


@app.get("/")
def index():
    return Response(content="Hello world!")


@app.websocket("/socket")
async def create_websocket(websocket: WebSocket, room: str, name: str):
    try:
        connection = await manager.connect(websocket, room=room, name=name)
        await manager.add_message(
            sender_id=id(connection),
            event="join",
            data=None,
        )
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        await manager.add_message(
            sender_id=id(connection),
            event="leave",
            data=None,
        )
        manager.disconnect(connection)


@app.get("/participant")
async def get_participants():
    return Response(content=None, status_code=204)


async def general_post(sender_id: int, data: BaseModel, event: str) -> Response:
    try:
        await manager.add_message(
            sender_id=sender_id,
            event=event,
            data=data,
        )
    except KeyError:
        raise HTTPException(status_code=404, detail="Invalid sender ID")
    return Response(content=None, status_code=201)


@app.post("/broadcast", status_code=201)
async def broadcast(
    payload: Broadcast,
    jwt_payload: Annotated[JwtPayload, Depends(verify_credential)],
):
    return await general_post(jwt_payload.id, payload, "broadcast")


@app.post("/bullet-comment", status_code=201)
async def bullet_comment(
    payload: BulletComment,
    jwt_payload: Annotated[JwtPayload, Depends(verify_credential)],
):
    return await general_post(jwt_payload.id, payload, "bullet_comment")

@app.post("/timer", status_code=201)
async def bullet_comment(
    payload: Timer,
    jwt_payload: Annotated[JwtPayload, Depends(verify_credential)],
):
    return await general_post(jwt_payload.id, payload, "timer")

@app.post("/pin", status_code=201)
async def bullet_comment(
    payload: Pin,
    jwt_payload: Annotated[JwtPayload, Depends(verify_credential)],
):
    return await general_post(jwt_payload.id, payload, "pin")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
