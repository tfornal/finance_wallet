import os
from dotenv import load_dotenv
from fastapi import FastAPI
from starlette.responses import JSONResponse
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig, MessageType
from pydantic import EmailStr, BaseModel
from typing import List
from fastapi import Depends, HTTPException, APIRouter, Request, Form, status, Query

router = APIRouter(prefix="/email", tags=["Password reset"])


class EmailSchema(BaseModel):
    email: List[EmailStr]


conf = ConnectionConfig(
    MAIL_USERNAME="tomasz.fornal6@gmail.com",
    MAIL_PASSWORD="chlt avrw cgie frnt",
    MAIL_FROM="tofo@gmail.com",
    MAIL_PORT=587,
    MAIL_SERVER="smtp.gmail.com",
    MAIL_FROM_NAME="Finance wallet",
    MAIL_STARTTLS=True,
    MAIL_SSL_TLS=False,
    USE_CREDENTIALS=True,
    VALIDATE_CERTS=True,
)


async def reset_password(subject: str, email_to: str, body: dict) -> JSONResponse:
    html = """<p>Hi this test mail, thanks for using Fastapi-mail</p> """
    message = MessageSchema(
        subject=subject,
        recipients=["tfornal90@gmail.com"],
        body=html,
        subtype="html",
    )
    fm = FastMail(conf)
    await fm.send_message(message, template_name="password_reset.html")

