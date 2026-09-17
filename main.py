from fastapi import FastAPI, Query, Header, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from typing import Optional, List

app = FastAPI(title="FOSTERS AI Tools")

API_TOKEN = "fosters_bot_2026"


# -----------------------------------------------------------------------------
# HOME DASHBOARD
# -----------------------------------------------------------------------------

@app.get("/", response_class=HTMLResponse)
def root():
    return """
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>FOSTERS AI Tools</title>
        <style>
            * { box-sizing: border-box; margin: 0; padding: 0; }
            body {
                background: #0a0a0a;
                color: #f5f5f0;
                font-family: Arial, Helvetica, sans-serif;
                min-height: 100vh;
            }
            .container { width: 90%; max-width: 1100px; margin: auto; padding: 70px 0; }
            .header { margin-bottom: 50px; }
            .brand {
                font-family: Georgia, 'Times New Roman', serif;
                font-size: 42px;
                letter-spacing: 8px;
                margin-bottom: 10px;
            }
            .subtitle {
                color: #888;
                font-size: 14px;
                letter-spacing: 2px;
                text-transform: uppercase;
            }
            .status {
                display: inline-flex;
                align-items: center;
                gap: 8px;
                margin-top: 24px;
                padding: 9px 14px;
                border: 1px solid #2d2d2d;
                border-radius: 999px;
                font-size: 13px;
                color: #bbb;
            }
            .dot { width: 8px; height: 8px; background: #5ad66f; border-radius: 50%; }
            .section-title {
                margin-bottom: 20px;
                font-size: 13px;
                color: #777;
                letter-spacing: 2px;
                text-transform: uppercase;
            }
            .grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
                gap: 15px;
            }
            .card {
                background: #111;
                border: 1px solid #222;
                border-radius: 14px;
                padding: 24px;
                transition: 0.2s ease;
            }
            .card:hover { transform: translateY(-3px); border-color: #3a3a3a; }
            .card h3 { font-size: 17px; margin-bottom: 9px; font-weight: 500; }
            .endpoint {
                display: inline-block;
                margin-bottom: 12px;
                color: #888;
                font-family: monospace;
                font-size: 13px;
            }
            .card p { color: #aaa; line-height: 1.6; font-size: 14px; }
            .footer {
                margin-top: 50px;
                padding-top: 25px;
                border-top: 1px solid #1f1f1f;
                display: flex;
                justify-content: space-between;
                align-items: center;
                flex-wrap: wrap;
                gap: 15px;
                color: #666;
                font-size: 12px;
            }
            .docs {
                color: #ddd;
                text-decoration: none;
                border: 1px solid #333;
                padding: 10px 15px;
                border-radius: 8px;
            }
            .docs:hover { background: #181818; }
            @media (max-width: 600px) {
                .brand { font-size: 30px; letter-spacing: 5px; }
                .container { padding: 40px 0; }
            }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <div class="brand">FOSTERS</div>
                <div class="subtitle">AI Tools Infrastructure</div>
                <div class="status"><span class="dot"></span>System operational</div>
            </div>

            <div class="section-title">Active Skills & Integrations</div>
            <div class="grid">
                <div class="card">
                    <h3>Size Recommendation</h3>
                    <span class="endpoint">GET /recommend-size</span>
                    <p>Recommends the ideal Fosters size based on the customer's height and weight.</p>
                </div>
                <div class="card">
                    <h3>Order Preparation</h3>
                    <span class="endpoint">POST /prepare-order</span>
                    <p>Structures product, color, size and quantity before starting the shipping process.</p>
                </div>
                <div class="card">
                    <h3>Shipping Preparation</h3>
                    <span class="endpoint">POST /prepare-shipping</span>
                    <p>Determines the correct shipping flow for Santa Cruz and other departments.</p>
                </div>
                <div class="card">
                    <h3>Product Catalog</h3>
                    <span class="endpoint">GET /catalog</span>
                    <p>Returns the currently available Henley colors and their product images.</p>
                </div>
                <div class="card">
                    <h3>Pancake Product Sync</h3>
                    <span class="endpoint">GET /products</span>
                    <p>Provides Fosters products and variations in the structure expected by Pancake.</p>
                </div>
                <div class="card">
                    <h3>Discount Engine</h3>
                    <span class="endpoint">GET /discount</span>
                    <p>Returns official quantity discounts only when requested explicitly by the customer.</p>
                </div>
                <div class="card">
                    <h3>Lead Classification</h3>
                    <span class="endpoint">POST /classify-lead</span>
                    <p>Classifies commercial intent and determines when human handoff is required.</p>
                </div>
                <div class="card">
                    <h3>Next Action Decision</h3>
                    <span class="endpoint">POST /decide-next-action</span>
                    <p>Chooses the next commercial action using deterministic priorities for sales and handoff.</p>
                </div>
            </div>

            <div class="footer">
                <span>FOSTERS · Santa Cruz, Bolivia</span>
                <a class="docs" href="/docs">API Documentation</a>
            </div>
        </div>
    </body>
    </html>
    """


