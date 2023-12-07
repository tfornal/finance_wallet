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
from .authorization import get_current_user, hash_password, oauth2_bearer

from datetime import datetime, timedelta
from typing import Annotated

from jose import JWTError, jwt
from passlib.context import CryptContext


router = APIRouter(
    prefix="/admin",
    tags=["admin"],
    responses={404: {"description": "Not found"}},
)

models.Base.metadata.create_all(bind=engine)
password_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
user_dependency = Annotated[dict, Depends(get_current_user)]


def encrypt_password(plain_password):
    return password_context.hash(plain_password)


def validate_password(plain_password, hashed_password):
    return password_context.verify(plain_password, hashed_password)


def get_db():
    try:
        db = SessionLocal()
        yield db
    finally:
        db.close()


@router.get("/", response_class=JSONResponse)
async def get_all_users(request: Request, db: Session = Depends(get_db)):
    users_model = db.query(models.Users).all()
    all_users = [{"username": user.username} for user in users_model]
    return all_users
