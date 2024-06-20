import secrets
from datetime import datetime

import jwt
from pydantic import BaseModel, field_serializer


class JwtPayload(BaseModel):
    id: int
    name: str
    room: str
    created_time: datetime

    @field_serializer("created_time")
    def serialize_created_time(self, created_time: datetime, _info) -> float:
        return created_time.timestamp()


_SECRET = secrets.token_urlsafe()


class Token:

    @staticmethod
    def generate_jwt(payload: JwtPayload) -> str:
        return jwt.encode(
            payload=payload.model_dump(),
            key=_SECRET,
            algorithm="HS256",
        )

    @staticmethod
    def decode_jwt(token: str) -> JwtPayload:
        decoded = jwt.decode(
            jwt=token,
            key=_SECRET,
            algorithms=["HS256"],
        )
        return JwtPayload(**decoded)