# -----------------------------------------------------------------------------
# SHARED PRODUCT DATA
# -----------------------------------------------------------------------------

FOSTERS_PRICE_BS = 300
FOSTERS_COST_BS = 110

FOSTERS_CATALOG = {
    "negro": {
        "name": "Negro",
        "image_url": "https://content.pancake.vn/user-content2.botcake.vn/2026/9/9/ae053b22c7ea2916219184518d0e10a1942790d1.png",
        "sizes": ["M", "L", "XL"],
    },
    "azul": {
        "name": "Azul",
        "image_url": "https://content.pancake.vn/user-content2.botcake.vn/2026/9/9/0a3d94035bd27b49047864197f5c3724017ac0fe.png",
        "sizes": ["M", "L", "XL", "XXL"],
    },
    "beige": {
        "name": "Beige",
        "image_url": "https://content.pancake.vn/user-content2.botcake.vn/2026/9/9/bf954fea7e166081bfcec3c599301ca8e23e855f.png",
        "sizes": ["M", "L", "XL"],
    },
    "blanco": {
        "name": "Blanco",
        "image_url": "https://content.pancake.vn/user-content2.botcake.vn/2026/9/9/3d7da6940f4817961c6f58400d329ac7c66874d9.png",
        "sizes": ["M", "L", "XL"],
    },
    "celeste": {
        "name": "Celeste",
        "image_url": "https://content.pancake.vn/user-content2.botcake.vn/2026/9/9/5d9217a7149d62bcfeff3edbaf83091bfc22f661.png",
        "sizes": ["M", "L", "XL"],
    },
    "verde": {
        "name": "Verde",
        "image_url": "https://content.pancake.vn/user-content2.botcake.vn/2026/9/9/288305bcae4d8fc5471e78bd9914fdd2b3b49840.png",
        "sizes": ["M", "L", "XL"],
    },
}

COLOR_ALIASES = {
    "negra": "negro",
    "negro": "negro",
    "navy": "azul",
    "azul marino": "azul",
    "marino": "azul",
    "azul": "azul",
    "crema": "beige",
    "arena": "beige",
    "beige": "beige",
    "blanca": "blanco",
    "blanco": "blanco",
    "celeste": "celeste",
    "verde": "verde",
}


# -----------------------------------------------------------------------------
# SIZE RECOMMENDATION
# -----------------------------------------------------------------------------

@app.get("/recommend-size")
def recommend_size(
    height_cm: float = Query(..., description="Altura del cliente en cm"),
    weight_kg: float = Query(..., description="Peso del cliente en kg"),
    usual_size: str | None = Query(None, description="Talle habitual del cliente"),
    authorization: str | None = Header(None),
):
    if authorization != f"Bearer {API_TOKEN}":
        raise HTTPException(status_code=401, detail="Unauthorized")

    if weight_kg < 65:
        recommended = "M"
        confidence = "medium"
        reason = "M es el talle más chico disponible actualmente."
    elif weight_kg <= 77:
        recommended = "M"
        confidence = "high"
        reason = "Por peso corresponde principalmente M."
        if height_cm >= 188 and weight_kg >= 73:
            recommended = "L"
            confidence = "medium"
            reason = "Por altura conviene subir a L para asegurar el largo."
    elif weight_kg <= 86:
        recommended = "L"
        confidence = "high"
        reason = "Por peso corresponde principalmente L."
    elif weight_kg <= 110:
        recommended = "XL"
        confidence = "high"
        reason = "Por peso corresponde principalmente XL."
    else:
        recommended = "XL"
        confidence = "low"
        reason = "XL es el talle más grande disponible de forma general; conviene confirmar el caso."

    if usual_size:
        usual_size = usual_size.upper()

    return {
        "recommended_size": recommended,
        "confidence": confidence,
        "reason": reason,
        "height_cm": height_cm,
        "weight_kg": weight_kg,
        "usual_size": usual_size,
    }


