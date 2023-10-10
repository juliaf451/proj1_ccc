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
    global cart_id
    cart_id += 1
    carts[cart_id] = []
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
    carts[cart_id].append({item_sku: cart_item.quantity})
    return "OK"
    

class CartCheckout(BaseModel):
    payment: str

@router.post("/{cart_id}/checkout")
def checkout(cart_id: int, cart_checkout: CartCheckout):
    """ """
    print(carts[cart_id])
    quantity = []
    potions = []
    
    # Loop through each dictionary in carts
    for cart in carts[cart_id]:
        quantity.extend(cart.values())
        potions.extend(cart.keys())

    # how do we translate the item sku to the correct potion (if its a string)
    with db.engine.begin() as connection:
        total = 0
        count = 0
        for i in range(0,len(quantity)):
            
            cost = quantity[i] * 50
            total = total+cost 
            count = count+ quantity[i]
            
            if potions[i] == "RED_POTION_0":
                sql_to_execute = sqlalchemy.text("UPDATE global_inventory SET num_red_potions = num_red_potions-:num")
                connection.execute(sql_to_execute, parameters={'num': quantity[i]})

            elif potions[i] == "GREEN_POTION_0":
                sql_to_execute = sqlalchemy.text("UPDATE global_inventory SET num_green_potions = num_green_potions-:num")
                connection.execute(sql_to_execute, parameters={'num': quantity[i]})
            elif potions[i] == "BLUE_POTION_0":
                sql_to_execute = sqlalchemy.text("UPDATE global_inventory SET num_blue_potions = num_blue_potions-:num")
                connection.execute(sql_to_execute, parameters={'num': quantity[i]})

            sql_to_execute = sqlalchemy.text("UPDATE global_inventory SET gold = gold+:money")
            connection.execute(sql_to_execute, parameters={'money': cost})


    return {"total_potions_bought": count, "total_gold_paid": total}



