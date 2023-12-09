import sys

sys.path.append("..")
import models
from database import engine, SessionLocal
from fastapi import Depends, HTTPException, APIRouter, Request, Form, status
from fastapi.responses import HTMLResponse
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from sqlalchemy import func
from sqlalchemy.orm import Session
from starlette.responses import RedirectResponse
from pydantic import BaseModel
from .authorization import get_current_user, hash_password, oauth2_bearer

from datetime import datetime, timedelta
from typing import Annotated

from jose import JWTError, jwt
from passlib.context import CryptContext  # allows to hash password
from fastapi.templating import Jinja2Templates

templates = Jinja2Templates(directory="templates")


SECRET_KEY = "dacee2503eaabfe54722dd00158df4f2bcf52a2f78bfdf74e73ca8194754c6cd"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 10

router = APIRouter(
    prefix="/user",
    tags=["user"],
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


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_user(
    email: str = Form(...),
    username: str = Form(...),
    password: str = Form(...),
    password_repeated: str = Form(...),
    db: Session = Depends(get_db),
):
    validation_email = (
        db.query(models.Users).filter(models.Users.email == email).first()
    )

    validation_username = (
        db.query(models.Users).filter(models.Users.username == username).first()
    )
    if validation_email is not None or validation_username is not None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Account already exists."
        )
    if not password == password_repeated:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Password incorrect."
        )

    user_model = models.Users()
    user_model.email = email
    user_model.username = username
    user_model.hashed_password = hash_password(password)

    db.add(user_model)
    db.commit()


@router.get("/change_password", response_class=HTMLResponse)
async def change_password(request: Request, db: SessionLocal = Depends(get_db)):
    user = await get_current_user(request)
    if user is None:
        return RedirectResponse(url="/authorization", status_code=status.HTTP_302_FOUND)
    user_model = (
        db.query(models.Users).filter(models.Users.user_id == user.get("id")).first()
    )
    return templates.TemplateResponse(
        "change_password.html", {"request": request, "email": user_model.email}
    )


@router.post("/change_password", response_class=HTMLResponse)
async def change_password_commit(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    new_password: str = Form(...),
    repeat_new_password: str = Form(...),
    db: Session = Depends(get_db),
):
    user = await get_current_user(request)
    if user is None:
        return RedirectResponse(url="/", status_code=status.HTTP_302_FOUND)

    user_model = (
        db.query(models.Users).filter(models.Users.user_id == user.get("id")).first()
    )

    if not validate_password(password, user_model.hashed_password):
        msg = "Current password is incorrect!"
        return templates.TemplateResponse(
            "change_password.html",
            {"request": request, "email": user_model.email, "msg": msg},
        )

    ### TODO checking password but already encrypted
    if new_password != repeat_new_password:
        msg = "New passwords do not match!"
        return templates.TemplateResponse(
            "change_password.html",
            {"request": request, "email": user_model.email, "msg": msg},
        )

    encrypted_password = encrypt_password(new_password)
    db.query(models.Users).filter(models.Users.user_id == user.get("id")).update(
        {
            "hashed_password": encrypted_password,
        }
    )
    db.commit()

    msg = "Password changed successfully!"
    return templates.TemplateResponse(
        "change_password.html",
        {"request": request, "email": user_model.email, "msg": msg},
    )


@router.get("/delete/{user_id}", response_class=HTMLResponse)
async def delete_user(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db),
):
    user = await get_current_user(request)
    if user is None:
        return RedirectResponse(url="/authorization", status_code=status.HTTP_302_FOUND)

    user_to_delete = (
        db.query(models.Users).filter(models.Users.username == username).first()
    )
    if user_to_delete is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, details="User not found."
        )

    db.query(models.Users).filter(models.Users.username == username).delete()
    db.commit()
