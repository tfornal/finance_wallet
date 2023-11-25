from fastapi import FastAPI
import models
from database import engine
from routers import wallet, users
from starlette.staticfiles import StaticFiles


app = FastAPI()
models.Base

app.mount("/static", StaticFiles(directory="static"), name="static")

app.include_router(wallet.router)
app.include_router(users.router)
