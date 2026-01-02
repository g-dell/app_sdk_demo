import os
import uuid
import json
import duckdb
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from dotenv import load_dotenv

load_dotenv()

# --- Connection ---
def get_db_connection():
    token = os.environ.get("motherduck_token")
    if token:
        try:
            print("Connecting to MotherDuck...")
            # Assicuriamoci che il nome del DB sia quello corretto
            conn = duckdb.connect(f"md:mcp_app_ChatGPT?motherduck_token={token}") 
            return conn
        except Exception as e:
            print(f"⚠️  MotherDuck connection failed: {e}")
            print("   -> Fallback to in-memory DuckDB.")
    
    print("Connecting to in-memory DuckDB...")
    conn = duckdb.connect(database=":memory:", read_only=False)
    return conn

DB_CONN = get_db_connection()

# --- Models ---
class Media(BaseModel):
    url: str
    alt_text: Optional[str] = None
    type: Optional[str] = "image"

class Variant(BaseModel):
    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    product_id: uuid.UUID
    sku: str
    price_adjustment: float = 0.0
    inventory_quantity: int
    media: Optional[List[Media]] = None
    attributes: Dict[str, Any] = Field(default_factory=dict)

class Product(BaseModel):
    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    name: str
    description: Optional[str] = None
    slug: str
    category_id: Optional[uuid.UUID] = None
    collection_ids: Optional[List[uuid.UUID]] = None
    brand: Optional[str] = None
    media: Optional[List[Media]] = None
    base_price: float
    currency: str = "EUR"
    attributes: Dict[str, Any] = Field(default_factory=dict)
    variants: Optional[List[Variant]] = None

class Category(BaseModel):
    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    name: str
    slug: str
    description: Optional[str] = None
    parent_id: Optional[uuid.UUID] = None

class Collection(BaseModel):
    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    name: str
    slug: str
    description: Optional[str] = None

class CartItem(BaseModel):
    product_id: uuid.UUID
    variant_id: Optional[uuid.UUID] = None
    quantity: int
    unit_price: float

class Cart(BaseModel):
    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    user_id: Optional[uuid.UUID] = None
    items: List[CartItem] = Field(default_factory=list)
    subtotal: float = 0.0
    discount: float = 0.0
    total: float = 0.0
    currency: str = "EUR"
    last_updated_at: str

# --- CRUD Operations (Adapted for New Schema) ---

def get_all_products() -> List[Product]:
    """Retrieve all products joining with attributes and variants."""
    cursor = DB_CONN.cursor()
    # Fetch base products
    # Schema: product_id, name, description, base_price
    rows = cursor.execute("SELECT product_id, name, description, base_price FROM products").fetchall()
    
    products = []
    for row in rows:
        p_id, name, desc, price = row
        
        # Fetch attributes
        attr_rows = cursor.execute("SELECT key, value FROM product_attributes WHERE product_id = ?", [p_id]).fetchall()
        attributes = {k: v for k, v in attr_rows}
        
        # Fetch variants
        # Schema: sku, product_id, inventory_quantity
        var_rows = cursor.execute("SELECT sku, inventory_quantity FROM variants WHERE product_id = ?", [p_id]).fetchall()
        variants = []
        for v_row in var_rows:
            sku, qty = v_row
            # Fetch variant attributes
            v_attr_rows = cursor.execute("SELECT key, value FROM variant_attributes WHERE sku = ?", [sku]).fetchall()
            v_attrs = {k: v for k, v in v_attr_rows}
            
            variants.append(Variant(
                id=uuid.uuid5(uuid.NAMESPACE_DNS, sku), # Deterministic ID from SKU
                product_id=uuid.UUID(p_id),
                sku=sku,
                inventory_quantity=qty,
                attributes=v_attrs,
                media=[] # Not in DB schema implies empty
            ))
            
    # Fetch images
        # Schema assumption: product_id, url, alt_text
        try:
            img_rows = cursor.execute("SELECT url, alt_text FROM images WHERE product_id = ?", [p_id]).fetchall()
            media_items = [Media(url=row[0], alt_text=row[1], type="image") for row in img_rows]
        except Exception as e:
            # Fallback if table doesn't exist or error
            print(f"Warning: Failed to fetch images for product {p_id}: {e}")
            media_items = []

        products.append(Product(
            id=uuid.UUID(p_id),
            name=name,
            description=desc,
            slug=name.lower().replace(" ", "-"), # Generate slug on fly
            base_price=price,
            attributes=attributes,
            variants=variants,
            media=media_items, 
            category_id=None, # Not in DB schema
            collection_ids=[]
        ))
    
    return products

