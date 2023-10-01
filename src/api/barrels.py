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
    barrels_delivered = 57
    print(barrels_delivered)

    return "OK"

# Gets called once a day
@router.post("/plan")
def get_wholesale_purchase_plan(wholesale_catalog: list[Barrel]):
    """ """
    print(wholesale_catalog)



    with db.engine.begin() as connection:
        inventory = connection.execute(sqlalchemy.text("SELECT * FROM global_inventory")).first()
        num_potions = inventory.num_red_potions
        gold = inventory.gold

        for barrel in wholesale_catalog:
            if gold >= barrel.price*barrel.quantity and num_potions < 15:
                sql_to_execute = sqlalchemy.text("UPDATE global_inventory SET num_red_ml = num_red_ml + :ml")
                connection.execute(sql_to_execute, parameters={'ml': barrel.ml_per_barrel*barrel.quantity})
                sql_to_execute = sqlalchemy.text("UPDATE global_inventory SET gold = gold - :cost")
                connection.execute(sql_to_execute, parameters={'cost': barrel.price*barrel.quantity})
                break  # Exit the loop after processing one barrel


    return [
        {
            "sku": "SMALL_RED_BARREL",
            "quantity": 1,
        }
    ]



