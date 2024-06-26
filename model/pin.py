from datetime import datetime
from pydantic import BaseModel


class Pin(BaseModel):
    sender: str
    message: str
