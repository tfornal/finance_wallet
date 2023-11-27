from datetime import timedelta, datetime
from fastapi import APIRouter, Depends, Form, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from starlette import status
from database import SessionLocal
from models import Users
from typing import Annotated

## authentication
from passlib.context import CryptContext
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import jwt, JWTError


SECRET_KEY = "ac9cfe2bb4a5036d00c472681c0ec91041a0a6eb88f817cb59d5e2a3071ff5cd"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 10

bcrypt_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_bearer = OAuth2PasswordBearer(tokenUrl="authorization/token")

router = APIRouter(prefix="/authorization", tags=["authorization"])


def get_db():
    try:
        db = SessionLocal()
        yield db
    finally:
        db.close()


class CreateUserRequest(BaseModel):
    email: str
    username: str
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str


def hash_password(plain_password):
    return bcrypt_context.hash(plain_password)


db_dependency = Annotated[Session, Depends(get_db)]
form_dependency = Annotated[OAuth2PasswordRequestForm, Depends()]
token_dependency = Annotated[str, Depends(oauth2_bearer)]


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_user(
    email: str = Form(...),
    username: str = Form(...),
    password: str = Form(...),
    password_repeated: str = Form(...),
    db: Session = Depends(get_db),
):
    validation_email = db.query(Users).filter(Users.email == email).first()
    validation_username = db.query(Users).filter(Users.username == username).first()
    if validation_email is not None or validation_username is not None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Account already exists."
        )
    if not password == password_repeated:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Password incorrect."
        )

    user_model = Users()
    user_model.email = email
    user_model.username = username
    user_model.hashed_password = hash_password(password)

    db.add(user_model)
    db.commit()


def authenticate_user(username: str, password: str, db):
    user = db.query(Users).filter(Users.username == username).first()
    if not user:
        return False
    if not bcrypt_context.verify(password, user.hashed_password):
        return False
    return user


def create_access_token(username: str, user_id: int, validation_time: timedelta):
    expiration = datetime.utcnow() + validation_time
    payload = {"sub": username, "id": user_id, "exp": expiration}
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


@router.post("/token", response_model=Token)
async def login_for_access_token(form_data: form_dependency, db: db_dependency):
    user = authenticate_user(form_data.username, form_data.password, db)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, details="User validation failed."
        )
    token = create_access_token(
        user.username, user.user_id, timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    return {"access_token": token, "token_type": "bearer"}


async def get_current_user(token: token_dependency):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        user_id: int = payload.get("id")
        if username is None or user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                details="User validation failed.",
            )
        return {"username": username, "id": user_id}

    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, details="User validation failed."
        )
