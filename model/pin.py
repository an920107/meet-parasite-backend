from datetime import datetime
from pydantic import BaseModel


class Pin(BaseModel):
    message: str
    created_time: datetime
    recipients: list[str]