def get_product(product_id: uuid.UUID) -> Optional[Product]:
    # Simplified implementation calling get_all_products and filtering. 
    # In prod, should be a specific query.
    all_prods = get_all_products()
    for p in all_prods:
        if p.id == product_id:
            return p
    return None

def create_cart(cart: Cart) -> Cart:
    """Creates a new cart and saves it to the database."""
    cursor = DB_CONN.cursor()
    # Save cart main info
    cursor.execute(
        "INSERT INTO carts (id, user_id, subtotal, discount, total, currency, last_updated_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
        [str(cart.id), str(cart.user_id) if cart.user_id else None, cart.subtotal, cart.discount, cart.total, cart.currency, cart.last_updated_at]
    )
    # Save items
    for item in cart.items:
        cursor.execute(
            "INSERT INTO cart_items (product_id, variant_id, quantity, unit_price, cart_id) VALUES (?, ?, ?, ?, ?)",
            [str(item.product_id), str(item.variant_id) if item.variant_id else None, item.quantity, item.unit_price, str(cart.id)]
        )
    return cart

def get_cart(cart_id: uuid.UUID) -> Optional[Cart]:
    """Retrieves a cart by ID."""
    cursor = DB_CONN.cursor()
    row = cursor.execute("SELECT id, user_id, subtotal, discount, total, currency, last_updated_at FROM carts WHERE id = ?", [str(cart_id)]).fetchone()
    if not row:
        return None
    
    cid, uid, sub, disc, tot, curr, last_up = row
    
    # Fetch items
    items_rows = cursor.execute("SELECT product_id, variant_id, quantity, unit_price FROM cart_items WHERE cart_id = ?", [str(cid)]).fetchall()
    items = []
    for i_row in items_rows:
        pid, vid, qty, price = i_row
        items.append(CartItem(
            product_id=uuid.UUID(pid),
            variant_id=uuid.UUID(vid) if vid else None,
            quantity=qty,
            unit_price=price
        ))
        
    return Cart(
        id=uuid.UUID(cid),
        user_id=uuid.UUID(uid) if uid else None,
        subtotal=sub,
        discount=disc,
        total=tot,
        currency=curr,
        last_updated_at=last_up,
        items=items
    )

def update_cart(cart_id: uuid.UUID, cart: Cart) -> Cart:
    """Updates an existing cart."""
    cursor = DB_CONN.cursor()
    # Delete old items (simple strategy)
    cursor.execute("DELETE FROM cart_items WHERE cart_id = ?", [str(cart_id)])
    cursor.execute("DELETE FROM carts WHERE id = ?", [str(cart_id)])
    
    # Re-insert
    return create_cart(cart)

def get_cart_by_session(session_id: str) -> Optional[Cart]:
    """Finds the cart associated with a session ID."""
    cursor = DB_CONN.cursor()
    row = cursor.execute("SELECT cart_id FROM user_sessions WHERE session_id = ?", [session_id]).fetchone()
    if row:
        return get_cart(uuid.UUID(row[0]))
    return None

def associate_cart_to_session(session_id: str, cart_id: uuid.UUID):
    """Links a cart to a session ID."""
    cursor = DB_CONN.cursor()
    # Upsert logic (simplificata: delete + insert)
    cursor.execute("DELETE FROM user_sessions WHERE session_id = ?", [session_id])
    cursor.execute("INSERT INTO user_sessions (session_id, cart_id, created_at) VALUES (?, ?, ?)", 
                   [session_id, str(cart_id), "now"])

# Needed for seed_data.py compatibility if we keep it
def create_product(product: Product) -> Product:
    # Not implemented for new schema in this helper, 
    # but defined to avoid ImportErrors if seed_data still imports it.
    pass

def create_category(category: Category) -> Category:
    pass

def create_collection(collection: Collection) -> Collection:
    pass

def create_variant(variant: Variant) -> Variant:
    pass
