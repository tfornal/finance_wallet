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

## authentication
from passlib.context import CryptContext
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import jwt, JWTError

# do html to jest potrzebne
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

router = APIRouter(prefix="/authorization", tags=["authorization"])

SECRET_KEY = "ac9cfe2bb4a5036d00c472681c0ec91041a0a6eb88f817cb59d5e2a3071ff5cd"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 10

bcrypt_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_bearer = OAuth2PasswordBearer(tokenUrl="authorization/token")

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


class LoginForm:
    def __init__(self, request: Request):
        self.request: Request = request
        self.username: Optional[str] = None
        self.password: Optional[str] = None

    async def create_oauth_form(self):
        form = await self.request.form()
        self.username = form.get("email")
        self.password = form.get("password")


@router.get("/login", response_class=HTMLResponse)
async def authentication_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})


def hash_password(plain_password):
    return bcrypt_context.hash(plain_password)


def verify_password(plain_password, hashed_password):
    return bcrypt_context.verify(plain_password, hashed_password)


def authenticate_user(username: str, password: str, db):
    user = db.query(models.Users).filter(models.Users.username == username).first()
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user


def create_access_token(username: str, user_id: int, validation_time: timedelta):
    expiration = datetime.utcnow() + validation_time
    payload = {"sub": username, "id": user_id, "exp": expiration}
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


@router.post("/token", response_model=Token)
async def login_for_access_token(
    response: Response, form_data: form_dependency, db: db_dependency
):
    user = authenticate_user(form_data.username, form_data.password, db)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="User validation failed."
        )
    token = create_access_token(
        user.username, user.user_id, timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    response.set_cookie(key="access_token", value=token, httponly=True)
    # return True
    return {"access_token": token, "token_type": "bearer"}


async def get_current_user(
    # token: token_dependency,  ########### jesli usune token_dependency - strace klodke
    # jesli wiec to usuniemy, to stworzy sie ciasteczko i tak, wiec pewnie trzeba to wywalic i stworzyc osobna
    # funkcje logowania
    request: Request,
    token: token_dependency,
):
    try:
        token = request.cookies.get("access_token")
        if token is None:
            return None
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
        raise HTTPException(status_code=404, detail="Not found")


@router.post("/login", response_class=JSONResponse)
async def login(response: Response, request: Request, db: db_dependency):
    # try:
    form = LoginForm(request)
    await form.create_oauth_form()
    response = RedirectResponse(url="/wallet", status_code=status.HTTP_302_FOUND)
    validate_user_cookie = await login_for_access_token(Response, form, db)

    if not validate_user_cookie:
        msg = "Incorrect Username of Password"
        return templates.TemplateResponse(
            "login.html", {"request": request, "msg": msg}
        )
    return response
    # except HTTPException:
    #     print("dDDDDDDD")
