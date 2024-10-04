"""API methods."""

from datetime import timedelta, datetime
from typing import Annotated

from fastapi import Body, Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from sqlmodel import Session, select

from app.auth import auth_handler
from app.auth import crypto
from app import model


app_obj = FastAPI()
app_obj.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,  # Set to True if cookies are needed
    allow_methods=["*"],  # Allow all methods (GET, POST, etc.)
    allow_headers=["*"],  # Allow all headers
)


@app_obj.on_event("startup")
def on_startup():
    model.create_db_and_tables()

# route handlers


@app_obj.post("/token")
async def login(
        form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
        session: Session = Depends(model.get_db_session)):
    """
    Login API to authenticate a user and generate an access token.

    This function takes user credentials from the request body
    and validates them against the database.
    If the credentials are valid, it generates an access token
    with a specific expiration time 
    and returns it along with the token type.

    Args:
        form_data: An instance of `OAuth2PasswordRequestForm` containing
            user credentials.
            Retrieved from the request body using Depends.
        session: A SQLAlchemy database session object. Obtained using
            Depends from `model.get_db_session`.

    Raises:
        HTTPException: If the username or password is incorrect (400 Bad Request).

    Returns:
        A `model.Token` object containing the access token and token type.
    """
    user = model.UserLogin(email=form_data.username,
                        password=form_data.password)
    db_user = auth_handler.check_and_get_user(user, session)
    if not db_user:
        raise HTTPException(
            status_code=400, detail="Incorrect username or password")
    token = auth_handler.create_access_token(db_user, timedelta(minutes=30))
    return model.Token(access_token=token, token_type="bearer")


@app_obj.get("/screenshots", tags=["screenshots"], response_model=list[model.Screenshot])
async def get_screenshots(
    num_screenshots: int = 3,
    session: Session = Depends(model.get_db_session),
    current_user_id: model.UserId = Depends(auth_handler.get_current_user_id)):
    """
    Retrieves a list of screenshots owned by the currently authenticated user.

    This API endpoint fetches all screenshots from the database that
    belong to the user identified by the access token provided in the
    request. It requires user authentication 
    through the `Depends` dependency on `auth_handler.get_current_user_id`.

    Args:
        session: A SQLAlchemy database session object. Obtained using
            Depends from `model.get_db_session`.
        current_user_id: An instance of `model.UserId` containing the
            authenticated user's ID. 
            Retrieved using Depends from `auth_handler.get_current_user_id`.

    Returns:
        A list of `model.Screenshot` objects representing the user's screenshots.
    """
    statement = select(model.Screenshot).where(
        model.Screenshot.owner_id == current_user_id.id).order_by(
            model.Screenshot.created_on.desc()
        ).limit(num_screenshots)
    return session.exec(statement)


@app_obj.get("/screenshots/{screenshot_id}", tags=["screenshots"], response_model=model.Screenshot)
async def get_single_screenshot(
    *,
    session: Session = Depends(model.get_db_session),
    screenshot_id: str):
    """
    Retrieves a specific screenshot by its external ID.

    This API endpoint fetches a single screenshot identified by
    the provided `screenshot_id` 
    from the database. It checks if the screenshot exists and raises
    a 404 Not Found exception if it's not found.

    Args:
        session: A SQLAlchemy database session object. Obtained using
            Depends from `model.get_db_session`.
        screenshot_id: The external ID of the screenshot to retrieve.

    Returns:
        A single `model.Screenshot` object if the screenshot is found, 
        otherwise returns None.

    Raises:
        HTTPException: If the screenshot with the provided ID is not found (404 Not Found).
    """
    q = select(model.Screenshot).where(
        model.Screenshot.external_id == screenshot_id)
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
    """
    Creates a new screenshot for the currently authenticated user.

    This API endpoint allows users to add new screenshots. It requires user
    authentication through the `Depends` dependency on
    `auth_handler.get_current_user_id`. The provided 
    `screenshot` data is validated against the `model.ScreenshotCreate` schema.

    Args:
        session: A SQLAlchemy database session object. Obtained using 
            Depends from `model.get_db_session`.
        current_user_id: An instance of `model.UserId` containing 
            the authenticated user's ID. 
            Retrieved using Depends from `auth_handler.get_current_user_id`.
        screenshot: An instance of `model.ScreenshotCreate` containing the
            data for the new screenshot.

    Returns:
        A `model.Screenshot` object representing the newly created screenshot.
    """
    screenshot_db = model.Screenshot.model_validate(
        screenshot, update={
            "owner_id": current_user_id.id,
            "created_on": datetime.now()
            })
    screenshot_db.external_id = crypto.generate_random_base64_string(32)
    session.add(screenshot_db)
    session.commit()
    session.refresh(screenshot_db)
    return screenshot_db


@app_obj.post("/user/signup", tags=["user"])
async def create_user(
    *,
    session: Session = Depends(model.get_db_session),
    user: model.UserCreate = Body(...)):
    """
    Creates a new user account.

    This API endpoint allows users to register and create new accounts. The
    provided `user` data is validated against the `model.UserCreate` schema. 
    The password is hashed before saving it to the database for security 
    reasons.

    Args:
        session: A SQLAlchemy database session object (Obtained using Depends).
        user: An instance of `model.UserCreate` containing the new 
          user's information.

    Returns:
        A `model.Token` object containing the access token and token type
        upon successful registration.
    """
    db_user = model.User.model_validate(user)
    # Hash password before saving it
    db_user.password = crypto.get_password_hash(db_user.password)
    session.add(db_user)
    session.commit()
    session.refresh(db_user)
    return model.Token(
        access_token=auth_handler.create_access_token(db_user),
        token_type="bearer")
