from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
import sqlalchemy
from src import database as db
from src.api import auth
from enum import Enum




router = APIRouter(
    prefix="/carts",
    tags=["cart"],
    dependencies=[Depends(auth.get_api_key)],
)


class search_sort_options(str, Enum):
    customer_name = "customer_name"
    item_sku = "item_sku"
    line_item_total = "line_item_total"
    timestamp = "timestamp"

class search_sort_order(str, Enum):
    asc = "asc"
    desc = "desc"   

@router.get("/search/", tags=["search"])
def search_orders(
    customer_name: str = "",
    potion_sku: str = "",
    search_page: str = "",
    sort_col: search_sort_options = search_sort_options.timestamp,
    sort_order: search_sort_order = search_sort_order.desc,
):
    
    limit = 5
    offset = 0
    order_by="catalog.id"

    # if sort_col is search_sort_options.customer_name:
    #     order_by = db.carts.customer_name
    # elif sort_col is search_sort_options.item_sku:
    #     order_by = db.catalog.sku
    # elif sort_col is search_sort_options.timestamp:
    #     order_by = sqlalchemy.desc(db.cart_items.timestamp)
    # else:
    #     assert False

    


    with db.engine.connect() as connection:

        result = connection.execute(
            sqlalchemy.text(
                """
                SELECT carts.id AS cart_id, carts.customer_name AS name, carts.created_at AS time, 
                    cart_items.catalog_id AS item_id, cart_items.quantity AS quantity,
                    catalog.sku AS sku, catalog.price AS price
                FROM carts
                JOIN cart_items ON cart_items.cart_id = carts.id
                JOIN catalog ON catalog.id = cart_items.catalog_id
                WHERE carts.customer_name ILIKE :name
                ORDER BY carts.customer_name
                LIMIT :limit OFFSET :offset
                """
            ),({'name':f"%{customer_name}%", 'limit':limit, 'offset':offset})
            ).all()


        # stmt = (
        #     sqlalchemy.select(
        #         db.carts.cart_id,
        #         db.carts.customer_name,
        #         db.carts.timestamp,
        #         db.cart_items.catalog_id,
        #         db.cart_items.quantity,
        #         db.catalog.item_sku,
        #         db.catalog.price,
        #     )
        #     .limit(limit)
        #     .offset(offset)
        #     .order_by(order_by, db.timestamp)
        #     )

    
        # # filter only if name parameter is passed
        # if customer_name != "":
        #     stmt = stmt.where(db.carts.customer_name.ilike(f"%{customer_name}%"))


        #result = connection.execute(stmt)
        results = []

        for row in result:
            results.append({
                    "line_item_id": row.item_id,
                    "item_sku": f"{row.quantity} {row.sku} POTION",
                    "customer_name": row.name,
                    "line_item_total": row.quantity*row.price,
                    "timestamp": row.time,
                })
    
    json = {"previous": "", "next": "","results": results}



    """
    Search for cart line items by customer name and/or potion sku.

    Customer name and potion sku filter to orders that contain the 
    string (case insensitive). If the filters aren't provided, no
    filtering occurs on the respective search term.

    Search page is a cursor for pagination. The response to this
    search endpoint will return previous or next if there is a
    previous or next page of results available. The token passed
    in that search response can be passed in the next search request
    as search page to get that page of results.

    Sort col is which column to sort by and sort order is the direction
    of the search. They default to searching by timestamp of the order
    in descending order.

    The response itself contains a previous and next page token (if
    such pages exist) and the results as an array of line items. Each
    line item contains the line item id (must be unique), item sku, 
    customer name, line item total (in gold), and timestamp of the order.
    Your results must be paginated, the max results you can return at any
    time is 5 total line items.
    """

    return json



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
   

    with db.engine.begin() as connection:

        customer_name = connection.execute(
            sqlalchemy.text(
                """
                SELECT customer_name FROM carts 
                WHERE :cart_id = carts.id
                """),({'cart_id':cart_id})).scalar()
        


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


        # Create an account for the customer with their name and cart id

        account_id = connection.execute(
            sqlalchemy.text(
                """
                INSERT INTO accounts (holders_name,cart_id) 
                VALUES (:name,:cart_id)
                RETURNING id
                """), ({'name':customer_name, 'cart_id':cart_id})).scalar()

        # Add the transaction to the ledger
        transaction_id = connection.execute(
            sqlalchemy.text(
                """
                INSERT INTO transactions (description) 
                VALUES (:customer || ' is buying :num potions for :cost gold')
                RETURNING id
                """), ({'customer':customer_name,'num':potions,'cost':gold})).scalar()

        # Update the potions ledger - one row per potion type
        for item in purchase:
            connection.execute(
                sqlalchemy.text(
                    """
                    INSERT INTO potion_ledger (transaction_id,account_id,potion_id,quantity_change) 
                    VALUES (:transaction_id, :account,:potion_id,:quantity)
                    """), ({'transaction_id':transaction_id, 'account':account_id,'potion_id':item.catalog_id,'quantity':-item.quantity}))

        # Update the gold ledger
        connection.execute(
            sqlalchemy.text(
                """
                INSERT INTO gold_ledger (change_gold,transaction_id,account_id) 
                VALUES (:cost,:transaction_id,:account_id)
                """), ({'cost':gold, 'transaction_id':transaction_id,'account_id':account_id}))


        
        # sum up to revise inventory
            
            
        #sql_to_execute = sqlalchemy.text("UPDATE global_inventory SET gold = gold+:money")
        #connection.execute(sql_to_execute, parameters={'money': gold})

       

    return {"total_potions_bought": potions, "total_gold_paid": gold}

