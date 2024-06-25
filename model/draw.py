from pydantic import BaseModel


class Draw(BaseModel):
    recipient: str
