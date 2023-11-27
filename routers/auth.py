from datetime import timedelta, datetime
from typing import Annotated
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from starlette import status
from database import SessionLocal
from models import Users

# ponizej do autentykacji
from passlib.context import CryptContext
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from jose import jwt, JWTError


router = APIRouter(prefix="/auth", tags=["auth"])

SECRET_KEY = "dacee2503eaabfe54722dd00158df4f2bcf52a2f78bfdf74e73ca8194754c6cd"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 10

## crypt context when we pass in our schemes, we will use to hash and unhas password
bcrypt_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
# auth/token" because token is going to be an api endpoint that we create in
# while auth is this file specifically [so this needs to much the prefix from router] (to moj dopisek)
oauth2_bearer = OAuth2PasswordBearer(tokenUrl="auth/token")


# we than need to create our user request of base model
## pydantic validation
class CreateUserRequest(BaseModel):
    email: str
    username: str
    password: str


# potem musimyu zrobic class of token
# we want to make sure that we use this tokebn because swagger and Fastapi make some magic behind the scenes;
# we need this token validation because on swagger we will be able log in and  type password and username to be able
# to authencitace user and to be able to do this we have a token class
# so right now we have user request and token class
class Token(BaseModel):
    access_token: str
    token_type: str


# tu juz wiem o co chodzi


def get_db():
    try:
        db = SessionLocal()
        yield db
    finally:
        db.close()


## teraz stworzyc database dependency
db_dependency = Annotated[Session, Depends(get_db)]


# at router.post we want to return a status code of status dot http
# which is the created status code for application we then wat to have function name to which we pass in one whichj is db dependency
# and then the create user request of our createuserrequest base pydantic model;
# we than we want to sau create_user_model  = Users  bases on the create_uiser_request passed
# ##
@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_user(db: db_dependency, create_user_request: CreateUserRequest):
    create_user_model = Users(
        email=create_user_request.email,
        username=create_user_request.username,
        hashed_password=bcrypt_context.hash(create_user_request.password),
    )
    db.add(create_user_model)
    db.commit()


#### tutaj zaczyna sie autentykacja
# slash token we create response_model of a token based ona  class token and base model of pydantic;
# do funkcji przekazujhemy form data - this creates the form that we need to be able to successfuly pass
#  any username and password; we than wanna pass our database with db injection;
# and we wanna sau user = authenticate_user where we pass our form_data. username and our form data.password and our database
# now one isse we are goint to know immediately is our authenticate user method does not exist so thats we wanna create right now # ##
@router.post("/token", response_model=Token)
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()], db: db_dependency
):
    user = authenticate_user(form_data.username, form_data.password, db)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Could not validate user."
        )
    token = create_access_token(
        user.username, user.user_id, timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )

    return {"access_token": token, "token_type": "bearer"}


#
# now we create jwt that we are goint to be using from the server and our cliens so
# we create create_accesS_token and pass all necessary arguments;
# we say encode the sub as the username and the id wwas the user id.
# SO the jwt once ytou decode it once we sau heu its a suser lets decode the jwt inside the jwt is going to be the username for that user
# and the if for that user we want to say expsires in 20 minutes and we are going to say hey in our encode which is or jwt we want to add
# an expiration  date whhich somethin called EXP whic is goint to be our expireation so we know when we want to return  JWT that is encoded
# where we can pass in the encode the secret key and the algorithm.
# The way we validate the JWT is thre really thins
# 1. encode that is goiing to be the data inside, 2. secret key and 3. algorithm. ##
def create_access_token(username: str, user_id: int, expires_delta: timedelta):
    encode = {"sub": username, "id": user_id}
    expires = datetime.utcnow() + expires_delta
    encode.update({"exp": expires})
    return jwt.encode(encode, SECRET_KEY, algorithm=ALGORITHM)


### method to decode jwt so we canuse it in the future
# we pass in a token of annotated string depends oauth t2bearer so our current user is going to take in our JWT once
# it validates that he this is correct
#
# najpierw zbieramy payload odkodowujac jwt
# potem sprobujemy uzyskac username i user_id
# jesli to sie nie uda to uzyskamy http exception
#  i uzyskamy jwterror)
## jesli sie uda to  uzyskamy username i id - jesli ktores z nich bedzie brakowalo - uzyskamu http exception
# jesli wszystko bedziue ok to otrzymamy return username i id


# ta fyunkcje nastepnie zastosowac w pozostalych funkcjach aplikacji aby za kazdym razem monitorowac
# czy mam token uprawniajacy mnie do przegladania danej sesji ;
# czyli przy np wywolywaniu user trzeba zastosowac user:user_dependency
# a user_dependency = Annotated[dict, Depents(get_current_user)]


###############!!!!!!!!!!!!!!! na jutro - zastosowac ta funkcje w moich pozostalych dzieki czemu bede mial ta klodke od oauth2
####### tuz po prawej stornie danej funkcji w swaggerze;
async def get_current_user(token: Annotated[str, Depends(oauth2_bearer)]):
    try:
        ### ponizej sa 3 czesci z ktorych sklada sie nassz jwt
        # eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ0b2ZvIiwiaWQiOjEzLCJleHAiOjE3MDEwMzY5MTh9.8_s7Xej9DLk4lZqqql2IqprzN30xdBWyZjzRnGXvlyo
        payload = jwt.decode(token, SECRET_KEY, algorithm=[ALGORITHM])
        username: str = payload.get(
            "sub"
        )  ## tak jest po odkodowaniu jwt jesli chodzi o usera
        user_id: int = payload.get("id")
        if username is None or user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate user.",
            )
        return {"username": username, "id": user_id}
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Could not validate user."
        )


### to jest raczej zrozumiale;
def authenticate_user(username: str, password: str, db):
    user = db.query(Users).filter(Users.username == username).first()
    if not user:
        return False
    if not bcrypt_context.verify(password, user.hashed_password):
        return False
    return user
