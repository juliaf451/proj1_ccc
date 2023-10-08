from fastapi import APIRouter
import sqlalchemy
from src import database as db



router = APIRouter()


@router.get("/catalog/", tags=["catalog"])
def get_catalog():
    """
    Each unique item combination must have only a single price.
    """
    with db.engine.begin() as connection:
        inventory = connection.execute(sqlalchemy.text("SELECT * FROM global_inventory")).first()
        num_red = inventory.num_red_potions
        num_blue = inventory.num_blue_potions
        num_green = inventory.num_green_potions
        
    # Can return a max of 20 items.
    statement = []

    if num_red != 0:
        statement.append({"sku": "RED_POTION_0",
        "name": "red potion",
        "quantity": num_red,
        "price": 50,
        "potion_type": [100, 0, 0, 0]}
        )
    
    if num_blue != 0:
        statement.append({"sku": "BLUE_POTION_0",
                "name": "blue potion",
                "quantity": num_blue,
                "price": 50,
                "potion_type": [0, 0, 100, 0]}) 

    if num_green != 0:
        statement.append({
                "sku": "GREEN_POTION_0",
                "name": "green potion",
                "quantity": num_green,
                "price": 50,
                "potion_type": [0, 100, 0, 0]}) 

    return statement
