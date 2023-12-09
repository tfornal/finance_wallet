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
from .authorization import oauth2_bearer, get_current_user
from typing import Annotated

### to bedzie ptorzebne gdy bede przechodzil na html
from fastapi.templating import Jinja2Templates


import pandas as pd
import plotly.express as px


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

templates = Jinja2Templates(directory="templates")


@router.get("/")
async def get_cummulated_cost_by_category(
    request: Request,
    db: Session = Depends(get_db),
):
    user = await get_current_user(request)
    if user is None:
        return RedirectResponse(url="/authorization", status_code=302)

    expenses = (
        db.query(models.Wallet)
        .filter(models.Wallet.owner_id == user.get("id"))
        .order_by(models.Wallet.price)
        .all()
    )
    df = pd.DataFrame(
        [
            {"Date": expense.date, "Price": expense.price, "Category": expense.category}
            for expense in expenses
        ]
    )
    df.sort_values(by="Date", inplace=True)
    df["Cumulative_Price"] = df.groupby("Category")["Price"].cumsum()
    df["Date"] = pd.to_datetime(df["Date"])
    fig = px.scatter(
        df, x="Date", y="Cumulative_Price", color="Category", title="Expenses Over Time"
    )
    fig.update_traces(mode="lines+markers", line=dict(shape="spline"))

    return templates.TemplateResponse(
        "home.html",
        {"request": request, "expenses": expenses, "user": user, "plot": fig.to_html()},
    )


@router.get("/", response_class=HTMLResponse)
async def get_all_by_user(
    request: Request,
    db: Session = Depends(get_db),
):
    user = await get_current_user(request)
    if user is None:
        return RedirectResponse(url="/authorization", status_code=status.HTTP_302_FOUND)
    expenses = (
        db.query(models.Wallet).filter(models.Wallet.owner_id == user.get("id")).all()
    )
    return templates.TemplateResponse(
        "home.html", {"request": request, "expenses": expenses, "user": user}
    )


@router.get("/add_expense", response_class=HTMLResponse)
async def create_expense(request: Request):
    user = await get_current_user(request)
    if user is None:
        return RedirectResponse(url="/authorization", status_code=status.HTTP_302_FOUND)
    return templates.TemplateResponse(
        "add_expense.html", {"request": request, "user": user}
    )


@router.post("/add_expense", response_class=HTMLResponse)
async def create_expense_commit(
    request: Request,
    title: str = Form(...),
    price: str = Form(...),
    category: str = Form(...),
    # date: str = Form(...), #### TODO poprawic wpisywanie dat
    db: Session = Depends(get_db),
):
    user = await get_current_user(request)
    if user is None:
        return RedirectResponse(url="/authorization", status_code=status.HTTP_302_FOUND)
    expense_model = models.Wallet()

    expense_model.title = title
    expense_model.price = price
    expense_model.category = category
    # expense_model.date = date
    expense_model.owner_id = user.get("id")
    db.add(expense_model)
    db.commit()

    return RedirectResponse(url="/wallet", status_code=status.HTTP_302_FOUND)


@router.get("/edit_expense/{expense_id}", response_class=HTMLResponse)
async def edit_expense(
    request: Request, expense_id: int, db: SessionLocal = Depends(get_db)
):
    user = await get_current_user(request)
    if user is None:
        return RedirectResponse(url="/authorization", status_code=status.HTTP_302_FOUND)
    expense = db.query(models.Wallet).filter(models.Wallet.id == expense_id).first()
    if not expense:
        raise HTTPException(status_code=404, detail="Expense not found")

    return templates.TemplateResponse(
        "edit_expense.html", {"request": request, "expense": expense, "user": user}
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
    user = await get_current_user(request)
    if user is None:
        return RedirectResponse(url="/authorization", status_code=status.HTTP_302_FOUND)
    expense = db.query(models.Wallet).filter(models.Wallet.id == expense_id).first()
    if not expense:
        raise HTTPException(status_code=404, detail="Expense not found")
    db.query(models.Wallet).filter(models.Wallet.id == expense_id).update(
        {
            "title": title,
            "price": price,
            "category": category,
            # "date": date,
            # Dodac inne kolumny, które chce zaktualizować
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
    user = await get_current_user(request)
    if user is None:
        return RedirectResponse(url="/authorization", status_code=status.HTTP_302_FOUND)
    expense_model = (
        db.query(models.Wallet)
        .filter(models.Wallet.id == expense_id)
        .filter(models.Wallet.owner_id == user.get("id"))
        .first()
    )
    if expense_model is None:
        return RedirectResponse(url="/wallet", status_code=status.HTTP_302_FOUND)

    db.query(models.Wallet).filter(models.Wallet.id == expense_id).delete()
    db.commit()

    return RedirectResponse(url="/wallet", status_code=status.HTTP_302_FOUND)


@router.get("/get_by_category/{category}")
async def get_by_category(
    request: Request,
    category: str,
    db: SessionLocal = Depends(get_db),
):
    user = await get_current_user(request)
    if user is None:
        return RedirectResponse(url="/authorization", status_code=status.HTTP_302_FOUND)

    expense_total = (
        db.query(func.sum(models.Wallet.price))
        .filter(models.Wallet.category == category)
        .filter(models.Wallet.owner_id == user.get("id"))
        .scalar()
    )
    return templates.TemplateResponse(
        "edit_expense.html", {"request": request, "expense_total": expense_total}
    )


@router.get("/")
async def get_cummulated_cost_by_category(
    request: Request,
    db: Session = Depends(get_db),
):
    user = await get_current_user(request)
    if user is None:
        return RedirectResponse(url="/authorization", status_code=302)

    expenses = (
        db.query(models.Wallet)
        .filter(models.Wallet.owner_id == user.get("id"))
        .order_by(models.Wallet.date)
        .all()
    )

    # Create a DataFrame from the expenses
    df = pd.DataFrame(
        [
            {"Date": expense.date, "Price": expense.price, "Category": expense.category}
            for expense in expenses
        ]
    )

    df.sort_values(by="Date", inplace=True)
    df["Cumulative_Price"] = df.groupby("Category")["Price"].cumsum()
    df["Date"] = pd.to_datetime(df["Date"])

    # Create a Plotly line chart
    fig = px.scatter(
        df,
        x="Date",
        y="Cumulative_Price",
        color="Category",
        title="Expenses Over Time",
    )
    fig.update_traces(mode="lines+markers", line=dict(shape="spline"))
    # Render the template with the HTML representation of the chart
    return templates.TemplateResponse(
        "home.html", {"request": request, "plot": fig.to_html()}
    )
