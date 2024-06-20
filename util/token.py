import secrets
from datetime import datetime

import jwt
from pydantic import BaseModel, field_serializer


class JwtPayload(BaseModel):
    id: int
    name: str
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

    @staticmethod
    def decode_jwt_from_header(header: str | None) -> JwtPayload | None:
        if header is None:
            return None
        header_splitted = header.split(" ")
        if len(header_splitted)!= 2 or header_splitted[0]!= "Bearer":
            return None
        try:
            return Token.decode_jwt(header_splitted[1])
        except jwt.exceptions.DecodeError as e:
            return None
