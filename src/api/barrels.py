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


    
    with db.engine.begin() as connection:

        cost = 0
        red_ml = 0
        blue_ml = 0
        green_ml = 0
        dark_ml = 0

        for barrel in barrels_delivered:
            potion = barrel.potion_type
            quantity = barrel.quantity
            cost = cost + barrel.price*quantity

            if potion == [1,0,0,0]:
                red_ml=red_ml+barrel.ml_per_barrel*quantity
                # sql_to_execute = sqlalchemy.text("UPDATE global_inventory SET num_red_ml = num_red_ml + :ml")
                # connection.execute(sql_to_execute, parameters={'ml': barrel.ml_per_barrel*quantity})
            elif potion == [0,1,0,0]:
                green_ml=green_ml+barrel.ml_per_barrel*quantity
                # sql_to_execute = sqlalchemy.text("UPDATE global_inventory SET num_green_ml = num_green_ml + :ml")
                # connection.execute(sql_to_execute, parameters={'ml': barrel.ml_per_barrel*quantity})
            elif potion == [0,0,1,0]:
                blue_ml=blue_ml+barrel.ml_per_barrel*quantity
                # sql_to_execute = sqlalchemy.text("UPDATE global_inventory SET num_blue_ml = num_blue_ml + :ml")
                # connection.execute(sql_to_execute, parameters={'ml': barrel.ml_per_barrel*quantity})
            elif potion == [0,0,0,1]:
                dark_ml=dark_ml+barrel.ml_per_barrel*quantity
            # sql_to_execute = sqlalchemy.text("UPDATE global_inventory SET gold = gold - :cost")
            # connection.execute(sql_to_execute, parameters={'cost': cost})

    with db.engine.begin() as connection:
        connection.execute(
            sqlalchemy.text(
                """
                UPDATE global_inventory SET
                num_red_ml = num_red_ml + :red_ml,
                num_blue_ml = num_blue_ml + :blue_ml,
                num_green_ml = num_green_ml + :green_ml,
                num_dark_ml = num_dark_ml + :dark_ml,
                gold = gold - :cost
                """),
            [{'red_ml':red_ml,'green_ml':green_ml,'blue_ml':blue_ml,'dark_ml':dark_ml,'cost':cost}])

    print(["Purchased: ",red_ml,green_ml,blue_ml,dark_ml,cost])
    return "OK"


# Gets called once a day
@router.post("/plan")
def get_wholesale_purchase_plan(wholesale_catalog: list[Barrel]):

# check the plan and return how many to buy
    
    print(wholesale_catalog)

    with db.engine.begin() as connection:
        inventory = connection.execute(sqlalchemy.text("SELECT * FROM global_inventory")).first()
        num_red_ml = inventory.num_red_ml
        num_blue_ml = inventory.num_blue_ml
        num_green_ml = inventory.num_green_ml
        num_dark_ml = inventory.num_dark_ml
        gold = inventory.gold

        purchase = []
        # what other types of barrels are there? should we query by potion_type instead?
        for barrel in wholesale_catalog:
            cost = barrel.price
            ml = barrel.ml_per_barrel

            
            if barrel.potion_type == [1,0,0,0] and gold >= cost and num_red_ml < 800 and ml <= 500:
                purchase.append({ "sku": barrel.sku, "quantity": 1})
                gold = gold - cost
            elif barrel.potion_type == [0,0,1,0] and gold >= cost and num_blue_ml < 800 and ml <= 500:
                purchase.append({ "sku": barrel.sku, "quantity": 1})
                gold = gold - cost
            elif barrel.potion_type == [0,1,0,0] and gold >= cost and num_green_ml < 800 and ml <= 500:
                purchase.append({ "sku": barrel.sku, "quantity": 1})
                gold = gold - cost
            elif barrel.potion_type == [0,0,0,1] and gold >= cost and num_dark_ml < 800 and ml <= 500:
                purchase.append({ "sku": barrel.sku, "quantity": 1})
                gold = gold - cost

    return purchase
