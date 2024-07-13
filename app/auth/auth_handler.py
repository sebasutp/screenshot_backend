""" Handles authentication.
"""

import os
from datetime import datetime, timedelta, timezone
from typing import Annotated, Union

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlmodel import select

from app import model
from app.auth import crypto

JWT_SECRET = os.getenv("JWT_SECRET")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


def check_and_get_user(data: model.UserLogin, session: model.Session):
    """ Returns the User object if the credentials are correct or None.
    """
    q = select(model.User).where(model.User.email == data.email)
    user = session.exec(q).first()
    if user:
        if crypto.verify_password(data.password, user.password):
            return user
    return None


def create_access_token(user: model.User, expires_delta: Union[timedelta, None] = None):
    """ Create JWT access token.
    """
    to_encode = {
        "sub": {'id': user.id, 'email': user.email}
    }
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=30)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)
    return encoded_jwt


def decode_jwt(token: str) -> dict:
    """ Decodes JWT token.
    """
    try:
        decoded_token = jwt.decode(
            token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return decoded_token
    except jwt.InvalidTokenError:
        return None


async def get_current_user_id(token: Annotated[str, Depends(oauth2_scheme)]):
    """ Dependency for authentication that returns the user id.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    decoded_token = decode_jwt(token)
    if not decoded_token:
        raise credentials_exception
    user_id = model.UserId(**decoded_token['sub'])
    return user_id
