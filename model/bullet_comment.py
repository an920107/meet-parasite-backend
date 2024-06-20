from datetime import datetime

from pydantic import BaseModel


class BulletComment(BaseModel):
    anonymous: bool
    type: int
    message: str
    emoji: str
    created_time: datetime
    recipients: list[str]
