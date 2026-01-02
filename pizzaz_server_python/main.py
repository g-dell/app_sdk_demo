import os
import json
import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional

from dotenv import load_dotenv
load_dotenv()

import mcp.types as types
from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel, Field, ValidationError

from starlette.middleware.cors import CORSMiddleware

from .config_loader import load_vertical_profile

# -----------------------------
# MCP init (MUST be before decorators)
# -----------------------------
mcp = FastMCP("pizzaz")

# -----------------------------
# Vertical profile
# -----------------------------
try:
    VERTICAL_PROFILE = load_vertical_profile()
    print(f"Loaded vertical profile: {VERTICAL_PROFILE.name}")
except Exception as e:
    print(f"Error loading vertical profile: {e}")
    raise

# -----------------------------
# Database layer imports
# -----------------------------
from .context import RequestContext, request_context
from .database import (
    DB_CONN,
    Product,
    Variant,
    Cart,
    CartItem,
    Media,
    get_all_products,
    get_product,
    create_cart,
    get_cart,
    update_cart,
    get_cart_by_session,
    associate_cart_to_session
)

# -----------------------------
# Tool input models
# -----------------------------
class SearchProductsInput(BaseModel):
    query: Optional[str] = Field(None, description="Termine di ricerca per i prodotti.")
    category_id: Optional[uuid.UUID] = Field(None, description="ID categoria per filtrare.")
    collection_id: Optional[uuid.UUID] = Field(None, description="ID collezione per filtrare.")
    min_price: Optional[float] = Field(None, description="Prezzo minimo.")
    max_price: Optional[float] = Field(None, description="Prezzo massimo.")
    sort_by: Optional[str] = Field(None, description="Ordinamento (es. 'price_asc', 'name_desc').")
    limit: int = Field(10, description="Max risultati.", ge=1, le=100)
    offset: int = Field(0, description="Offset paginazione.", ge=0)

class GetProductDetailsInput(BaseModel):
    product_id: uuid.UUID = Field(..., description="ID del prodotto.")

class AddToCartInput(BaseModel):
    product_id: uuid.UUID = Field(..., description="ID del prodotto da aggiungere.")
    variant_id: Optional[uuid.UUID] = Field(None, description="ID variante (se applicabile).")
    quantity: int = Field(1, description="Quantità.", ge=1)
    cart_id: Optional[uuid.UUID] = Field(None, description="Opzionale se in sessione.")

class UpdateCartItemInput(BaseModel):
    product_id: uuid.UUID = Field(..., description="ID prodotto nel carrello.")
    variant_id: Optional[uuid.UUID] = Field(None, description="ID variante nel carrello (se applicabile).")
    quantity: int = Field(..., description="Nuova quantità (0 = rimuovi).", ge=0)
    cart_id: Optional[uuid.UUID] = Field(None, description="Opzionale se in sessione.")

class RemoveFromCartInput(BaseModel):
    product_id: uuid.UUID = Field(..., description="ID prodotto da rimuovere.")
    variant_id: Optional[uuid.UUID] = Field(None, description="ID variante da rimuovere (se applicabile).")
    cart_id: Optional[uuid.UUID] = Field(None, description="Opzionale se in sessione.")

class ViewCartInput(BaseModel):
    cart_id: Optional[uuid.UUID] = Field(None, description="Opzionale se in sessione.")

# -----------------------------
# Helpers
# -----------------------------
def _schema(model: type[BaseModel]) -> Dict[str, Any]:
    return model.model_json_schema()

def _json_content(payload: Any):
    # Convertiamo in JSON serializzabile
    return types.StructuredContent(
        type="application/json",
        json=json.loads(json.dumps(payload, default=str))
    )

def _text_content(text: str) -> types.TextContent:
    return types.TextContent(type="text", text=text)

def _ok(result_json: Any, output_template: Optional[str] = None) -> types.ServerResult:
    meta = {}
    if output_template:
        meta["openai/outputTemplate"] = output_template

    return types.ServerResult(
        types.CallToolResult(
            content=[_json_content(result_json)],
            _meta=meta,
            isError=False,
        )
    )

