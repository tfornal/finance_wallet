import sys

sys.path.append("..")
import models
from database import engine, SessionLocal
from fastapi import Depends, HTTPException, APIRouter, Request, Form, status
from fastapi.responses import JSONResponse, HTMLResponse
from sqlalchemy import func, Date
from sqlalchemy.orm import Session

from starlette.responses import RedirectResponse
from starlette import status

from datetime import datetime, date
from typing import Optional

# from pydantic import BaseModel, Field
from .authorization import get_current_user, oauth2_bearer
from typing import Annotated

### to bedzie ptorzebne gdy bede przechodzil na html
from fastapi.templating import Jinja2Templates

router = APIRouter(
    prefix="/wallet", tags=["wallet"], responses={404: {"description": "Not found"}}
)


def get_db():
    try:
        db = SessionLocal()
        yield db
    finally:
        db.close()


user_dependency = Annotated[dict, Depends(get_current_user)]
token_dependency = Annotated[str, Depends(oauth2_bearer)]
models.Base.metadata.create_all(bind=engine)

templates = Jinja2Templates(
    directory="templates"
)  #### to bedzie potrzebne jak bede przechodzil na html


@router.get("/", response_class=HTMLResponse)
async def get_all_by_user(
    request: Request,
    db: Session = Depends(get_db),
):
    expenses = db.query(models.Wallet).filter(models.Wallet.owner_id == 13).all()
    return templates.TemplateResponse(
        "home.html", {"request": request, "expenses": expenses}
    )


@router.get("/add_expense", response_class=HTMLResponse)
async def create_expense(request: Request):
    return templates.TemplateResponse("add_expense.html", {"request": request})


@router.post("/add_expense", response_class=HTMLResponse)
async def create_expense_commit(
    request: Request,
    title: str = Form(...),
    price: str = Form(...),
    category: str = Form(...),
    # date: str = Form(...), #### TODO poprawic wpisywanie dat
    db: Session = Depends(get_db),
):
    # breakpoint()
    expense_model = models.Wallet()

    expense_model.title = title
    expense_model.price = price
    expense_model.category = category
    # expense_model.date = date
    expense_model.owner_id = 13
    # breakpoint()
    db.add(expense_model)
    db.commit()

    return RedirectResponse(url="/wallet", status_code=status.HTTP_302_FOUND)


@router.get("/edit_expense/{expense_id}", response_class=HTMLResponse)
async def edit_expense(
    request: Request, expense_id: int, db: SessionLocal = Depends(get_db)
):
    expense = db.query(models.Wallet).filter(models.Wallet.id == expense_id).first()
    if not expense:
        raise HTTPException(status_code=404, detail="Expense not found")

    return templates.TemplateResponse(
        "edit_expense.html", {"request": request, "expense": expense}
    )


@router.post("/edit_expense/{expense_id}", response_class=HTMLResponse)
async def edit_expense_commit(
    request: Request,
    expense_id: int,
    title: str = Form(...),
    price: str = Form(...),
    category: str = Form(...),
    # date: str = Form(...),  #### TODO poprawic wpisywanie dat
    db: Session = Depends(get_db),
):
    # breakpoint()
    expense = db.query(models.Wallet).filter(models.Wallet.id == expense_id).first()
    if not expense:
        raise HTTPException(status_code=404, detail="Expense not found")
    db.query(models.Wallet).filter(models.Wallet.id == expense_id).update(
        {
            "title": title,
            "price": price,
            "category": category,
            # "date": date,
            # Dodaj inne kolumny, które chcesz zaktualizować
        }
    )
    db.commit()

    return RedirectResponse(url="/wallet", status_code=status.HTTP_302_FOUND)


@router.get("/delete/{expense_id}")
async def delete_expense(
    request: Request,
    expense_id: int,
    db: SessionLocal = Depends(get_db),
):
    expense_model = (
        db.query(models.Wallet)
        .filter(models.Wallet.id == expense_id)
        .filter(models.Wallet.owner_id == 13)
        .first()
    )
    if expense_model is None:
        return RedirectResponse(url="/wallet", status_code=status.HTTP_302_FOUND)

    db.query(models.Wallet).filter(models.Wallet.id == expense_id).delete()
    db.commit()

    return RedirectResponse(url="/wallet", status_code=status.HTTP_302_FOUND)


###############################################################

