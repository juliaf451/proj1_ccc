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
    #carts[cart_id].append({item_sku: cart_item.quantity})

    with db.engine.begin() as connection:
        connection.execute(
            sqlalchemy.text(
                """
                INSERT INTO carts (cart_id, quantity, catalog_id) 
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

    # update statmenets here * use update/select combo

    # print(carts[cart_id])
    # quantity = []
    # potions = []
    
    # # Loop through each dictionary in carts
    # for cart in carts[cart_id]:
    #     quantity.extend(cart.values())
    #     potions.extend(cart.keys())

    with db.engine.begin() as connection:

        connection.execute(
                sqlalchemy.text(
                    """
                    UPDATE catalog
                    SET inventory = catalog.inventory - carts.quantity
                    FROM carts
                    WHERE catalog.id = carts.catalog_id and carts.cart_id = :cart_id
                    """),
                [{'cart_id':cart_id}])
        
        purchase = connection.execute(
            sqlalchemy.text(
                """SELECT *
                FROM carts
                WHERE cart_id = :cart_id"""),
                [{'cart_id':cart_id}]).scalars().all()

        for item in purchase:
            catalog_id = item.catalog_id
            quantity = item.quantity

            # Fetch the price of the catalog item
            price = connection.execute(
                sqlacalchemy.text("""
                SELECT price
                FROM catalog
                WHERE id = :catalog_id
                """),
                {'catalog_id': catalog_id}
            ).scalar()

            # Calculate the cost for this item and add it to the total cost
            item_cost = price * quantity
            gold += item_cost



        # for i in range(0,len(quantity)):
            
        #     price = connection.execute(
        #         sqlalchemy.text(
        #             """
        #             SELECT price
        #             FROM catalog
        #             WHERE catalog.sku = :potions
        #             """),
        #         [{'potions':potions[i]}]).scalar_one()

        #     cost = quantity[i] * price
        #     total = total+cost 
        #     count = count+ quantity[i]
       
        #     connection.execute(
        #         sqlalchemy.text(
        #             """
        #             UPDATE catalog
        #             SET inventory = catalog.inventory - :num
        #             WHERE catalog.sku = :potions
        #             """),
        #         [{'num':quantity[i],'potions':potions[i]}])

        #     sql_to_execute = sqlalchemy.text("UPDATE global_inventory SET gold = gold+:money")
        #     connection.execute(sql_to_execute, parameters={'money': cost})


    return {"total_potions_bought": potions, "total_gold_paid": gold}



