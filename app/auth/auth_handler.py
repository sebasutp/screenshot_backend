import time
from typing import Dict, Annotated
from datetime import datetime, timedelta, timezone
from typing import Union

import jwt
from decouple import config
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi import Depends, HTTPException, status

import app.model as model
import app.auth.crypto as crypto


JWT_SECRET = "96706f2fb5daf56405a9f2554399e53e93fe2b5f22c1b6bfc48c1d1f77a79151"
JWT_ALGORITHM = "HS256"

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def check_and_get_user(data: model.UserLogin, session: model.Session):
    user = session.query(model.User).filter(model.User.email == data.email).first()
    if user:
        if crypto.verify_password(data.password, user.password):
            return user
    return None

def create_access_token(user: model.User, expires_delta: Union[timedelta, None] = None):
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
    try:
        decoded_token = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return decoded_token
    except:
        return None

async def get_current_user_id(token: Annotated[str, Depends(oauth2_scheme)]):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        decoded_token = decode_jwt(token)
        if not decoded_token:
            raise credentials_exception
        user_id = model.UserId(**decoded_token['sub'])
        return user_id
    except:
        raise credentials_exception
