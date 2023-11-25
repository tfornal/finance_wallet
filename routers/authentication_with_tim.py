import sys

sys.path.append("..")
import models
from database import engine, SessionLocal
from fastapi import Depends, HTTPException, APIRouter, Request, Form, status
from fastapi.responses import JSONResponse  # , HTMLResponse
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from sqlalchemy import func
from sqlalchemy.orm import Session
from starlette.responses import RedirectResponse
from pydantic import BaseModel

# do autentykacji ponizej
from datetime import datetime, timedelta
from jose import JWTError, jwt

# from jose import JWTError, jwt
from passlib.context import CryptContext  # allows to hash password

SECRET_KEY = "dacee2503eaabfe54722dd00158df4f2bcf52a2f78bfdf74e73ca8194754c6cd"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 10


### to bedzie ptorzebne gdy bede przechodzil na html
# from fastapi.templating import Jinja2Templates

router = APIRouter(
    prefix="/authentication",
    tags=["authentication"],
    responses={404: {"description": "Not found"}},
)


def get_db():
    try:
        db = SessionLocal()
        yield db
    finally:
        db.close()


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: str or None = None


class User(BaseModel):
    username: str
    email: str
    full_name: str or None = None
    active: bool or None = None


class UserInDB(User):
    hashed_password: str


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth_2_scheme = OAuth2PasswordBearer(tokenUrl="token")


models.Base.metadata.create_all(bind=engine)


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password):
    return pwd_context.hash(password)


def get_user(db, username: str):
    if username in db:
        user_data = db[username]
        return UserInDB(**user_data)


def authenticate_user(db, username: str, password: str):
    user = get_user(db, username)
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user


def create_access_token(data: dict, expires_delta: timedelta or None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encode_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encode_jwt


async def get_current_user():
    pass