def _err(message: str) -> types.ServerResult:
    return types.ServerResult(
        types.CallToolResult(
            content=[_text_content(message)],
            isError=True,
        )
    )

# -----------------------------
# MCP: list tools/resources/templates
# -----------------------------
@mcp._mcp_server.list_tools()
async def _list_tools() -> List[types.Tool]:
    return [
        types.Tool(
            name="search_products",
            description="Cerca prodotti nel catalogo.",
            inputSchema=_schema(SearchProductsInput),
        ),
        types.Tool(
            name="get_product_details",
            description="Ottieni i dettagli di un prodotto specifico.",
            inputSchema=_schema(GetProductDetailsInput),
        ),
        types.Tool(
            name="add_to_cart",
            description="Aggiungi un prodotto al carrello.",
            inputSchema=_schema(AddToCartInput),
        ),
        types.Tool(
            name="view_cart",
            description="Visualizza il contenuto del carrello.",
            inputSchema=_schema(ViewCartInput),
        ),
        types.Tool(
            name="update_cart_item",
            description="Aggiorna la quantità di un articolo nel carrello.",
            inputSchema=_schema(UpdateCartItemInput),
        ),
        types.Tool(
            name="remove_from_cart",
            description="Rimuovi un articolo dal carrello.",
            inputSchema=_schema(RemoveFromCartInput),
        ),
    ]

@mcp._mcp_server.list_resources()
async def _list_resources() -> List[types.Resource]:
    return []

@mcp._mcp_server.list_resource_templates()
async def _list_resource_templates() -> List[types.ResourceTemplate]:
    return []

async def _handle_read_resource(req: types.ReadResourceRequest) -> types.ServerResult:
    return types.ServerResult(
        types.ReadResourceResult(
            contents=[],
            _meta={"error": f"Unknown resource: {req.params.uri}"},
        )
    )

# -----------------------------
# Tool implementations
# -----------------------------
async def _call_search_products(req: types.CallToolRequest) -> types.ServerResult:
    try:
        _ = SearchProductsInput.model_validate(req.params.arguments or {})

        # Al momento: uso get_all_products() (puoi evolverlo con filtri/ricerca)
        products = get_all_products()

        # Se Product è pydantic, .model_dump() funziona
        products_json = [p.model_dump() for p in products]

        # Output template testuale semplice (puoi sostituirlo con ui://... più avanti)
        out = "Ho trovato i seguenti prodotti:\n"
        if products:
            for p in products:
                out += f"- {p.name} (Prezzo: {getattr(p, 'base_price', 'N/A')})\n"
        else:
            out += "Nessun prodotto trovato."

        return _ok(products_json, output_template=out)

    except ValidationError as e:
        return _err(f"Invalid input for search_products: {e}")

    except Exception as e:
        return _err(f"search_products failed: {e}")

async def _call_get_product_details(req: types.CallToolRequest) -> types.ServerResult:
    try:
        input_data = GetProductDetailsInput.model_validate(req.params.arguments or {})
        product = get_product(input_data.product_id)

        if not product:
            return _err(f"Product with ID {input_data.product_id} not found.")

        product_json = product.model_dump()

        # Se nel vertical profile hai un template stringa, lo puoi usare come testo.
        # Per ora: testo semplice (evitiamo format complessi che rompono)
        out = f"{product.name}\n{getattr(product, 'description', '')}".strip()

        return _ok(product_json, output_template=out)

    except ValidationError as e:
        return _err(f"Invalid input for get_product_details: {e}")

    except Exception as e:
        return _err(f"get_product_details failed: {e}")

def _resolve_cart(input_cart_id: Optional[uuid.UUID]) -> Optional[Cart]:
    """Helper to resolve cart from ID OR session context."""
    if input_cart_id:
        return get_cart(input_cart_id)
    
    # Check session context
    ctx = request_context.get()
    if ctx and ctx.widgetSessionId:
        return get_cart_by_session(ctx.widgetSessionId)
    
    return None

