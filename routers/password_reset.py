from fastapi import APIRouter, Depends, Request, HTTPException, status
from .schemas import PasswordReset, NewPassword
from .auth import create_access_token, hash_password
from typing import Annotated
from sqlalchemy.orm import Session
from database import engine, SessionLocal
from .send_email import reset_password
import models
from datetime import timedelta, datetime
from .auth import oauth2_bearer, get_current_user, get_user_by_token
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

router = APIRouter(prefix="/password", tags=["Password reset"])

templates = Jinja2Templates(directory="templates")


def get_db():
    try:
        db = SessionLocal()
        yield db
    finally:
        db.close()


# @router.get("", response_class=HTMLResponse)
# async def reset_request(request: Request):
#     user = await get_current_user(request)
#     if user is None:
#         return RedirectResponse(url="/auth", status_code=status.HTTP_302_FOUND)
#     return templates.TemplateResponse("password_reset.html", {"request": request})


@router.post("", response_class=HTMLResponse)
async def reset_request(user_email: PasswordReset, db: Session = Depends(get_db)):
    user = db.query(models.Users).filter(models.Users.email == user_email.email).first()
    if user is not None:
        token = create_access_token(user.username, user.user_id, timedelta(minutes=10))
        reset_link = f"http://localhost:8000/reset?token={token}"
        await reset_password(
            "Password Reset",
            user_email.email,
            reset_link,
        )

    else:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Email address not found."
        )


@router.put("/reset/", response_description="Reset password")
async def reset(token: str, new_password: NewPassword, db: Session = Depends(get_db)):
    request_data = {k: v for k, v in new_password.dict().items() if v is not None}
    user = await get_user_by_token(token)
    # get the hashed version of the password
    current_time = datetime.utcnow().timestamp()
    if current_time <= user["exp"]:  ### inny warunek;
        # use token to get the current user

        # update the password of the current user
        new_hashed_password = hash_password(request_data["password"])
        db.query(models.Users).filter(models.Users.username == user["username"]).update(
            {
                "hashed_password": new_hashed_password,
            }
        )
        db.commit()
        breakpoint()
    #     if update_result.modified_count == 1:
    #         # get the newly updated current user and return as a response
    #         updated_student = await db["users"].find_one({"_id": user["_id"]})
    #         if (updated_student) is not None:
    #             return updated_student

    # existing_user = await db["users"].find_one({"_id": user["_id"]})
    # if (existing_user) is not None:
    #     return existing_user

    # Raise error if the user can not be found in the database
    # raise HTTPException(status_code=404, detail=f"User not found")
