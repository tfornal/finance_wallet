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
    MAIL_PASSWORD="chlt avrw cgie frnt",  ### private key google
    MAIL_FROM="tfornal90@gmail.com",
    MAIL_PORT=587,
    MAIL_SERVER="smtp.gmail.com",
    MAIL_FROM_NAME="Finance wallet",
    MAIL_STARTTLS=True,
    MAIL_SSL_TLS=False,
    USE_CREDENTIALS=True,
    VALIDATE_CERTS=True,
)


async def reset_password(subject: str, email_to: str, body: dict):
    message = """<p>FASTAPI TEST MAIL</p> """
    message = MessageSchema(
        subject=subject,
        recipients=[email_to],
        template_body=body,
        subtype="html",
    )
    fm = FastMail(conf)
    await fm.send_message(message=message, template_name="reset_password.html")