# @router.get("/all_users", response_class=HTMLResponse)
# # request - przekazuje fastapi prosbe o uzyskanie dostepu do html
# async def get_expenses_of_all_users(request: Request, db: Session = Depends(get_db)):
#     expenses = db.query(models.Wallet).all()
#     expenses_data = [
#         {
#             "id": expense.id,
#             "price": expense.price,
#             "description": expense.description,
#             "owner_id": expense.owner_id,
#         }
#         for expense in expenses
#     ]
#     return templates.TemplateResponse(
#         "layout.html", {"request": request, "expenses": expenses_data}
#     )


# @router.get("/expenses", response_class=HTMLResponse)
# async def get_expenses_by_user(
#     request: Request,
#     user: user_dependency,
#     token: token_dependency,
#     db: Session = Depends(get_db),
# ):
#     user = await get_current_user(request, token)
#     if user is None:
#         raise HTTPException(
#             status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication failed!"
#         )
#     all_expenses = (
#         db.query(models.Wallet).filter(models.Wallet.owner_id == user.get("id")).all()
#     )

#     expenses_data = [
#         {
#             "id": expense.id,
#             "price": expense.price,
#             "description": expense.description,
#             "category": expense.category,
#             "owner_id": expense.owner_id,
#         }
#         for expense in all_expenses
#     ]
#     if len(expenses_data) != 0:  # is not None:
#         return expenses_data
#     raise HTTPException(status_code=404, detail="Expenses not found.")


# @router.get("/sum", response_class=HTMLResponse)
# async def get_purchase_sum(
#     request: Request,
#     user: user_dependency,
#     token: token_dependency,
#     db: Session = Depends(get_db),
# ):
#     user = await get_current_user(request, token)
#     if user is None:
#         raise HTTPException(
#             status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication failed!"
#         )
#     expenses_models = (
#         db.query(
#             models.Wallet.owner_id, func.sum(models.Wallet.price).label("total_price")
#         )
#         .filter(models.Wallet.owner_id == user.get("id"))
#         .group_by(models.Wallet.owner_id)
#         .all()
#     )
#     expenses_data = [
#         {"owner_id": expense.owner_id, "total_cost": expense.total_price}
#         for expense in expenses_models
#     ]
#     return expenses_data


# @router.get("/max/{username}", response_class=HTMLResponse)
# async def get_most_expensive(
#     request: Request, username: str, db: Session = Depends(get_db)
# ):
#     max_price = (
#         db.query(func.max(models.Wallet.price))
#         .join(models.Users)
#         .filter(models.Users.username == username)
#         .scalar()
#     )

#     return {"username": username, "max_price": max_price}


# @router.post("/add-expense", response_class=HTMLResponse)
# async def create_expense(
#     request: Request,
#     date: datetime = Form(None),
#     price: float = Form(...),
#     description: str = Form(...),
#     category: str = Form(...),
#     owner_id: int = Form(...),
#     db: Session = Depends(get_db),
# ):
#     wallet_model = models.Wallet()

#     wallet_model.price = price
#     wallet_model.description = description
#     wallet_model.category = category
#     wallet_model.owner_id = owner_id

#     if date:
#         wallet_model.date = date.date()  # Pobierz tylko datę
#     else:
#         wallet_model.date = None

#     db.add(wallet_model)
#     db.commit()


# @router.put("/edit-expense/{expense_id}", response_class=HTMLResponse)
# async def edit_expense(
#     request: Request,
#     expense_id: int,
#     date: datetime = Form(None),
#     price: float = Form(...),
#     description: str = Form(...),
#     category: str = Form(...),
#     owner_id: int = Form(...),
#     db: Session = Depends(get_db),
# ):
#     wallet_model = (
#         db.query(models.Wallet).filter(models.Wallet.id == expense_id).first()
#     )
#     wallet_model.date = date
#     wallet_model.price = price
#     wallet_model.description = description
#     wallet_model.category = category
#     wallet_model.owner_id = ()
#     db.add(wallet_model)
#     db.commit()


# @router.get("/delete/{expense_id}", response_class=HTMLResponse)
# async def delete_expense(
#     request: Request, expense_id: int, db: Session = Depends(get_db)
# ):
#     expenses = db.query(models.Wallet).filter(models.Wallet.id == expense_id).first()
#     if expenses is None:
#         return RedirectResponse(url="/wallet", status_code=status.HTTP_302_FOUND)
#     db.query(models.Wallet).filter(models.Wallet.id == expense_id).delete()
#     db.commit()
