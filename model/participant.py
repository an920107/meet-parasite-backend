from pydantic import BaseModel


class Participant(BaseModel):
    id: int
    name: str
