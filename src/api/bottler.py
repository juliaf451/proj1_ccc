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
    total = 0

    potions = []
    num = []

    for item in potions_delivered:
        potion_type = item.potion_type
        quantity = item.quantity
        total += quantity

        # How we know what to add to the ledger

        red_ml = red_ml + potion_type[0]*quantity
        green_ml = green_ml + potion_type[1]*quantity
        blue_ml = blue_ml + potion_type[2]*quantity
        dark_ml = dark_ml + potion_type[3]*quantity

        potions.append(potion_type)
        num.append(quantity)
    
    ml = red_ml+blue_ml+green_ml+dark_ml

    with db.engine.begin() as connection:

        # Add the bottle transaction to the transaction table
        # Update potions and ml ledgers with the bottler transaction
        # Sum up potions and ml ledgers and update inventories corresponding

         # Add the transaction to the ledger
        transaction_id = connection.execute(
            sqlalchemy.text(
                """
                INSERT INTO transactions (description) 
                VALUES ('Bottling :ml ml into :num potions')
                RETURNING id
                """), ({'num':total, 'ml':ml})).scalar()

        # Update the potions ledger - one row per potion type
        for item in potions_delivered:
            potions_jsonb = json.dumps(item.potion_type)
            pot_id = connection.execute(
                sqlalchemy.text(
                    """
                    SELECT id
                    FROM catalog
                    WHERE :type = catalog.potion_type
                    """), ({'type':potions_jsonb})).scalar()
            
            connection.execute(
                sqlalchemy.text(
                    """
                    INSERT INTO potion_ledger (transaction_id,potion_id,quantity_change) 
                    VALUES (:transaction_id, :id,:quantity)
                    """), ({'transaction_id':transaction_id, 'id':pot_id,'quantity':item.quantity}))
        
        # Update the barrels ledger
        connection.execute(
            sqlalchemy.text(
                """
                INSERT INTO barrel_ledger 
                (transaction_id,change_red,change_green,change_blue,change_dark) 
                VALUES (:transaction_id,:red,:green,:blue,:dark)
                """), ({'transaction_id':transaction_id,'red':-red_ml,'green':-green_ml,'blue':-blue_ml,'dark':-dark_ml}))

        # Update our inventory by summing the ledger
        # connection.execute(
        #         sqlalchemy.text(
        #             """
        #             UPDATE global_inventory
        #             SET num_red_ml = (SELECT SUM(change_red)
        #             FROM barrel_ledger),
        #             num_blue_ml = (SELECT SUM(change_blue)
        #             FROM barrel_ledger),
        #             num_green_ml = (SELECT SUM(change_green)
        #             FROM barrel_ledger),
        #             num_dark_ml = (SELECT SUM(change_dark)
        #             FROM barrel_ledger)
        #             """))


        for index, value in enumerate(num):
            potions_jsonb = json.dumps(potions[index])
            connection.execute(
                sqlalchemy.text(
                    """
                    UPDATE catalog
                    SET inventory = catalog.inventory + :num
                    WHERE catalog.potion_type = :potions
                    """),
                [{'num':value,'potions':potions_jsonb}])
            
        

    return "OK"


# Gets called 4 times a day
@router.post("/plan")
def get_bottle_plan():
    
    # Determine how many potions to make
    # Pull all the types of potions and how many we have of each. 
    # Order the list by which we have the least of, loop through bottling that way

    with db.engine.begin() as connection:
        
        inventory = connection.execute(sqlalchemy.text("""
                SELECT SUM(change_red) AS red,SUM(change_green) AS green,SUM(change_blue) AS blue,SUM(change_dark) AS dark
                FROM barrel_ledger""")).all()
        
        num_red_ml = inventory[0].red
        num_blue_ml = inventory[0].blue
        num_green_ml = inventory[0].green
        num_dark_ml = inventory[0].dark

        catalog = connection.execute(sqlalchemy.text("SELECT inventory,potion_type,id FROM catalog")).all()
        catalog = sorted(catalog, key=lambda item: item[0])

    
    bottle = []

    

    for item in catalog:
        quantity = 0
        potion_type = item[1]
        if num_red_ml >= potion_type[0] and num_green_ml >= potion_type[1] and \
            num_blue_ml >= potion_type[2] and num_dark_ml >= potion_type[3]:

            red = 1000
            green = 1000
            blue = 1000
            dark = 1000

            if potion_type[0] > 0:
                red = int(num_red_ml/potion_type[0])
            if potion_type[1] > 0:
                green = int(num_green_ml/potion_type[1])
            if potion_type[2] > 0:
                blue = int(num_blue_ml/potion_type[2])
            if potion_type[3] > 0:
                dark = int(num_dark_ml/potion_type[3])
            
            quantity = min([red,green,blue,dark])
            
            num_red_ml = num_red_ml-potion_type[0]*quantity
            num_green_ml = num_green_ml-potion_type[1]*quantity
            num_blue_ml = num_blue_ml-potion_type[2]*quantity
            num_dark_ml = num_dark_ml-potion_type[3]*quantity
            
            bottle.append({
                "potion_type": potion_type,
                "quantity": quantity
            })

    print(bottle)

    return bottle
