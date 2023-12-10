import sys

sys.path.append("..")
import models
from database import engine, SessionLocal
from fastapi import Depends, HTTPException, APIRouter, Request, Form, status, Query
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
        hole=0.7,
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
    fig.update_layout(updatemenus=[])
    return fig


@router.get("/")
async def get_all_assets(request: Request, db: Session = Depends(get_db)):
    user = await get_current_user(request)
    if user is None:
        return RedirectResponse(url="/authorization", status_code=302)

    all_assets = (
        db.query(models.Assets).filter(models.Assets.owner_id == user.get("id")).all()
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


@router.get("/", response_class=HTMLResponse)
async def get_all_by_user(
    request: Request,
    db: Session = Depends(get_db),
):
    user = await get_current_user(request)
    if user is None:
        return RedirectResponse(url="/authorization", status_code=status.HTTP_302_FOUND)
    assets = (
        db.query(models.Wallet).filter(models.Assets.owner_id == user.get("id")).all()
    )
    return templates.TemplateResponse(
        "assets.html", {"request": request, "assets": assets, "user": user}
    )
