from fastapi import FastAPI
import models
from routers import wallet, users, authorization
from starlette.staticfiles import StaticFiles


app = FastAPI()
models.Base

app.mount("/static", StaticFiles(directory="static"), name="static")

app.include_router(wallet.router)
app.include_router(users.router)
app.include_router(authorization.router)