# -----------------------------------------------------------------------------
# ORDER PREPARATION
# -----------------------------------------------------------------------------

class OrderPrepRequest(BaseModel):
    product: Optional[str] = None
    color: Optional[str] = None
    size: Optional[str] = None
    quantity: Optional[int] = None
    city: Optional[str] = None
    name: Optional[str] = None
    phone: Optional[str] = None


@app.post("/prepare-order")
def prepare_order(data: OrderPrepRequest):
    quantity = data.quantity if data.quantity and data.quantity > 0 else 1
    missing_fields: List[str] = []

    if not data.product:
        missing_fields.append("product")
    if not data.color:
        missing_fields.append("color")
    if not data.size:
        missing_fields.append("size")
    if not data.city:
        missing_fields.append("city")
    if not data.name:
        missing_fields.append("name")

    ready_to_order = len(missing_fields) == 0

    return {
        "product": data.product,
        "color": data.color,
        "size": data.size,
        "quantity": quantity,
        "city": data.city,
        "name": data.name,
        "phone": data.phone,
        "missing_fields": missing_fields,
        "ready_to_order": ready_to_order,
        "next_step": "ready" if ready_to_order else f"ask_for_{missing_fields[0]}",
    }


# -----------------------------------------------------------------------------
# SHIPPING PREPARATION
# -----------------------------------------------------------------------------

class ShippingPrepRequest(BaseModel):
    department: Optional[str] = None
    city: Optional[str] = None
    order_confirmed: Optional[bool] = False
    location_shared: Optional[bool] = False
    full_name: Optional[str] = None
    ci: Optional[str] = None


@app.post("/prepare-shipping")
def prepare_shipping(data: ShippingPrepRequest):
    department = (data.department or "").strip().lower()
    city = (data.city or "").strip().lower()

    is_santa_cruz = (
        "santa cruz" in department
        or "santa cruz" in city
        or department in ["scz", "santa cruz de la sierra"]
        or city in ["scz", "santa cruz de la sierra"]
    )

    if not data.order_confirmed:
        return {
            "shipping_type": "not_ready",
            "missing_fields": [],
            "next_step": "wait_for_order_confirmation",
            "handoff_required": False,
            "message": "No pedir datos de envío todavía.",
        }

    if is_santa_cruz:
        if not data.location_shared:
            return {
                "shipping_type": "santa_cruz",
                "missing_fields": ["location"],
                "next_step": "ask_location",
                "handoff_required": False,
                "message": "Pedir ubicación para coordinar el envío.",
            }

        return {
            "shipping_type": "santa_cruz",
            "missing_fields": [],
            "next_step": "handoff_admin",
            "handoff_required": True,
            "message": "Ubicación recibida. Derivar a administrador.",
        }

    missing_fields = []
    if not data.full_name:
        missing_fields.append("full_name")
    if not data.ci:
        missing_fields.append("ci")

    if missing_fields:
        return {
            "shipping_type": "other_department",
            "missing_fields": missing_fields,
            "next_step": "ask_full_name_and_ci",
            "handoff_required": False,
            "message": "Pedir nombre completo y CI.",
        }

    return {
        "shipping_type": "other_department",
        "missing_fields": [],
        "next_step": "handoff_admin",
        "handoff_required": True,
        "message": "Nombre completo y CI recibidos. Derivar a administrador.",
    }


# -----------------------------------------------------------------------------
# CATALOG
# -----------------------------------------------------------------------------

@app.get("/catalog")
def get_catalog(color: Optional[str] = None):
    if color:
        normalized = COLOR_ALIASES.get(color.strip().lower(), color.strip().lower())
        item = FOSTERS_CATALOG.get(normalized)

        if not item:
            return {
                "found": False,
                "color": color,
                "available_colors": [item["name"] for item in FOSTERS_CATALOG.values()],
            }

        return {
            "found": True,
            "product": "Henley Fosters",
            "color": item["name"],
            "sizes": item["sizes"],
            "image_url": item["image_url"],
        }

    return {
        "found": True,
        "product": "Henley Fosters",
        "price_bs": FOSTERS_PRICE_BS,
        "colors": [
            {
                "name": item["name"],
                "sizes": item["sizes"],
                "image_url": item["image_url"],
            }
            for item in FOSTERS_CATALOG.values()
        ],
    }


# -----------------------------------------------------------------------------
# PANCAKE PRODUCT SYNC
# -----------------------------------------------------------------------------

