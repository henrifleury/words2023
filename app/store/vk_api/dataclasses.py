from dataclasses import dataclass
from typing import Optional


@dataclass
class UpdateObject:
    id: int
    user_id: int
    body: str
    peer_id: int

@dataclass
class Update:
    type: str
    object: UpdateObject


@dataclass
class Message:
    user_id: Optional[int]
    text: Optional[str]
    keyboard: Optional[str]
    peer_id: Optional[int]