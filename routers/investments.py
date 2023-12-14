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
        try:  ##########################TODO!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
            db.query(models.Investments).filter(
                models.Investments.asset == asset
            ).update(
                {
                    "current_price": price["usd"],
                }
            )
        except:  ##########################TODO!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
            continue
    db.commit()


def update_price_list(df: pd.DataFrame, prices: dict):
    df.set_index("asset", inplace=True)
    for coin, price in prices.items():
        if coin in df.index:
            df.at[coin, "current_price"] = price["usd"]
    df = df.reset_index()
    return df


def get_cumulated_value(df):
    value = df["current_value"].sum()
    return value


def get_cumulated_cost(df):
    value = df["invested"].sum()
    return value


@router.get("/")
async def get_all_crypto(request: Request, db: Session = Depends(get_db)):
    user = await get_current_user(request)
    if user is None:
        return RedirectResponse(url="/authorization", status_code=302)

    update_current_price(user.get("id"), db)
    # update_current_holdings_value(user.get("id"), db)

    all_crypto_assets = (
        db.query(models.Investments)
        .filter(models.Investments.owner_id == user.get("id"))
        .order_by(models.Investments.current_value.desc())
        .all()
    )

    df = create_assets_dataframe(all_crypto_assets)
    current_value = get_cumulated_value(df)
    invested = get_cumulated_cost(df)

    fig = create_pie_chart(df)

    return templates.TemplateResponse(
        "investments.html",
        {
            "request": request,
            "user": user,
            "all_crypto_assets": all_crypto_assets,
            "current_value": current_value,
            "invested": invested,
            "plot_pie": fig.to_html(),
        },
    )


@router.get("/add", response_class=HTMLResponse)
async def add_crypto_asset(request: Request, db: SessionLocal = Depends(get_db)):
    user = await get_current_user(request)
    if user is None:
        return RedirectResponse(url="/authorization", status_code=status.HTTP_302_FOUND)
    return templates.TemplateResponse(
        "add_crypto_asset.html",
        {"request": request, "user": user},
    )


@router.post("/add", response_class=HTMLResponse)
async def add_crypto_asset_commit(
    request: Request,
    # crypto_asset: str = Form(...),
    current_price: float = Form(...),
    holdings: float = Form(...),
    invested: float = Form(...),
    db: Session = Depends(get_db),
):
    user = await get_current_user(request)
    if user is None:
        return RedirectResponse(url="/authorization", status_code=status.HTTP_302_FOUND)

    asset_model = models.Investments()
    asset_model.asset = "test"  # crypto_asset##########################TODO!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
    asset_model.current_price = current_price
    asset_model.holdings = holdings
    asset_model.invested = invested
    asset_model.current_value = (
        0.1  ##########################T ODO!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
    )
    asset_model.pnl = (
        0.1  ##########################TODO!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
    )
    asset_model.owner_id = user.get("id")
    db.add(asset_model)
    db.commit()

    return RedirectResponse(url="/investments", status_code=status.HTTP_302_FOUND)


@router.get("/edit/{crypto_asset_id}", response_class=HTMLResponse)
async def edit_crypto_asset(
    request: Request, crypto_asset_id: int, db: SessionLocal = Depends(get_db)
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
    crypto_asset_id=int,
    asset: str = Form(...),
    current_price: float = Form(...),
    holdings: float = Form(...),
    invested: float = Form(...),
    db: Session = Depends(get_db),
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
        raise HTTPException(status_code=404, detail="Asset not found")

    db.query(models.Investments).filter(
        models.Investments.id == crypto_asset_id
    ).update(
        {
            "asset": asset,
            "current_price": current_price,
            "holdings": holdings,
            "invested": invested,
        }
    )
    db.commit()

    return RedirectResponse(url="/investments", status_code=status.HTTP_302_FOUND)


@router.get("/delete/{crypto_asset_id}")
async def delete_asset(
    request: Request,
    crypto_asset_id: int,
    db: SessionLocal = Depends(get_db),
):
    user = await get_current_user(request)
    if user is None:
        return RedirectResponse(url="/authorization", status_code=status.HTTP_302_FOUND)
    asset_model = (
        db.query(models.Investments)
        .filter(models.Investments.id == crypto_asset_id)
        .filter(models.Investments.owner_id == user.get("id"))
        .first()
    )
    if asset_model is None:
        return RedirectResponse(url="/investments", status_code=status.HTTP_302_FOUND)

    db.query(models.Investments).filter(
        models.Investments.id == crypto_asset_id
    ).delete()
    db.commit()

    return RedirectResponse(url="/investments", status_code=status.HTTP_302_FOUND)