def build_pancake_variations():
    variations = []

    for color_key, color_data in FOSTERS_CATALOG.items():
        for size in color_data["sizes"]:
            variation_id = f"henley-{color_key}-{size.lower()}"
            variations.append(
                {
                    "api_variation_id": variation_id,
                    "fields": [
                        {"name": "Color", "value": color_data["name"], "id": ""},
                        {"name": "Talla", "value": size, "id": ""},
                    ],
                    "images": [color_data["image_url"]],
                    "last_imported_price": FOSTERS_COST_BS,
                    "retail_price": FOSTERS_PRICE_BS,
                    "weight": 0,
                    "barcode": variation_id.upper(),
                    "custom_id": variation_id,
                    "permalink": "https://fosters-tools.onrender.com/catalog",
                }
            )

    return variations


@app.get("/products")
def get_products():
    all_sizes = ["M", "L", "XL", "XXL"]

    product = {
        "name": "Henley Fosters",
        "id": "fosters-henley",
        "permalink": "https://fosters-tools.onrender.com/catalog",
        "product_attributes": [
            {
                "name": "Color",
                "values": [item["name"] for item in FOSTERS_CATALOG.values()],
                "id": "color",
            },
            {
                "name": "Talla",
                "values": all_sizes,
                "id": "talla",
            },
        ],
        "variations": build_pancake_variations(),
        "weight": 0,
        "custom_id": "FOSTERS-HENLEY",
    }

    return {
        "data": [{"product": product}],
        "total": 1,
    }


# -----------------------------------------------------------------------------
# DISCOUNTS
# -----------------------------------------------------------------------------

@app.get("/discount")
def get_discount(quantity: int):
    offers = {
        2: {"total": 560, "unit_price": 280},
        3: {"total": 810, "unit_price": 270},
        4: {"total": 1050, "unit_price": 262.5},
        5: {"total": 1250, "unit_price": 250},
    }

    offer = offers.get(quantity)
    if not offer:
        return {
            "found": False,
            "quantity": quantity,
            "message": "No hay una oferta oficial configurada para esa cantidad.",
        }

    return {
        "found": True,
        "quantity": quantity,
        "total_bs": offer["total"],
        "unit_price_bs": offer["unit_price"],
        "message": f"{quantity} prendas por {offer['total']} Bs",
    }


# -----------------------------------------------------------------------------
# LEAD CLASSIFICATION
# -----------------------------------------------------------------------------

class LeadClassifyRequest(BaseModel):
    has_replied: bool = False
    has_product: bool = False
    has_color: bool = False
    has_size: bool = False
    wants_to_buy: bool = False
    asks_for_payment: bool = False
    asks_for_human: bool = False
    has_complaint: bool = False
    asks_for_discount: bool = False


@app.post("/classify-lead")
def classify_lead(data: LeadClassifyRequest):
    if data.asks_for_human or data.has_complaint or data.asks_for_payment:
        return {
            "stage": "handoff",
            "intent_level": "high",
            "should_handoff": True,
            "reason": "Caso que requiere atención humana.",
        }

    if data.wants_to_buy and data.has_product and data.has_color and data.has_size:
        return {
            "stage": "ready_to_order",
            "intent_level": "high",
            "should_handoff": False,
            "reason": "Cliente con intención clara y variante definida.",
        }

    if data.has_color or data.has_size or data.wants_to_buy or data.asks_for_discount:
        return {
            "stage": "interested",
            "intent_level": "medium",
            "should_handoff": False,
            "reason": "Cliente mostrando interés comercial.",
        }

    if data.has_replied:
        return {
            "stage": "contacted",
            "intent_level": "low",
            "should_handoff": False,
            "reason": "Cliente ya interactuó con la atención.",
        }

    return {
        "stage": "new",
        "intent_level": "low",
        "should_handoff": False,
        "reason": "Lead nuevo sin señales adicionales.",
    }


# -----------------------------------------------------------------------------
# NEXT ACTION ORCHESTRATOR
# -----------------------------------------------------------------------------

class NextActionRequest(BaseModel):
    product: Optional[str] = None
    color: Optional[str] = None
    size: Optional[str] = None
    quantity: Optional[int] = 1
    city: Optional[str] = None
    department: Optional[str] = None
    wants_to_buy: bool = False
    asks_for_catalog: bool = False
    asks_for_size_help: bool = False
    asks_for_discount: bool = False
    asks_for_payment: bool = False
    asks_for_human: bool = False
    has_complaint: bool = False
    location_shared: bool = False
    full_name: Optional[str] = None
    ci: Optional[str] = None


