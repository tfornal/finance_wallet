import sys

sys.path.append("..")
import models
from database import engine, SessionLocal
from fastapi import Depends, HTTPException, APIRouter, Request, Form, status, Query
from typing import List
from fastapi.responses import JSONResponse, HTMLResponse
from sqlalchemy import func, Date, text
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
from fastapi import Depends, Request
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from starlette.responses import RedirectResponse


import math
from pycoingecko import CoinGeckoAPI

router = APIRouter(
    prefix="/investments",
    tags=["investments"],
    responses={404: {"description": "Not found"}},
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


def calculate_percentage_share(user_id: int, db: Session):
    assets = db.query(models.Assets).filter(models.Assets.owner_id == user_id).all()
    total_asset_value = sum(asset.asset_value_pln for asset in assets)
    for asset in assets:
        asset.percentage_share = (
            (asset.asset_value_pln / total_asset_value) * 100
            if total_asset_value
            else 0
        )
    db.commit()


def get_recent_prices(crypto_assets: list):
    cg = CoinGeckoAPI()
    price = cg.get_price(ids=crypto_assets, vs_currencies="usd")

    return price


def format_number(number):
    if number >= 1_000_000:
        return f"{number / 1_000_000:.1f}M"
    elif number >= 1_000:
        return f"{number / 1_000:.1f}k"
    else:
        return str(number)


def update_df(df):
    USD_PLN = 4.03
    df["invested"] = pd.to_numeric(df["invested"], errors="coerce")
    df["current_value"] = pd.to_numeric(df["current_value"], errors="coerce")
    # Replace commas with periods and convert to float for "current_price"
    df["current_price"] = df["current_price"].astype("str")
    df["current_price"] = df["current_price"].str.replace(",", ".")
    df["current_price"] = df["current_price"].astype("float64")

    df["holdings"] = df["holdings"].astype("str")
    df["holdings"] = df["holdings"].str.replace(",", ".")
    df["holdings"] = df["holdings"].astype("float64")
    # Calculate "current_value" based on "current_price" and "holdings"
    df["current_value"] = df["current_price"] * df["holdings"] * USD_PLN
    return df


def create_assets_dataframe(all_investments):
    return pd.DataFrame(
        [
            {
                "asset": investment.asset,
                "current_price": investment.current_price,
                "holdings": investment.holdings,
                "invested": investment.invested,
                "current_value": investment.current_value,
                "pnl": investment.pnl,
            }
            for investment in all_investments
        ]
    )


def create_pie_chart(df):
    # Ensure the "invested" and "current_value" columns are numeric

    invested_total_amount = df["invested"].sum()
    current_total_value = df["current_value"].sum()

    color_palette = px.colors.qualitative.Pastel
    fig = px.pie(
        df,
        values="current_value",
        names="asset",
        hole=0.6,
        labels={"asset": "Coin"},
        # hover_data=["holdings"],
        color_discrete_sequence=color_palette,
    )
    fig.update_layout(
        annotations=[
            dict(
                text=f"{format_number(current_total_value)} PLN",
                showarrow=False,
                x=0.5,
                y=0.5,
                font=dict(size=30, color="green"),
            )
        ]
    )
    fig.update_traces(
        textinfo="percent",
        insidetextfont=dict(size=14),
    )
    return fig


def get_list_of_crypto_assets(user_id: int, db: Session):
    list_of_assets = (
        db.query(models.Investments.asset)
        .filter(models.Investments.owner_id == user_id)
        .distinct()
        .all()
    )
    list_of_assets = [i[0] for i in list_of_assets]
    return list_of_assets


def update_current_price(user_id: int, db: Session):
    list_of_assets = get_list_of_crypto_assets(user_id, db)
    prices = get_recent_prices(list_of_assets)

    for asset, price in prices.items():
        print(asset, price)
        db.query(models.Investments).filter(models.Investments.asset == asset).update(
            {
                "current_price": price["usd"],
            }
        )
    db.commit()


def update_current_holdings_value(user_id: int, db: Session):
    crypto_assets = (
        db.query(models.Investments)
        .filter(models.Investments.owner_id == user_id)
        .all()
    )
    for coin in crypto_assets:
        coin.current_value = coin.current_price * coin.holdings * 4.03
    db.commit()


def update_price_list(df: pd.DataFrame, prices: dict):
    df.set_index("asset", inplace=True)
    for coin, price in prices.items():
        if coin in df.index:
            df.at[coin, "current_price"] = price["usd"]
    df = df.reset_index()
    return df


@router.get("/")
async def get_all_investments(request: Request, db: Session = Depends(get_db)):
    user = await get_current_user(request)
    if user is None:
        return RedirectResponse(url="/authorization", status_code=302)

    update_current_price(user.get("id"), db)
    update_current_holdings_value(user.get("id"), db)

    all_crypto_assets = (
        db.query(models.Investments)
        .filter(models.Investments.owner_id == user.get("id"))
        .all()
    )
    df = create_assets_dataframe(all_crypto_assets)
    fig = create_pie_chart(df)

    return templates.TemplateResponse(
        "investments.html",
        {
            "request": request,
            "user": user,
            "all_crypto_assets": all_crypto_assets,
            "plot_pie": fig.to_html(),
        },
    )


@router.get("/edit/{crypto_asset_id}", response_class=HTMLResponse)
async def edit_expense(
    request: Request, expense_id: int, db: SessionLocal = Depends(get_db)
):
    user = await get_current_user(request)
    if user is None:
        return RedirectResponse(url="/authorization", status_code=status.HTTP_302_FOUND)
    crypto_asset = (
        db.query(models.Investments)
        .filter(models.Investments.id == crypto_asset_id)
        .first()
    )
    if not crypto_asset:
        raise HTTPException(status_code=404, detail="Expense not found")

    return templates.TemplateResponse(
        "edit_crypto_asset.html",
        {"request": request, "crypto_asset": crypto_asset, "user": user},
    )


@router.post("/edit/{crypto_asset_id}", response_class=HTMLResponse)
async def edit_crypto_asset_commit(
    request: Request,
    crypto_asset_id: int,
    crypto_asset: str = Form(...),
    price: float = Form(...),
    category: str = Form(...),
    db: Session = Depends(get_db),
):
    # breakpoint()
    user = await get_current_user(request)
    if user is None:
        return RedirectResponse(url="/authorization", status_code=status.HTTP_302_FOUND)
    expense = (
        db.query(models.Investments)
        .filter(models.Investments.id == crypto_asset_id)
        .first()
    )
    if not expense:
        raise HTTPException(status_code=404, detail="Expense not found")
    db.query(models.Investments).filter(
        models.Investments.id == crypto_asset_id
    ).update(
        {
            "crypto_asset": crypto_asset,
            "holdings": holdings,
            "invested": invested,
            # "date": date,
            # Dodac inne kolumny, które chce zaktualizować
        }
    )
    db.commit()


#     return RedirectResponse(url="/wallet", status_code=status.HTTP_302_FOUND)
