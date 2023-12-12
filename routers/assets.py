import sys

sys.path.append("..")
import models
from database import engine, SessionLocal
from fastapi import (
    Depends,
    HTTPException,
    APIRouter,
    Request,
    Form,
    status,
    Query,
)
from fastapi.responses import JSONResponse, HTMLResponse
from sqlalchemy import func, Date, event
from sqlalchemy.orm import Session

from starlette.responses import RedirectResponse
from starlette import status

from datetime import datetime, date
from typing import Optional

# from pydantic import BaseModel, Field
from .authorization import oauth2_bearer, get_current_user
from typing import Annotated


import pandas as pd
import plotly.express as px
from fastapi import Depends, Request
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from starlette.responses import RedirectResponse
import math

router = APIRouter(
    prefix="/assets", tags=["assets"], responses={404: {"description": "Not found"}}
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


def format_number(number):
    if number >= 1_000_000:
        return f"{number / 1_000_000:.1f}M"
    elif number >= 1_000:
        return f"{number / 1_000:.1f}k"
    else:
        return str(number)


def create_assets_dataframe(all_assets):
    return pd.DataFrame(
        [
            {
                "Title": asset.title,
                "Asset_value": asset.asset_value_pln,
                "Percentage_share": asset.percentage_share,
                "Category": asset.category,
            }
            for asset in all_assets
        ]
    )


def create_pie_chart(df, total_asset_value):
    color_palette = px.colors.qualitative.Pastel
    fig = px.pie(
        df,
        values="Asset_value",
        names="Category",
        hole=0.6,
        labels={"Values": "Procenty"},
        hover_data=["Title"],
        color_discrete_sequence=color_palette,
    )
    fig.update_layout(
        annotations=[
            dict(
                text=f"{format_number(total_asset_value)} PLN",
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


@router.get("/")
async def get_all_assets(request: Request, db: Session = Depends(get_db)):
    user = await get_current_user(request)
    if user is None:
        return RedirectResponse(url="/authorization", status_code=302)

    calculate_percentage_share(user.get("id"), db)

    all_assets = (
        db.query(models.Assets)
        .filter(models.Assets.owner_id == user.get("id"))
        .order_by(models.Assets.asset_value_pln.asc())
        .all()
    )
    df = create_assets_dataframe(all_assets)
    total_asset_value = df["Asset_value"].sum()
    fig = create_pie_chart(df, total_asset_value)

    return templates.TemplateResponse(
        "assets.html",
        {
            "request": request,
            "user": user,
            "assets": all_assets,
            "plot_pie": fig.to_html(),
        },
    )


@router.get("/edit/{asset_id}", response_class=HTMLResponse)
async def edit_asset(
    request: Request, asset_id: int, db: SessionLocal = Depends(get_db)
):
    user = await get_current_user(request)
    if user is None:
        return RedirectResponse(url="/authorization", status_code=status.HTTP_302_FOUND)
    asset = db.query(models.Assets).filter(models.Assets.id == asset_id).first()
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    return templates.TemplateResponse(
        "edit_asset.html", {"request": request, "asset": asset, "user": user}
    )


@router.post("/edit/{asset_id}", response_class=HTMLResponse)
async def edit_expense_commit(
    request: Request,
    asset_id: int,
    title: str = Form(...),
    asset_value_pln: str = Form(...),
    category: str = Form(...),
    db: Session = Depends(get_db),
):
    user = await get_current_user(request)
    if user is None:
        return RedirectResponse(url="/authorization", status_code=status.HTTP_302_FOUND)
    expense = db.query(models.Assets).filter(models.Assets.id == asset_id).first()
    if not expense:
        raise HTTPException(status_code=404, detail="Expense not found")
    db.query(models.Assets).filter(models.Assets.id == asset_id).update(
        {
            "title": title,
            "asset_value_pln": asset_value_pln,
            "category": category,
        }
    )
    db.commit()

    return RedirectResponse(url="/assets", status_code=status.HTTP_302_FOUND)


@router.get("/add_asset", response_class=HTMLResponse)
async def add_asset(request: Request):
    user = await get_current_user(request)
    if user is None:
        return RedirectResponse(url="/authorization", status_code=status.HTTP_302_FOUND)
    return templates.TemplateResponse(
        "add_asset.html", {"request": request, "user": user}
    )


@router.post("/add_asset", response_class=HTMLResponse)
async def add_asset_commit(
    request: Request,
    title: str = Form(...),
    asset_value_pln: str = Form(...),
    category: str = Form(...),
    db: Session = Depends(get_db),
):
    user = await get_current_user(request)
    if user is None:
        return RedirectResponse(url="/authorization", status_code=status.HTTP_302_FOUND)

    asset_model = models.Assets()
    asset_model.title = title
    asset_model.asset_value_pln = asset_value_pln
    asset_model.category = category
    asset_model.owner_id = user.get("id")

    db.add(asset_model)
    db.commit()

    return RedirectResponse(url="/assets", status_code=status.HTTP_302_FOUND)


@router.get("/delete/{asset_id}")
async def delete_asset(
    request: Request,
    asset_id: int,
    db: SessionLocal = Depends(get_db),
):
    user = await get_current_user(request)
    if user is None:
        return RedirectResponse(url="/authorization", status_code=status.HTTP_302_FOUND)
    asset_model = (
        db.query(models.Assets)
        .filter(models.Assets.id == asset_id)
        .filter(models.Assets.owner_id == user.get("id"))
        .first()
    )
    if asset_model is None:
        return RedirectResponse(url="/assets", status_code=status.HTTP_302_FOUND)

    db.query(models.Assets).filter(models.Assets.id == asset_id).delete()
    db.commit()

    return RedirectResponse(url="/assets", status_code=status.HTTP_302_FOUND)
