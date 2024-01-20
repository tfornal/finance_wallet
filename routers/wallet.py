import sys

sys.path.append("..")
import models
from database import engine, SessionLocal
from fastapi import Depends, HTTPException, APIRouter, Request, Form, status, Query
from typing import List
from fastapi.responses import JSONResponse, HTMLResponse
from sqlalchemy import func, Date
from sqlalchemy.orm import Session

from starlette.responses import RedirectResponse
from starlette import status

from datetime import datetime, date
from typing import Optional

# from pydantic import BaseModel, Field
from .auth import oauth2_bearer, get_current_user
from typing import Annotated

### to bedzie ptorzebne gdy bede przechodzil na html
from fastapi.templating import Jinja2Templates


import pandas as pd
import plotly.express as px
from fastapi import Depends, Request
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from starlette.responses import RedirectResponse
import math

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


def plot_pie_chart():
    ...


@router.get("/date")
async def select_by_period(
    request: Request, db: Session = Depends(get_db), start_date: str = Form(...)
):
    user = await get_current_user(request)
    if user is None:
        return RedirectResponse(url="/auth", status_code=302)

    start_date = datetime.strptime("2018-11-21", "%Y-%m-%d").date()
    end_date = datetime.strptime("2023-12-01", "%Y-%m-%d").date()

    # Oblicz indeks początkowy dla zapytania

    # Użyj metody filter, aby zastosować warunek pomiędzy datami
    expense_by_date = (
        db.query(models.Wallet)
        .filter(models.Wallet.owner_id == user.get("id"))
        .filter(models.Wallet.date.between(start_date, end_date))
        .order_by(models.Wallet.date)
        .all()
    )

    return expense_by_date


def get_expenses_for_user(
    db: Session, user_id: int, order_by: str = "date"
) -> List[models.Wallet]:
    return (
        db.query(models.Wallet)
        .filter(models.Wallet.owner_id == user_id)
        .order_by(order_by)
        .all()
    )


def calculate_cumulative_prices(df: pd.DataFrame) -> pd.DataFrame:
    df.sort_values(by="Date", inplace=True)
    df["Cumulative_Price"] = df.groupby("Category")["Price"].cumsum()
    df["Date"] = pd.to_datetime(df["Date"])
    return df


def generate_scatter_plot(df: pd.DataFrame) -> px.scatter:
    pastel_palette = px.colors.qualitative.Pastel
    fig = px.scatter(
        df,
        x="Date",
        y="Cumulative_Price",
        color="Category",
        title="Expenses Over Time",
        color_discrete_sequence=pastel_palette,
    )
    fig.update_layout(
        updatemenus=[],
        plot_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(showgrid=True, gridcolor="lightgrey"),
        yaxis=dict(showgrid=True, gridcolor="lightgrey"),
        showlegend=True,
        legend=dict(bgcolor="rgba(255,255,255,0.7)"),
    )
    fig.update_traces(mode="lines+markers", line=dict(shape="spline"))
    return fig


def generate_pie_chart(df: pd.DataFrame) -> px.pie:
    pastel_palette = px.colors.qualitative.Pastel
    total_cost_by_category = df.groupby("Category")["Price"].sum().reset_index()
    fig = px.pie(
        total_cost_by_category,
        values="Price",
        names="Category",
        title="Wykres Kołowy z Liniami Procentowymi",
        hole=0.5,
        labels={"Values": "Procenty"},
        hover_data=["Category"],
        color_discrete_sequence=pastel_palette,
    )
    fig.update_layout(updatemenus=[])
    fig.update_traces(textposition="outside", textinfo="percent+label")
    return fig


@router.get("/")
async def get_expenses_by_user(
    request: Request,
    page: int = Query(1, ge=1),
    items_per_page: int = Query(300, le=100),
    db: Session = Depends(get_db),
):
    user = await get_current_user(request)
    if user is None:
        return RedirectResponse(url="/auth", status_code=302)

    all_expenses = get_expenses_for_user(db, user.get("id"))

    total_pages = math.ceil(len(all_expenses) / items_per_page)
    start_index = (page - 1) * items_per_page
    end_index = start_index + items_per_page
    expenses = all_expenses[start_index:end_index]

    df = pd.DataFrame(
        [
            {
                "Index": i + start_index,
                "Date": expense.date,
                "Price": expense.price,
                "Category": expense.category,
            }
            for i, expense in enumerate(expenses)
        ]
    )
    if df.empty:
        return templates.TemplateResponse(
            "wallet.html",
            {
                "request": request,
                "expenses": expenses,
                "user": user,
                "page": page,
                "total_pages": total_pages,
                "start_index": start_index,
            },
        )
    df = calculate_cumulative_prices(df)

    scatter_plot = generate_scatter_plot(df)
    pie_chart = generate_pie_chart(df)

    return templates.TemplateResponse(
        "wallet.html",
        {
            "request": request,
            "expenses": expenses,
            "user": user,
            "plot_trend": scatter_plot.to_html(),
            "plot_pie": pie_chart.to_html(),
            "page": page,
            "total_pages": total_pages,
            "start_index": start_index,
        },
    )


@router.get("/add_expense", response_class=HTMLResponse)
async def create_expense(request: Request):
    user = await get_current_user(request)
    if user is None:
        return RedirectResponse(url="/auth", status_code=status.HTTP_302_FOUND)
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
        return RedirectResponse(url="/auth", status_code=status.HTTP_302_FOUND)
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
        return RedirectResponse(url="/auth", status_code=status.HTTP_302_FOUND)
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
        return RedirectResponse(url="/auth", status_code=status.HTTP_302_FOUND)
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
        return RedirectResponse(url="/auth", status_code=status.HTTP_302_FOUND)
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
        return RedirectResponse(url="/auth", status_code=status.HTTP_302_FOUND)

    expense_total = (
        db.query(func.sum(models.Wallet.price))
        .filter(models.Wallet.category == category)
        .filter(models.Wallet.owner_id == user.get("id"))
        .scalar()
    )
    return templates.TemplateResponse(
        "edit_expense.html", {"request": request, "expense_total": expense_total}
    )
