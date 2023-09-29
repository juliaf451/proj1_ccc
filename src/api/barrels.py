from fastapi import APIRouter, Depends
from pydantic import BaseModel
from src.api import auth
import sqlalchemy
from src import database as db



router = APIRouter(
    prefix="/barrels",
    tags=["barrels"],
    dependencies=[Depends(auth.get_api_key)],
)

class Barrel(BaseModel):
    sku: str

    ml_per_barrel: int
    potion_type: list[int]
    price: int

    quantity: int

@router.post("/deliver")
def post_deliver_barrels(barrels_delivered: list[Barrel]):
    """ """
    print(barrels_delivered)

    return "OK"

# Gets called once a day
@router.post("/plan")
def get_wholesale_purchase_plan(wholesale_catalog: list[Barrel]):
    """ """
    print(wholesale_catalog)

    prices = [barrel.price for barrel in wholesale_catalog]
    ml = [barrel.ml_per_barrel for barrel in wholesale_catalog]

    with db.engine.begin() as connection:
        if connection.execute(sqlalchemy.text("SELECT gold FROM global_inventory")) >= prices:
            sql_to_execute = sqlalchemy.text("UPDATE global_inventory SET num_red_ml = num_red_ml+ml")
            result = connection.execute(sql_to_execute)
            sql_to_execute = sqlalchemy.text("UPDATE global_inventory SET gold = gold-prices")
            result = connection.execute(sql_to_execute)

    return [
        {
            "sku": "SMALL_RED_BARREL",
            "quantity": 1,
        }
    ]



