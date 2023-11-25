import sys

sys.path.append("..")
import models
from database import engine, SessionLocal
from fastapi import Depends, HTTPException, APIRouter, Request, Form, status
from fastapi.responses import JSONResponse  # , HTMLResponse
from sqlalchemy import func
from sqlalchemy.orm import Session
from starlette.responses import RedirectResponse
from .authentication import get_current_user

### to bedzie ptorzebne gdy bede przechodzil na html
# from fastapi.templating import Jinja2Templates

router = APIRouter(
    prefix="/wallet", tags=["wallet"], responses={404: {"description": "Not found"}}
)


def get_db():
    try:
        db = SessionLocal()
        yield db
    finally:
        db.close()


models.Base.metadata.create_all(bind=engine)
# templates = Jinja2Templates(directory="templates") #### to bedzie potrzebne jak bede przechodzil na html


@router.get("/", response_class=JSONResponse)
# request - przekazuje fastapi prosbe o uzyskanie dostepu do html
async def get_expenses_of_all_users(request: Request, db: Session = Depends(get_db)):
    expenses = db.query(models.Wallet).all()
    expenses_data = [
        {
            "id": expense.id,
            "price": expense.price,
            "description": expense.description,
            "owner_id": expense.owner_id,
        }
        for expense in expenses
    ]
    return expenses_data


@router.get("/{user_id}", response_class=JSONResponse)
async def get_expenses_by_user(
    request: Request, user_id: int, db: Session = Depends(get_db)
):
    expenses = db.query(models.Wallet).filter(models.Wallet.owner_id == user_id).all()
    expenses_data = [
        {
            "id": expense.id,
            "description": expense.description,
            "price": expense.price,
            "owner_id": expense.owner_id,
        }
        for expense in expenses
    ]
    return expenses_data


@router.get("/sum/{user_id}", response_class=JSONResponse)
async def get_purchase_sum(
    request: Request, user_id: int, db: Session = Depends(get_db)
):
    expenses_models = (
        db.query(
            models.Wallet.owner_id, func.sum(models.Wallet.price).label("total_price")
        )
        .filter(models.Wallet.owner_id == user_id)
        .group_by(models.Wallet.owner_id)
        .all()
    )
    expenses_data = [
        {"owner_id": expense.owner_id, "total_cost": expense.total_price}
        for expense in expenses_models
    ]
    return expenses_data


@router.post("/add-expense", response_class=JSONResponse)
async def create_expense(
    request: Request,
    description: str = Form(...),
    price: float = Form(...),
    owner_id: int = Form(...),
    db: Session = Depends(get_db),
):
    wallet_model = models.Wallet()

    wallet_model.description = description
    wallet_model.price = price
    wallet_model.owner_id = owner_id
    db.add(wallet_model)
    db.commit()
    return RedirectResponse(url="/wallet", status_code=status.HTTP_302_FOUND)


@router.put("/edit-expense/{expense_id}", response_class=JSONResponse)
async def edit_expense(
    request: Request,
    expense_id: int,
    description: str = Form(...),
    price: float = Form(...),
    owner_id: int = Form(...),
    db: Session = Depends(get_db),
):
    wallet_model = (
        db.query(models.Wallet).filter(models.Wallet.id == expense_id).first()
    )
    # wallet_model = models.Wallet()
    wallet_model.description = description
    wallet_model.price = price
    wallet_model.owner_id = (
    )
    db.add(wallet_model)
    db.commit()
    return RedirectResponse(url="/wallet", status_code=status.HTTP_302_FOUND)


@router.get("/delete/{expense_id}", response_class=JSONResponse)
async def delete_expense(
    request: Request, expense_id: int, db: Session = Depends(get_db)
):
    expenses = db.query(models.Wallet).filter(models.Wallet.id == expense_id).first()
    if expenses is None:
        return RedirectResponse(url="/wallet", status_code=status.HTTP_302_FOUND)
    db.query(models.Wallet).filter(models.Wallet.id == expense_id).delete()
    db.commit()
    return RedirectResponse(url="/wallet", status_code=status.HTTP_302_FOUND)
