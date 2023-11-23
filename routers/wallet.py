import sys

sys.path.append("..")
import models
from database import engine, SessionLocal
from fastapi import Depends, HTTPException, APIRouter, Request, Form, status
from fastapi.responses import JSONResponse  # , HTMLResponse
from sqlalchemy.orm import Session

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

#### to bedzie potrzebne jak bede przechodzil na html
# templates = Jinja2Templates(directory="templates")


@router.get("/", response_class=JSONResponse)
# request - przekazuje fastapi prosbe o uzyskanie dostepu do html
async def get_expenses_json(request: Request, db: Session = Depends(get_db)):
    expenses = db.query(models.Wallet).filter(models.Wallet.owner_id == 3).all()
    expenses_data = [
        {"id": expense.id, "price": expense.price, "description": expense.description}
        for expense in expenses
    ]
    return expenses_data
