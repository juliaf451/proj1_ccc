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
    print(barrels_delivered)

    with db.engine.begin() as aconnection:

        for barrel in barrels_delivered:
            potion = barrel.potion_type
            quantity = 1
            cost = barrel.price

            if potion == [1,0,0,0]:
                sql_to_execute = sqlalchemy.text("UPDATE global_inventory SET num_red_ml = num_red_ml + :ml")
                connection.execute(sql_to_execute, parameters={'ml': barrel.ml_per_barrel*quantity})
            elif potion == [0,1,0,0]:
                sql_to_execute = sqlalchemy.text("UPDATE global_inventory SET num_green_ml = num_green_ml + :ml")
                connection.execute(sql_to_execute, parameters={'ml': barrel.ml_per_barrel*quantity})
            elif potion == [0,0,1,0]:
                sql_to_execute = sqlalchemy.text("UPDATE global_inventory SET num_blue_ml = num_blue_ml + :ml")
                connection.execute(sql_to_execute, parameters={'ml': barrel.ml_per_barrel*quantity})
            
            sql_to_execute = sqlalchemy.text("UPDATE global_inventory SET gold = gold - :cost")
            connection.execute(sql_to_execute, parameters={'cost': cost})


    return "OK"


# Gets called once a day
@router.post("/plan")
def get_wholesale_purchase_plan(wholesale_catalog: list[Barrel]):

# check the plan and return how many to buy
    
    print(wholesale_catalog)

    with db.engine.begin() as connection:
        inventory = connection.execute(sqlalchemy.text("SELECT * FROM global_inventory")).first()
        num_red_potions = inventory.num_red_potions
        num_blue_potions = inventory.num_blue_potions
        num_green_potions = inventory.num_green_potions
        gold = inventory.gold

        purchase = []
        # what other types of barrels are there? should we query by potion_type instead?
        for barrel in wholesale_catalog:
            cost = barrel.price
            if barrel.potion_type == [1,0,0,0] and gold >= cost and num_red_potions < 8:
                purchase.append({ "sku": barrel.sku,
                    "quantity": 1})
                gold = gold - cost
            elif barrel.potion_type == [0,0,1,0] and gold >= cost and num_blue_potions < 8:
                purchase.append({ "sku": barrel.sku,
                    "quantity": 1})
                gold = gold - cost
            elif barrel.potion_type == [0,1,0,0] and gold >= cost and num_green_potions < 8:
                purchase.append({ "sku": barrel.sku,
                    "quantity": 1})
                gold = gold - cost

    return purchase
