from fastapi import APIRouter, Depends
from pydantic import BaseModel
from src.api import auth
import math
import sqlalchemy
from src import database as db

router = APIRouter(
    prefix="/audit",
    tags=["audit"],
    dependencies=[Depends(auth.get_api_key)],
)

@router.get("/inventory")
def get_inventory():
    """ """
    with db.engine.begin() as connection:
        gold = sum(connection.execute(sqlalchemy.text("SELECT change_gold FROM gold_ledger")).scalars().all())
        ml = sum(connection.execute(sqlalchemy.text("""
            SELECT change_red,change_green,change_blue,change_dark 
            FROM barrel_ledger""")).scalars().all())
        potions = sum(connection.execute(sqlalchemy.text("SELECT quantity_change FROM potion_ledger")).scalars().all())

    print({"number_of_potions": potions, "ml_in_barrels": ml, "gold": gold})
    return {"number_of_potions": potions, "ml_in_barrels": ml, "gold": gold}

class Result(BaseModel):
    gold_match: bool
    barrels_match: bool
    potions_match: bool

# Gets called once a day
@router.post("/results")
def post_audit_results(audit_explanation: Result):
    """ """
    print(audit_explanation)

    return "OK"
