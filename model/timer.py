from datetime import datetime
from pydantic import BaseModel


class Timer(BaseModel):
    countdown: int
    created_time: datetime
    recipients: list[str]
