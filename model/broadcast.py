from pydantic import BaseModel


class Broadcast(BaseModel):
    message: str
