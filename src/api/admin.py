from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
from src.api import auth
import sqlalchemy
from src import database as db

router = APIRouter(
    prefix="/admin",
    tags=["admin"],
    dependencies=[Depends(auth.get_api_key)],
)

@router.post("/reset")
def reset():
    """
    Reset the game state. Gold goes to 100, all potions are removed from
    inventory, and all barrels are removed from inventory. Carts are all reset.
    """
    # delete truncate
    with db.engine.begin() as connection:
        connection.execute(
            sqlalchemy.text(
                """
                UPDATE global_inventory SET
                num_red_ml = 0,
                num_blue_ml = 0,
                num_green_ml = 0,
                gold = 100
                """))
        connection.execute(sqlalchemy.text("UPDATE catalog SET inventory=0"))
        connection.execute(sqlalchemy.text("TRUNCATE carts"))
        connection.execute(sqlalchemy.text("TRUNCATE cart_items"))
        connection.execute(sqlalchemy.text("TRUNCATE transactions"))
        connection.execute(sqlalchemy.text("TRUNCATE accounts"))
        connection.execute(sqlalchemy.text("TRUNCATE barrel_ledger"))
        connection.execute(sqlalchemy.text("TRUNCATE gold_ledger"))
        connection.execute(sqlalchemy.text("TRUNCATE potion_ledger"))

        transaction_id = connection.execute(
            sqlalchemy.text(
                """
                INSERT INTO transactions (description) 
                VALUES ('Start with 100 gold')
                RETURNING id
                """)).scalar()
        
        # Update the gold ledger
        connection.execute(
            sqlalchemy.text(
                """
                INSERT INTO gold_ledger (change_gold,transaction_id) 
                VALUES (100,:transaction_id)
                """), ({'transaction_id':transaction_id}))


    return "OK"


@router.get("/shop_info/")
def get_shop_info():
    """ """

    # TODO: Change me!
    return {
        "shop_name": "Cal Poly Concoctions",
        "shop_owner": "Julia",
    }
