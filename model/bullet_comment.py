from datetime import datetime

from pydantic import BaseModel


class BulletComment(BaseModel):
    anonymous: bool
    fromUser: str
    type: int
    message: str
    emoji: str
    created_time: datetime
    recipients: list[str]
