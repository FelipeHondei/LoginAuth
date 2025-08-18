from dataclasses import dataclass
from typing import Optional


@dataclass
class User:
    id: int
    name: str
    email: str
    password_hash: str


@dataclass
class Task:
    id: int
    user_id: int
    title: str
    description: Optional[str]
    done: bool


