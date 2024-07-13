from fastapi import FastAPI, Body, Depends, HTTPException, status
from typing import Annotated
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm

from sqlmodel import Session, SQLModel, select
from datetime import timedelta

import app.model as model
import app.auth.auth_handler as auth_handler
import app.auth.crypto as crypto

app_obj = FastAPI()

@app_obj.on_event("startup")
def on_startup():
    model.create_db_and_tables()

# route handlers

@app_obj.post("/token")
async def login(form_data: Annotated[OAuth2PasswordRequestForm, Depends()], session: Session = Depends(model.get_db_session)):
    user = model.UserLogin(email=form_data.username, password=form_data.password)
    db_user = auth_handler.check_and_get_user(user, session)
    if not db_user:
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    token = auth_handler.create_access_token(db_user, timedelta(minutes=30))
    return model.Token(access_token=token, token_type="bearer")


@app_obj.get("/screenshots", tags=["screenshots"], response_model=list[model.Screenshot])
async def get_screenshots(
    *,
    session: Session = Depends(model.get_db_session),
    current_user_id: model.UserId = Depends(auth_handler.get_current_user_id)):
    statement = select(model.Screenshot).where(model.Screenshot.owner_id == current_user_id.id)
    return session.exec(statement)


@app_obj.get("/screenshots/{id}", tags=["screenshots"], response_model=model.Screenshot)
async def get_single_screenshot(*, session: Session = Depends(model.get_db_session), id: str):
    q = select(model.Screenshot).where(model.Screenshot.external_id == id)
    screenshot = session.exec(q).first()
    if not screenshot:
        raise HTTPException(status_code=404, detail="Screenshot not found")
    return screenshot


@app_obj.post("/screenshots", tags=["screenshots"], response_model=model.Screenshot)
async def add_screenshots(
    *,
    session: Session = Depends(model.get_db_session),
    current_user_id: model.UserId = Depends(auth_handler.get_current_user_id),
    screenshot: model.ScreenshotCreate):
    screenshot_db = model.Screenshot.model_validate(screenshot, update={"owner_id": current_user_id.id})
    screenshot_db.external_id = crypto.generate_random_base64_string(32)
    session.add(screenshot_db)
    session.commit()
    session.refresh(screenshot_db)
    return screenshot_db

@app_obj.post("/user/signup", tags=["user"])
async def create_user(*, session: Session = Depends(model.get_db_session), user: model.UserCreate = Body(...)):
    db_user = model.User.model_validate(user)
    # Hash password before saving it
    db_user.password = crypto.get_password_hash(db_user.password)
    session.add(db_user)
    session.commit()
    session.refresh(db_user)
    return model.Token(access_token=auth_handler.create_access_token(db_user), token_type="bearer")