def _ensure_cart(input_cart_id: Optional[uuid.UUID]) -> Cart:
    """Gets existing cart or creates a new one linked to session."""
    cart = _resolve_cart(input_cart_id)
    if cart:
        return cart
        
    # Create new
    cart_id = uuid.uuid4()
    # Default currency from profile
    currency = getattr(VERTICAL_PROFILE, "currency", "EUR")
    
    new_cart = Cart(
        id=cart_id,
        items=[],
        subtotal=0.0,
        discount=0.0,
        total=0.0,
        currency=currency,
        last_updated_at=datetime.now().isoformat()
    )
    
    created = create_cart(new_cart)
    
    # Link to session if available
    ctx = request_context.get()
    if ctx and ctx.widgetSessionId:
        associate_cart_to_session(ctx.widgetSessionId, cart_id)
        
    return created

async def _call_add_to_cart(req: types.CallToolRequest) -> types.ServerResult:
    try:
        input_data = AddToCartInput.model_validate(req.params.arguments or {})
        
        # Get or create cart
        cart = _ensure_cart(input_data.cart_id)

        # TODO: qui dovresti leggere il prezzo reale dal DB (product/variant)
        unit_price = 10.0

        # Check if item exists
        found = None
        for item in cart.items:
            if item.product_id == input_data.product_id and item.variant_id == input_data.variant_id:
                found = item
                break
        
        if found:
            found.quantity += input_data.quantity
        else:
            cart.items.append(
                CartItem(
                    product_id=input_data.product_id,
                    variant_id=input_data.variant_id,
                    quantity=input_data.quantity,
                    unit_price=unit_price,
                )
            )

        # Recalculate
        cart.subtotal = sum(i.quantity * i.unit_price for i in cart.items)
        discount = getattr(cart, "discount", 0.0)
        cart.total = cart.subtotal - discount
        cart.last_updated_at = datetime.now().isoformat()
        
        updated = update_cart(cart.id, cart)
        created_json = updated.model_dump()

        out = f"Il prodotto è stato aggiunto al carrello. Totale articoli: {len(updated.items)}"
        return _ok(created_json, output_template=out)

    except ValidationError as e:
        return _err(f"Invalid input for add_to_cart: {e}")

    except Exception as e:
        return _err(f"add_to_cart failed: {e}")

async def _call_view_cart(req: types.CallToolRequest) -> types.ServerResult:
    try:
        input_data = ViewCartInput.model_validate(req.params.arguments or {})
        
        cart = _resolve_cart(input_data.cart_id)

        if not cart:
            if input_data.cart_id:
                return _err(f"Cart with ID {input_data.cart_id} not found.")
            else:
                 return _err("Nessun carrello attivo per questa sessione.")

        cart_json = cart.model_dump()

        out = f"Il tuo carrello (ID: {cart.id}) contiene {len(cart.items)} articoli. Totale: {cart.total} {getattr(cart, 'currency', 'EUR')}"
        return _ok(cart_json, output_template=out)

    except ValidationError as e:
        return _err(f"Invalid input for view_cart: {e}")

    except Exception as e:
        return _err(f"view_cart failed: {e}")

async def _call_update_cart_item(req: types.CallToolRequest) -> types.ServerResult:
    try:
        input_data = UpdateCartItemInput.model_validate(req.params.arguments or {})
        cart = _resolve_cart(input_data.cart_id)
        if not cart:
            return _err(f"Cart not found.")

        # trova item
        found = None
        for item in cart.items:
            if item.product_id == input_data.product_id and item.variant_id == input_data.variant_id:
                found = item
                break

        if not found:
            return _err("Item not found in cart.")

        if input_data.quantity == 0:
            cart.items.remove(found)
        else:
            found.quantity = input_data.quantity

        # ricalcolo totali
        cart.subtotal = sum(i.quantity * i.unit_price for i in cart.items)
        # sconto se esiste
        discount = getattr(cart, "discount", 0.0)
        cart.total = cart.subtotal - discount
        cart.last_updated_at = datetime.now().isoformat()

        updated = update_cart(cart.id, cart)
        updated_json = updated.model_dump()

        out = "Carrello aggiornato."
        return _ok(updated_json, output_template=out)

    except ValidationError as e:
        return _err(f"Invalid input for update_cart_item: {e}")

    except Exception as e:
        return _err(f"update_cart_item failed: {e}")

