from pydantic import BaseModel


class Draw(BaseModel):
    target: str
