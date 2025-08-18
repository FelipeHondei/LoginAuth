from pydantic import BaseModel, EmailStr, Field
from typing import Optional


class RegisterRequest(BaseModel):
    name: str = Field(min_length=2, max_length=80)
    email: EmailStr
    password: str = Field(min_length=6, max_length=128)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TaskCreate(BaseModel):
    title: str = Field(min_length=1, max_length=120)
    description: Optional[str] = Field(default=None, max_length=1000)


class TaskUpdate(BaseModel):
    title: Optional[str] = Field(default=None, min_length=1, max_length=120)
    description: Optional[str] = Field(default=None, max_length=1000)
    done: Optional[bool] = None


class UserOut(BaseModel):
    id: int
    name: str
    email: EmailStr


class TaskOut(BaseModel):
    id: int
    title: str
    description: Optional[str]
    done: bool


