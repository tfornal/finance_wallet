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
from .authorization import get_current_user

# do autentykacji ponizej
from datetime import datetime, timedelta
from typing import Annotated

## do autentykacji
from jose import JWTError, jwt
from passlib.context import CryptContext  # allows to hash password


SECRET_KEY = "dacee2503eaabfe54722dd00158df4f2bcf52a2f78bfdf74e73ca8194754c6cd"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 10


### to bedzie ptorzebne gdy bede przechodzil na html
# from fastapi.templating import Jinja2Templates


router = APIRouter(
    prefix="/users",
    tags=["users"],
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


@router.post("/create", response_class=JSONResponse)
async def register_user(
    request: Request,
    username: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    password2: str = Form(...),
    db: Session = Depends(get_db),
):
    validation2 = db.query(models.Users).filter(models.Users.email == email).first()
    validation1 = (
        db.query(models.Users).filter(models.Users.username == username).first()
    )

    if validation1 is not None or validation2 is not None:
        raise HTTPException(status_code=404, detail="juz istnieje")
    if password != password2:
        raise HTTPException(status_code=404, detail="zle haslo")

    users_model = models.Users()
    users_model.email = email
    users_model.username = username
    users_model.hashed_password = encrypt_password(password)
    db.add(users_model)
    db.commit()
    return users_model


@router.get("/delete/{username_param}", response_class=JSONResponse)
async def delete_user(
    request: Request, username_param: str, db: Session = Depends(get_db)
):
    user_to_delete = (
        db.query(models.Users).filter(models.Users.username == username_param).first()
    )
    if user_to_delete is not None:
        db.query(models.Users).filter(models.Users.username == username_param).delete()
        db.commit()
        return "usunieto"
    return "NIE MA TAKIEGO UZYTKOWNIKA"


async def get_current_user():
    pass
