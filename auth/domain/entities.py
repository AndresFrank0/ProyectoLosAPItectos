# src/auth/domain/entities.py
from sqlmodel import Field, SQLModel
from typing import Optional

class UserBase(SQLModel):
    email: str = Field(unique=True, index=True)
    name: str
    role: str = Field(default="admin") # 'client' or 'admin'

class User(UserBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    hashed_password: str

class UserCreate(UserBase):
    password: str

class UserPublic(SQLModel):
    id: int
    email: str
    name: str
    role: str = "client"

class Token(SQLModel):
    access_token: str
    token_type: str = "bearer"

class TokenData(SQLModel):
    email: Optional[str] = None
    scopes: list[str] = []