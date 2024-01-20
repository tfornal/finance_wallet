from datetime import timedelta, datetime
from fastapi import APIRouter, Depends, Form, HTTPException, Request, Response
from pydantic import BaseModel
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from starlette import status
from database import SessionLocal
import models
from typing import Annotated, Optional
from starlette.responses import RedirectResponse
import re
from passlib.context import CryptContext
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import jwt, JWTError
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field, EmailStr

router = APIRouter(prefix="/auth", tags=["auth"])

SECRET_KEY = "ac9cfe2bb4a5036d00c472681c0ec91041a0a6eb88f817cb59d5e2a3071ff5cd"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 100

bcrypt_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_bearer = OAuth2PasswordBearer(tokenUrl="auth/token")

templates = Jinja2Templates(directory="templates")


def get_db():
    try:
        db = SessionLocal()
        yield db
    finally:
        db.close()


db_dependency = Annotated[Session, Depends(get_db)]
form_dependency = Annotated[OAuth2PasswordRequestForm, Depends()]
token_dependency = Annotated[str, Depends(oauth2_bearer)]


class CreateUserRequest(BaseModel):
    email: str
    username: str
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str


class PasswordReset(BaseModel):
    email: EmailStr


class NewPassword(BaseModel):
    password: str
