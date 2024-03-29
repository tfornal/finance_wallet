##TODO expiration of token in get_current_user - ustawienie, aby wylogowal po wygasnieciu tokena;

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


class LoginForm:
    def __init__(self, request: Request):
        self.request: Request = request
        self.email: Optional[str] = None
        self.password: Optional[str] = None

    async def create_oauth_form(self):
        form = await self.request.form()
        self.email = form.get("email")
        self.password = form.get("password")


@router.post("/token", response_model=Token)
async def login_for_access_token(
    response: Response, form_data: form_dependency, db: db_dependency
):
    user = authenticate_user(form_data.email, form_data.password, db)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid user email or password.")
    token = create_access_token(
        user.username, user.user_id, timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    response.set_cookie(key="access_token", value=token, httponly=True)
    return True


@router.get("/", response_class=HTMLResponse)
async def authentication_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})


@router.post("/", response_class=HTMLResponse)
async def login(request: Request, db: Session = Depends(get_db)):
    try:
        form = LoginForm(request)
        await form.create_oauth_form()
        response = RedirectResponse(url="/assets", status_code=status.HTTP_302_FOUND)

        validate_user_cookie = await login_for_access_token(
            response=response, form_data=form, db=db
        )
        if not validate_user_cookie:
            msg = "Incorrect username or password"
            return templates.TemplateResponse(
                "login.html", {"request": request, "msg": msg}
            )
        return response
    except HTTPException:
        msg = "Unknown error"
        return templates.TemplateResponse(
            "login.html", {"request": request, "msg": msg}
        )


def hash_password(plain_password):
    return bcrypt_context.hash(plain_password)


def verify_password(plain_password, hashed_password):
    return bcrypt_context.verify(plain_password, hashed_password)


def authenticate_user(email: str, password: str, db):
    user = db.query(models.Users).filter(models.Users.email == email).first()
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user


def create_access_token(username: str, user_id: int, validation_time: timedelta):
    expiration = datetime.utcnow() + validation_time
    payload = {"sub": username, "id": user_id, "exp": expiration}
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def is_token_expired():
    pass


def check_password_strength(password):
    pattern = re.compile(r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[\W_]).+$")
    return bool(pattern.match(password))


async def get_user_by_token(token):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        user_id: int = payload.get("id")
        expiration: int = payload.get("exp", 0)

        current_time = datetime.utcnow().timestamp()

        if current_time > expiration:
            return None

        if username is None or user_id is None:
            return None
        return {"username": username, "id": user_id, "exp": expiration}
    except JWTError:
        return None


async def get_current_user(request: Request):
    try:
        token = request.cookies.get("access_token")
        if token is None:
            return None
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        user_id: int = payload.get("id")
        expiration: int = payload.get("exp", 0)

        current_time = datetime.utcnow().timestamp()
        if current_time > expiration:
            # Token has expired, perform logout
            await logout(request)
            return None

        if username is None or user_id is None:
            await logout(request)
            return None
        return {"username": username, "id": user_id}
    except JWTError:
        await logout(request)
        return None


@router.get("/logout", response_class=JSONResponse)
async def logout(request: Request):
    msg = "Logout successful"
    response = templates.TemplateResponse(
        "login.html", {"request": request, "msg": msg}
    )
    response.delete_cookie(key="access_token")
    return response


@router.get("/logout", response_class=JSONResponse)
async def logout(request: Request):
    msg = "Logout successful"
    response = templates.TemplateResponse(
        "login.html", {"request": request, "msg": msg}
    )
    response.delete_cookie(key="access_token")
    return response


@router.get("/register", response_class=HTMLResponse)
async def register(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})


@router.post("/register", response_class=JSONResponse)
async def register_user(
    request: Request,
    email: str = Form(...),
    username: str = Form(...),
    password: str = Form(...),
    password2: str = Form(...),
    db: Session = Depends(get_db),
):
    validation2 = db.query(models.Users).filter(models.Users.email == email).first()
    validation1 = (
        db.query(models.Users).filter(models.Users.username == username).first()
    )
    #### TODO PRZEKIEROWAC DO HTML a nie httpexception - inaczej wyskakuje
    #### TODO albo response = RedirectResponse(url="/wallet", status_code=status.
    #### HTTP_302_FOUND)?????
    if validation1 is not None or validation2 is not None:
        raise HTTPException(status_code=404, detail="juz istnieje")
    if password != password2:
        raise HTTPException(status_code=404, detail="zle haslo")
    validate_password_strength = check_password_strength(password)
    # TODO - activate once finished!
    # if not validate_password_strength:
    #     msg = "Password do not match the required pattern!"
    #     return templates.TemplateResponse(
    #         "register.html", {"request": request, "msg": msg}
    #     )

    users_model = models.Users()
    users_model.email = email
    users_model.username = username
    users_model.hashed_password = hash_password(password)
    db.add(users_model)
    db.commit()

    msg = "User successfully created!"

    return templates.TemplateResponse("login.html", {"request": request, "msg": msg})


@router.get("/reset_password", response_class=HTMLResponse)
async def authentication_page(request: Request):
    return templates.TemplateResponse("reset_password.html", {"request": request})
