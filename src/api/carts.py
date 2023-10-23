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


@router.post("/")
def create_cart(new_cart: NewCart):
    """ """
    with db.engine.begin() as connection:
        cart_id = connection.execute(
            sqlalchemy.text(
                """
                INSERT INTO carts (customer_name)
                VALUES (:name)
                RETURNING id
                """),{'name':new_cart.customer}).scalar()

    print(cart_id)
    return {"cart_id": cart_id}


@router.get("/{cart_id}")
def get_cart(cart_id: int):
    """ """
    
    return cart_id


class CartItem(BaseModel):
    quantity: int


@router.post("/{cart_id}/items/{item_sku}")
def set_item_quantity(cart_id: int, item_sku: str, cart_item: CartItem):
    """ """
    #carts[cart_id].append({item_sku: cart_item.quantity})

    with db.engine.begin() as connection:
        connection.execute(
            sqlalchemy.text(
                """
                INSERT INTO cart_items (cart_id, quantity, catalog_id) 
                SELECT :cart_id, :quantity, catalog.id 
                FROM catalog WHERE catalog.sku = :item_sku  
                """),
                [{'cart_id':cart_id, 'item_sku':item_sku, 'quantity': cart_item.quantity}])

    return "OK"
    

class CartCheckout(BaseModel):
    payment: str

@router.post("/{cart_id}/checkout")
def checkout(cart_id: int, cart_checkout: CartCheckout):
    """ """
    
    # Create an account for the customer with their name and cart id
    # create transaction for their cart
    # update potion and gold ledgers corresponding
    # sum up to revise inventory

    with db.engine.begin() as connection:

        connection.execute(
                sqlalchemy.text(
                    """
                    UPDATE catalog
                    SET inventory = catalog.inventory - cart_items.quantity
                    FROM cart_items
                    WHERE catalog.id = cart_items.catalog_id and cart_items.cart_id = :cart_id
                    """),
                [{'cart_id':cart_id}])
        
        purchase = connection.execute(
            sqlalchemy.text(
                """SELECT *
                FROM cart_items
                WHERE cart_id = :cart_id"""),
                [{'cart_id':cart_id}]).all()
        
        
        gold = 0
        potions = 0

        for item in purchase:

            catalog_id = item.catalog_id
            quantity = item.quantity
            potions += quantity
            # Fetch the price of the catalog item
            price = connection.execute(
                sqlalchemy.text("""
                SELECT price
                FROM catalog
                WHERE id = :catalog_id
                """),
                {'catalog_id': catalog_id}).scalar()

            # Calculate the cost for this item and add it to the total cost
            item_cost = price * quantity
            gold += item_cost

        sql_to_execute = sqlalchemy.text("UPDATE global_inventory SET gold = gold+:money")
        connection.execute(sql_to_execute, parameters={'money': gold})

       

    return {"total_potions_bought": potions, "total_gold_paid": gold}

