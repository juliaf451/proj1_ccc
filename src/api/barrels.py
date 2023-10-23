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
        total = 0

        # Create transaction for barrels
        # Update ml and gold ledgers corresponding
        # Update inventory by summing ledger

        for barrel in barrels_delivered:
            potion = barrel.potion_type
            quantity = barrel.quantity
            total += quantity
            cost = cost + barrel.price*quantity

            if potion == [1,0,0,0]:
                red_ml=red_ml+barrel.ml_per_barrel*quantity
            elif potion == [0,1,0,0]:
                green_ml=green_ml+barrel.ml_per_barrel*quantity
            elif potion == [0,0,1,0]:
                blue_ml=blue_ml+barrel.ml_per_barrel*quantity
            elif potion == [0,0,0,1]:
                dark_ml=dark_ml+barrel.ml_per_barrel*quantity

    ml = red_ml + green_ml + blue_ml + dark_ml

    with db.engine.begin() as connection:

        # Add the transaction to the ledger
        transaction_id = connection.execute(
            sqlalchemy.text(
                """
                INSERT INTO transactions (description) 
                VALUES ('Delivery of :num barrels with :ml ml')
                RETURNING id
                """), ({'num':total, 'ml':ml}))

        # Update the gold ledger
        connection.execute(
            sqlalchemy.text(
                """
                INSERT INTO gold_ledger (change_gold,transaction_id) 
                VALUES (:cost,:transaction_id)
                """), ({'cost':-cost, 'transaction_id':transaction_id}))
        
        # Update the barrels ledger
        connection.execute(
            sqlalchemy.text(
                """
                INSERT INTO barrel_ledger 
                (transaction_id,change_red,change_green,change_blue,change_dark) 
                VALUES (:transaction_id,:red,:green,:blue,:dark)
                """), ({'transaction_id':transaction_id,'red':red_ml,'green':green_ml,'blue':blue_ml,'dark':dark_ml}))

        # Update our inventory by summing the ledger
        connection.execute(
                sqlalchemy.text(
                    """
                    UPDATE global_inventory
                    SET num_red_ml = (SELECT SUM(change_red)
                    FROM barrel_ledger),
                    num_blue_ml = (SELECT SUM(change_blue)
                    FROM barrel_ledger),
                    num_green_ml = (SELECT SUM(change_green)
                    FROM barrel_ledger),
                    num_dark_ml = (SELECT SUM(change_dark)
                    FROM barrel_ledger)
                    """))


        # connection.execute(
        #     sqlalchemy.text(
        #         """
        #         UPDATE global_inventory SET
        #         num_red_ml = num_red_ml + :red_ml,
        #         num_blue_ml = num_blue_ml + :blue_ml,
        #         num_green_ml = num_green_ml + :green_ml,
        #         num_dark_ml = num_dark_ml + :dark_ml,
        #         gold = gold - :cost
        #         """),
        #     [{'red_ml':red_ml,'green_ml':green_ml,'blue_ml':blue_ml,'dark_ml':dark_ml,'cost':cost}])

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

            if barrel.potion_type == [0,0,1,0] and gold >= cost and num_blue_ml < 800 and ml <= 500:
                purchase.append({ "sku": barrel.sku, "quantity": 1})
                num_blue_ml += ml
                gold = gold - cost
            elif barrel.potion_type == [0,1,0,0] and gold >= cost and num_green_ml < 800 and ml <= 500:
                purchase.append({ "sku": barrel.sku, "quantity": 1})
                num_green_ml += ml
                gold = gold - cost
            elif barrel.potion_type == [1,0,0,0] and gold >= cost and num_red_ml < 800 and ml <= 500:
                purchase.append({ "sku": barrel.sku, "quantity": 1})
                num_red_ml += ml
                gold = gold - cost
            elif barrel.potion_type == [0,0,0,1] and gold >= cost and num_dark_ml < 800 and ml <= 500:
                purchase.append({ "sku": barrel.sku, "quantity": 1})
                num_dark_ml += ml
                gold = gold - cost

    return purchase