@app.post("/decide-next-action")
def decide_next_action(data: NextActionRequest):
    # PRIORIDAD 1: DERIVACIÓN HUMANA
    if data.asks_for_payment or data.asks_for_human or data.has_complaint:
        reason = "human_request"
        if data.asks_for_payment:
            reason = "payment_request"
        elif data.has_complaint:
            reason = "complaint"

        return {
            "next_action": "handoff",
            "priority": "critical",
            "should_handoff": True,
            "reason": reason,
            "missing_fields": [],
            "message_hint": "Derivar al administrador y detener la IA.",
        }

    # PRIORIDAD 2: AYUDA DE TALLE
    if data.asks_for_size_help and not data.size:
        return {
            "next_action": "recommend_size",
            "priority": "high",
            "should_handoff": False,
            "reason": "size_help_requested",
            "missing_fields": ["height_cm", "weight_kg"],
            "message_hint": "Pedir altura y peso si todavía no fueron proporcionados.",
        }

    # PRIORIDAD 3: CATÁLOGO
    if data.asks_for_catalog and not data.color:
        return {
            "next_action": "send_catalog",
            "priority": "normal",
            "should_handoff": False,
            "reason": "catalog_requested",
            "missing_fields": [],
            "message_hint": "Usar get_fosters_catalog y enviar todas las imágenes.",
        }

    # PRIORIDAD 4: DESCUENTO
    if data.asks_for_discount:
        if not data.quantity or data.quantity <= 1:
            return {
                "next_action": "ask_quantity_for_discount",
                "priority": "normal",
                "should_handoff": False,
                "reason": "discount_requested_without_quantity",
                "missing_fields": ["quantity"],
                "message_hint": "Preguntar cuántas prendas quiere llevar.",
            }

        return {
            "next_action": "get_discount",
            "priority": "normal",
            "should_handoff": False,
            "reason": "discount_requested",
            "missing_fields": [],
            "message_hint": "Usar get_fosters_discount.",
        }

    # PRIORIDAD 5: COMPLETAR PEDIDO
    if data.wants_to_buy:
        if not data.color:
            return {
                "next_action": "ask_color",
                "priority": "normal",
                "should_handoff": False,
                "reason": "missing_color",
                "missing_fields": ["color"],
                "message_hint": "Preguntar qué color quiere.",
            }

        if not data.size:
            return {
                "next_action": "ask_size",
                "priority": "normal",
                "should_handoff": False,
                "reason": "missing_size",
                "missing_fields": ["size"],
                "message_hint": "Preguntar qué talle busca.",
            }

        if not data.city and not data.department:
            return {
                "next_action": "ask_destination",
                "priority": "high",
                "should_handoff": False,
                "reason": "order_ready_missing_destination",
                "missing_fields": ["city_or_department"],
                "message_hint": "Preguntar si es para Santa Cruz o envío a otro departamento.",
            }

        destination = f"{data.city or ''} {data.department or ''}".strip().lower()
        is_santa_cruz = "santa cruz" in destination or destination == "scz"

        if is_santa_cruz:
            if not data.location_shared:
                return {
                    "next_action": "ask_location",
                    "priority": "high",
                    "should_handoff": False,
                    "reason": "santa_cruz_missing_location",
                    "missing_fields": ["location"],
                    "message_hint": "Pedir ubicación para coordinar el envío.",
                }

            return {
                "next_action": "handoff",
                "priority": "critical",
                "should_handoff": True,
                "reason": "santa_cruz_shipping_ready",
                "missing_fields": [],
                "message_hint": "Ubicación recibida. Derivar al administrador.",
            }

        missing_shipping = []
        if not data.full_name:
            missing_shipping.append("full_name")
        if not data.ci:
            missing_shipping.append("ci")

        if missing_shipping:
            return {
                "next_action": "ask_name_ci",
                "priority": "high",
                "should_handoff": False,
                "reason": "other_department_missing_data",
                "missing_fields": missing_shipping,
                "message_hint": "Pedir únicamente nombre completo y CI.",
            }

        return {
            "next_action": "handoff",
            "priority": "critical",
            "should_handoff": True,
            "reason": "other_department_shipping_ready",
            "missing_fields": [],
            "message_hint": "Nombre y CI recibidos. Derivar al administrador.",
        }

    return {
        "next_action": "continue_sales",
        "priority": "normal",
        "should_handoff": False,
        "reason": "no_critical_action",
        "missing_fields": [],
        "message_hint": "Continuar la conversación comercial normalmente.",
    }
