from fastapi import APIRouter, Depends
from enum import Enum
from pydantic import BaseModel
from src.api import auth
import sqlalchemy
from src import database as db



router = APIRouter(
    prefix="/bottler",
    tags=["bottler"],
    dependencies=[Depends(auth.get_api_key)],
)

class PotionInventory(BaseModel):
    potion_type: list[int]
    quantity: int

@router.post("/deliver")
def post_deliver_bottles(potions_delivered: list[PotionInventory]):
    # Update database
    print(potions_delivered)

    for item in potions_delivered:
        if item.potion_type == [100, 0, 0, 0]:
            quantity_red = item.quantity

        elif item.potion_type == [0, 100, 0, 0]:
            quantity_green = item.quantity

        elif item.potion_type == [0, 0, 100, 0]:
            quantity_blue = item.quantity
    
    with db.engine.begin() as connection:
        
        sql_to_execute = sqlalchemy.text("UPDATE global_inventory SET num_red_potions = num_red_potions+:potions")
        connection.execute(sql_to_execute, parameters={'potions': quantity_red})

        sql_to_execute = sqlalchemy.text("UPDATE global_inventory SET num_red_ml = num_red_ml-:ml")
        connection.execute(sql_to_execute, parameters={'ml': quantity_red * 100})

        sql_to_execute = sqlalchemy.text("UPDATE global_inventory SET num_green_potions = num_green_potions+:potions")
        connection.execute(sql_to_execute, parameters={'potions': quantity_green})

        sql_to_execute = sqlalchemy.text("UPDATE global_inventory SET num_red_ml = num_red_ml-:ml")
        connection.execute(sql_to_execute, parameters={'ml': quantity_green * 100})

        sql_to_execute = sqlalchemy.text("UPDATE global_inventory SET num_blue_potions = num_blue_potions+:potions")
        connection.execute(sql_to_execute, parameters={'potions': quantity_blue})

        sql_to_execute = sqlalchemy.text("UPDATE global_inventory SET num_blue_ml = num_blue_ml-:ml")
        connection.execute(sql_to_execute, parameters={'ml': quantity_blue * 100})

    return "OK"


# Gets called 4 times a day
@router.post("/plan")
def get_bottle_plan():
    
    # Determine how many potions to make
    
    with db.engine.begin() as connection:
        
        inventory = connection.execute(sqlalchemy.text("SELECT num_red_ml, num_red_potions FROM global_inventory")).first()
        num_red_ml = inventory.num_red_ml
        num_blue_ml = inventory.num_blue_ml
        num_green_ml = inventory.num_green_ml
        
        quantity_red = int(num_red_ml/100)
        quantity_blue = int(num_blue_ml/100)
        quantity_green = int(num_green_ml/100)
            

    # Each bottle has a quantity of what proportion of red, blue, and
    # green potion to add.
    # Expressed in integers from 1 to 100 that must sum up to 100.

    # Initial logic: bottle all barrels into red potions.

    return [
            {
                "potion_type": [100, 0, 0, 0],
                "quantity": quantity_red,
            },
            {
                "potion_type": [0, 100, 0, 0],
                "quantity": quantity_green,
            },
            {
                "potion_type": [0, 0, 100, 0],
                "quantity": quantity_blue,
            }
        ]


