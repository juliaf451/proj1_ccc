from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
import sqlalchemy
from src import database as db
from src.api import auth




router = APIRouter(
    prefix="/carts",
    tags=["cart"],
    dependencies=[Depends(auth.get_api_key)],
)


class NewCart(BaseModel):
    customer: str

cart_id = 0
carts = {}

@router.post("/")
def create_cart(new_cart: NewCart):
    """ """
    cart_id += 1
    carts[cart_id] = 0
    return {"cart_id": cart_id}


@router.get("/{cart_id}")
def get_cart(cart_id: int):
    """ """
    cart_info = carts.get(cart_id, {})
    return cart_info


class CartItem(BaseModel):
    quantity: int


@router.post("/{cart_id}/items/{item_sku}")
def set_item_quantity(cart_id: int, item_sku: str, cart_item: CartItem):
    """ """
    carts[cart_id] = cart_item.quantity
    return "OK"
    

class CartCheckout(BaseModel):
    payment: str

@router.post("/{cart_id}/checkout")
def checkout(cart_id: int, cart_checkout: CartCheckout):
    """ """
    quantity = carts[cart_id]
    cost = quantity*50
    
    with db.engine.begin() as connection:
        sql_to_execute = sqlalchemy.text("UPDATE global_inventory SET gold = gold+:money")
        connection.execute(sql_to_execute, parameters={'money': cost})
        sql_to_execute = sqlalchemy.text("UPDATE global_inventory SET num_red_potions = num_red_potions-:num")
        connection.execute(sql_to_execute, parameters={'num': quantity})


    return {"total_potions_bought": quantity, "total_gold_paid": cost}



