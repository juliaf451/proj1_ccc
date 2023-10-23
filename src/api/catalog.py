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
        inventory = connection.execute(sqlalchemy.text(
            "SELECT sku,inventory,price,potion_type FROM catalog WHERE inventory != 0")).all()
    
    inventory = sorted(inventory, key=lambda item: item[1], reverse=True)
    # Can return a max of 20 items.
    statement = []

    for item in inventory:
        
        statement.append({"sku": item[0],
        "name": f"{item[0]} POTION",
        "quantity": item[1],
        "price": item[2],
        "potion_type": item[3]}
        )

        if len(statement >= 6):
            break
        
    print(statement)
 

    return statement
