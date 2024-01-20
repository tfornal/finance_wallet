from fastapi import FastAPI
import models
from routers import wallet, user, auth, assets, investments, password_reset, send_email
from starlette.staticfiles import StaticFiles
from starlette import status
from starlette.responses import RedirectResponse

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/")
async def root():
    return RedirectResponse(url="/assets", status_code=status.HTTP_302_FOUND)


app.include_router(user.router)
app.include_router(wallet.router)
app.include_router(investments.router)
app.include_router(assets.router)
app.include_router(auth.router)
app.include_router(password_reset.router)
app.include_router(send_email.router)
