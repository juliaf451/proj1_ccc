from fastapi import APIRouter, Depends
from enum import Enum
from pydantic import BaseModel
from src.api import auth
import sqlalchemy
from src import database as db
import json



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
    red_ml = 0
    blue_ml = 0
    green_ml = 0
    dark_ml = 0

    potions = []
    num = []

    for item in potions_delivered:
        potion_type = item.potion_type
        quantity = item.quantity
        red_ml = red_ml + potion_type[0]*quantity
        green_ml = green_ml + potion_type[1]*quantity
        blue_ml = blue_ml + potion_type[2]*quantity
        dark_ml = dark_ml + potion_type[3]*quantity

        potions.append(potion_type)
        num.append(quantity)
    

    with db.engine.begin() as connection:

        connection.execute(
            sqlalchemy.text(
                """
                UPDATE global_inventory SET
                num_red_ml = num_red_ml - :red_ml,
                num_blue_ml = num_blue_ml - :blue_ml,
                num_green_ml = num_green_ml - :green_ml,
                num_dark_ml = num_dark_ml - :dark_ml
                """),
            [{'red_ml':red_ml,'green_ml':green_ml,'blue_ml':blue_ml,'dark_ml':dark_ml}])

        for i in range(0,len(num)):
            potions_jsonb = json.dumps(potions[i])
            connection.execute(
                sqlalchemy.text(
                    """
                    UPDATE catalog
                    SET inventory = catalog.inventory + :num
                    WHERE catalog.potion_type = :potions
                    """),
                [{'num':num[i],'potions':potions_jsonb}])

    return "OK"


# Gets called 4 times a day
@router.post("/plan")
def get_bottle_plan():
    
    # Determine how many potions to make
    # Pull all the types of potions and how many we have of each. 
    # Order the list by which we have the least of, loop through bottling that way

    with db.engine.begin() as connection:
        
        ml_inventory = connection.execute(sqlalchemy.text("SELECT * FROM global_inventory")).first()
        num_red_ml = ml_inventory.num_red_ml
        num_blue_ml = ml_inventory.num_blue_ml
        num_green_ml = ml_inventory.num_green_ml
        num_dark_ml = ml_inventory.num_dark_ml

        catalog = connection.execute(sqlalchemy.text("SELECT inventory,potion_type FROM catalog")).all()
        catalog = sorted(catalog, key=lambda item: item[0])


    
        bottle = []
        
        while num_red_ml > 25 and num_blue_ml > 25 and num_green_ml > 25 and num_dark_ml > 25:
            for item in catalog:
                quantity = 0
                potion_type = item[1]
                if num_red_ml >= potion_type[0] and num_green_ml >= potion_type[1] and \
                    num_blue_ml >= potion_type[2] and num_dark_ml >= potion_type[3]:

                    quantity += 1

                    num_red_ml = num_red_ml-potion_type[0]
                    num_green_ml = num_green_ml-potion_type[1]
                    num_blue_ml = num_blue_ml-potion_type[2]
                    num_dark_ml = num_dark_ml-potion_type[3]

                    bottle.append({
                        "potion_type": potion_type,
                        "quantity": quantity,
                    })

        print(bottle)

        return bottle
 