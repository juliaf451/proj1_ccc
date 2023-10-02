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
        quantity = item.quantity
    
    with db.engine.begin() as connection:
        
        inventory = connection.execute(sqlalchemy.text("SELECT num_red_ml, num_red_potions FROM global_inventory")).first()
        num_ml = inventory.num_red_ml
        
        sql_to_execute = sqlalchemy.text("UPDATE global_inventory SET num_red_potions = num_red_potions+:potions")
        connection.execute(sql_to_execute, parameters={'potions': quantity})

        sql_to_execute = sqlalchemy.text("UPDATE global_inventory SET num_red_ml = num_red_ml-:ml")
        connection.execute(sql_to_execute, parameters={'ml': quantity * 100})

    return "OK"


# Gets called 4 times a day
@router.post("/plan")
def get_bottle_plan():
    
    # Determine how many potions to make
    
    with db.engine.begin() as connection:
        
        inventory = connection.execute(sqlalchemy.text("SELECT num_red_ml, num_red_potions FROM global_inventory")).first()
        num_ml = inventory.num_red_ml
        
        quantity = int(num_ml/100)
            
    

    # Each bottle has a quantity of what proportion of red, blue, and
    # green potion to add.
    # Expressed in integers from 1 to 100 that must sum up to 100.

    # Initial logic: bottle all barrels into red potions.

    return [
            {
                "potion_type": [100, 0, 0, 0],
                "quantity": quantity,
            }
        ]