async def _call_remove_from_cart(req: types.CallToolRequest) -> types.ServerResult:
    try:
        input_data = RemoveFromCartInput.model_validate(req.params.arguments or {})
        cart = _resolve_cart(input_data.cart_id)
        if not cart:
            return _err(f"Cart not found.")

        before = len(cart.items)
        cart.items = [
            i for i in cart.items
            if not (
                i.product_id == input_data.product_id and
                (input_data.variant_id is None or i.variant_id == input_data.variant_id)
            )
        ]

        if len(cart.items) == before:
            return _err("Item not found in cart.")

        cart.subtotal = sum(i.quantity * i.unit_price for i in cart.items)
        discount = getattr(cart, "discount", 0.0)
        cart.total = cart.subtotal - discount
        cart.last_updated_at = datetime.now().isoformat()

        updated = update_cart(cart.id, cart)
        updated_json = updated.model_dump()

        return _ok(updated_json, output_template="Articolo rimosso dal carrello.")

    except ValidationError as e:
        return _err(f"Invalid input for remove_from_cart: {e}")

    except Exception as e:
        return _err(f"remove_from_cart failed: {e}")

# -----------------------------
# Single router for CallToolRequest
# -----------------------------
async def _call_tool_request(req: types.CallToolRequest) -> types.ServerResult:
    name = req.params.name
    if name == "search_products":
        return await _call_search_products(req)
    if name == "get_product_details":
        return await _call_get_product_details(req)
    if name == "add_to_cart":
        return await _call_add_to_cart(req)
    if name == "view_cart":
        return await _call_view_cart(req)
    if name == "update_cart_item":
        return await _call_update_cart_item(req)
    if name == "remove_from_cart":
        return await _call_remove_from_cart(req)

    return _err(f"Unknown tool: {name}")

mcp._mcp_server.request_handlers[types.CallToolRequest] = _call_tool_request
mcp._mcp_server.request_handlers[types.ReadResourceRequest] = _handle_read_resource

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.middleware.trustedhost import TrustedHostMiddleware

# -----------------------------
# ASGI app (Streamable HTTP)
# -----------------------------
app = mcp.streamable_http_app()

# Fix for "Invalid Host header" / 421 error on Render
app.add_middleware(TrustedHostMiddleware, allowed_hosts=["*"])

class RequestContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Extract session ID from headers (simulating OpenAI or Client passing it)
        # We look for 'X-Widget-Session' or 'X-Session-ID'
        session_id = request.headers.get("X-Widget-Session") or request.headers.get("X-Session-ID")
        
        # We also generate a request ID
        req_id = str(uuid.uuid4())
        
        # Create context
        ctx = RequestContext(requestId=req_id, widgetSessionId=session_id)
        token = request_context.set(ctx)
        
        try:
            response = await call_next(request)
            return response
        finally:
            request_context.reset(token)

app.add_middleware(RequestContextMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=False,
)

from starlette.staticfiles import StaticFiles

# ... existing middleware ...

# Mount static files
# Static files mount removed as dataset is now on Mother Duck
# static_dir = os.path.join(os.getcwd(), "archive", "Clothes_Dataset")
# if os.path.exists(static_dir):
#     app.mount("/static/images", StaticFiles(directory=static_dir), name="images")
#     print(f"Serving static images from {static_dir} at /static/images")
# else:
#     print(f"Warning: Static directory {static_dir} not found.")

# -----------------------------
# Local run
# -----------------------------
if __name__ == "__main__":
    import uvicorn

    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run("pizzaz_server_python.main:app", host=host, port=port, reload=True)
