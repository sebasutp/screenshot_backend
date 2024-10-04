""" Model classes and data persistence.
"""

import os
from typing import Optional, Union

from pydantic import BaseModel, EmailStr
from sqlmodel import Field, Session, SQLModel, create_engine
from datetime import datetime

connect_args = {"check_same_thread": False}
engine = create_engine(
    os.getenv("DB_URL"),
    echo=True,
    connect_args=connect_args)

def get_db_session():
    """Returns DB session."""
    with Session(engine) as session:
        yield session

def create_db_and_tables():
    """Creates database with schema."""
    SQLModel.metadata.create_all(engine)

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Union[str, None] = None

class UserLogin(SQLModel):
    email: EmailStr = Field(...)
    password: str = Field(...)

class UserId(SQLModel):
    id: int
    email: EmailStr

class UserCreate(UserLogin):
    fullname: Optional[str] = Field(...)

class User(UserCreate, table=True):
    id: int = Field(default=None, primary_key=True)
    #screenshots: list["Screenshot"] = Relationship(back_populates="owner")

class ApiTokenCreate(SQLModel):
    name: str = Field(...)
    token: str = Field(...)

class ApiToken(ApiTokenCreate, table=True):
    id: int = Field(default=None, primary_key=True)
    owner_id: int | None = Field(default=None, foreign_key="user.id")

class ScreenshotCreate(SQLModel):
    url: str = Field(...)
    img: str = Field(...)

class ScreenshotBase(ScreenshotCreate):
    owner_id: int | None = Field(default=None, foreign_key="user.id")
    external_id: str = Field(default = None)
    created_on: datetime
    #owner: User | None = Relationship(back_populates="screenshots")

class Screenshot(ScreenshotBase, table=True):
    id: int = Field(default=None, primary_key=True)
