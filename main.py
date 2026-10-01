from fastapi import FastAPI, Query, Header, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from typing import Optional, List
import os
import json
from urllib import request as urllib_request, error as urllib_error

app = FastAPI(title="FOSTERS + aguaMILANO AI Tools")

API_TOKEN = "fosters_bot_2026"
telegram_bearer = HTTPBearer(auto_error=False)


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
        <title>FOSTERS + aguaMILANO AI Tools</title>
        <style>
            * { box-sizing: border-box; margin: 0; padding: 0; }
            body { background:#0a0a0a; color:#f5f5f0; font-family:Arial,Helvetica,sans-serif; min-height:100vh; }
            .container { width:90%; max-width:1100px; margin:auto; padding:70px 0; }
            .header { margin-bottom:50px; }
            .brand { font-family:Georgia,'Times New Roman',serif; font-size:42px; letter-spacing:8px; margin-bottom:10px; }
            .subtitle { color:#888; font-size:14px; letter-spacing:2px; text-transform:uppercase; }
            .status { display:inline-flex; align-items:center; gap:8px; margin-top:24px; padding:9px 14px; border:1px solid #2d2d2d; border-radius:999px; font-size:13px; color:#bbb; }
            .dot { width:8px; height:8px; background:#5ad66f; border-radius:50%; }
            .section-title { margin-bottom:20px; font-size:13px; color:#777; letter-spacing:2px; text-transform:uppercase; }
            .grid { display:grid; grid-template-columns:repeat(auto-fit,minmax(280px,1fr)); gap:15px; }
            .card { background:#111; border:1px solid #222; border-radius:14px; padding:24px; transition:.2s ease; }
            .card:hover { transform:translateY(-3px); border-color:#3a3a3a; }
            .card h3 { font-size:17px; margin-bottom:9px; font-weight:500; }
            .endpoint { display:inline-block; margin-bottom:12px; color:#888; font-family:monospace; font-size:13px; }
            .card p { color:#aaa; line-height:1.6; font-size:14px; }
            .footer { margin-top:50px; padding-top:25px; border-top:1px solid #1f1f1f; display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:15px; color:#666; font-size:12px; }
            .docs { color:#ddd; text-decoration:none; border:1px solid #333; padding:10px 15px; border-radius:8px; }
            .docs:hover { background:#181818; }
            @media (max-width:600px) { .brand { font-size:30px; letter-spacing:5px; } .container { padding:40px 0; } }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <div class="brand">FOSTERS</div>
                <div class="subtitle">Multi-brand AI Tools Infrastructure</div>
                <div class="status"><span class="dot"></span>System operational</div>
            </div>
            <div class="section-title">Active Skills & Integrations</div>
            <div class="grid">
                <div class="card"><h3>Size Recommendation</h3><span class="endpoint">GET /recommend-size</span><p>Recommends the ideal Fosters size based on height and weight.</p></div>
                <div class="card"><h3>Order Preparation</h3><span class="endpoint">POST /prepare-order</span><p>Structures product, color, size and quantity before shipping.</p></div>
                <div class="card"><h3>Shipping Preparation</h3><span class="endpoint">POST /prepare-shipping</span><p>Determines the correct shipping flow.</p></div>
                <div class="card"><h3>Product Catalog</h3><span class="endpoint">GET /catalog</span><p>Returns current Henley colors, sizes and images.</p></div>
                <div class="card"><h3>Pancake Product Sync</h3><span class="endpoint">GET /products?page=1&pageSize=50</span><p>Paginated product feed for Pancake.</p></div>
                <div class="card"><h3>Pancake Sync Test</h3><span class="endpoint">GET /products-test?page=1&pageSize=50</span><p>Minimal one-product feed with warehouse stock for Pancake synchronization testing.</p></div>
                <div class="card"><h3>Discount Engine</h3><span class="endpoint">GET /discount</span><p>Returns official quantity discounts when explicitly requested.</p></div>
                <div class="card"><h3>Lead Classification</h3><span class="endpoint">POST /classify-lead</span><p>Classifies commercial intent and human handoff.</p></div>
                <div class="card"><h3>Next Action Decision</h3><span class="endpoint">POST /decide-next-action</span><p>Chooses the next commercial action using deterministic priorities.</p></div>\n                <div class="card"><h3>Telegram Handoff Alerts</h3><span class="endpoint">POST /notify-handoff</span><p>Sends internal Telegram notifications when a conversation is derived to a human.</p></div>
                <div class="card"><h3>aguaMILANO Catalog</h3><span class="endpoint">GET /agua/catalog</span><p>Returns the current aguaMILANO catalog, prices, colors and product status.</p></div>
                <div class="card"><h3>aguaMILANO Shirt Size</h3><span class="endpoint">GET /agua/recommend-shirt-size</span><p>Recommends shirt size using height, weight and the real garment measurements.</p></div>
                <div class="card"><h3>aguaMILANO Stock</h3><span class="endpoint">POST /agua/check-stock</span><p>Stock-check contract prepared for Pancake POS integration.</p></div>
                <div class="card"><h3>aguaMILANO Order</h3><span class="endpoint">POST /agua/prepare-order</span><p>Structures shirts, shorts, matching sets and future espadrille orders.</p></div>
                <div class="card"><h3>aguaMILANO Shipping</h3><span class="endpoint">POST /agua/prepare-shipping</span><p>Determines Santa Cruz vs national shipping flow.</p></div>
                <div class="card"><h3>aguaMILANO Orchestrator</h3><span class="endpoint">POST /agua/decide-next-action</span><p>Chooses the next commercial action for the aguaMILANO agent.</p></div>
            </div>
            <div class="footer"><span>FOSTERS · Santa Cruz, Bolivia</span><a class="docs" href="/docs">API Documentation</a></div>
        </div>
    </body>
    </html>
    """


# -----------------------------------------------------------------------------
# SHARED PRODUCT DATA
# -----------------------------------------------------------------------------

FOSTERS_PRICE_BS = 300
FOSTERS_COST_BS = 110
PANCAKE_WAREHOUSE_ID = "c52e67ad-d9d0-4276-abe4-e0c9f1f7d2da"

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
    "negra": "negro", "negro": "negro",
    "navy": "azul", "azul marino": "azul", "marino": "azul", "azul": "azul",
    "crema": "beige", "arena": "beige", "beige": "beige",
    "blanca": "blanco", "blanco": "blanco",
    "celeste": "celeste", "verde": "verde",
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
        recommended, confidence, reason = "M", "medium", "M es el talle más chico disponible actualmente."
    elif weight_kg <= 77:
        recommended, confidence, reason = "M", "high", "Por peso corresponde principalmente M."
        if height_cm >= 188 and weight_kg >= 73:
            recommended, confidence, reason = "L", "medium", "Por altura conviene subir a L para asegurar el largo."
    elif weight_kg <= 86:
        recommended, confidence, reason = "L", "high", "Por peso corresponde principalmente L."
    elif weight_kg <= 110:
        recommended, confidence, reason = "XL", "high", "Por peso corresponde principalmente XL."
    else:
        recommended, confidence, reason = "XL", "low", "XL es el talle más grande disponible de forma general; conviene confirmar el caso."

    if usual_size:
        usual_size = usual_size.upper()

    return {"recommended_size": recommended, "confidence": confidence, "reason": reason, "height_cm": height_cm, "weight_kg": weight_kg, "usual_size": usual_size}


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
    if not data.product: missing_fields.append("product")
    if not data.color: missing_fields.append("color")
    if not data.size: missing_fields.append("size")
    if not data.city: missing_fields.append("city")
    if not data.name: missing_fields.append("name")
    ready_to_order = len(missing_fields) == 0
    return {
        "product": data.product, "color": data.color, "size": data.size,
        "quantity": quantity, "city": data.city, "name": data.name, "phone": data.phone,
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
        "santa cruz" in department or "santa cruz" in city
        or department in ["scz", "santa cruz de la sierra"]
        or city in ["scz", "santa cruz de la sierra"]
    )
    if not data.order_confirmed:
        return {"shipping_type":"not_ready","missing_fields":[],"next_step":"wait_for_order_confirmation","handoff_required":False,"message":"No pedir datos de envío todavía."}
    if is_santa_cruz:
        if not data.location_shared:
            return {"shipping_type":"santa_cruz","missing_fields":["location"],"next_step":"ask_location","handoff_required":False,"message":"Pedir ubicación para coordinar el envío."}
        return {"shipping_type":"santa_cruz","missing_fields":[],"next_step":"handoff_admin","handoff_required":True,"message":"Ubicación recibida. Derivar a administrador."}
    missing_fields = []
    if not data.full_name: missing_fields.append("full_name")
    if not data.ci: missing_fields.append("ci")
    if missing_fields:
        return {"shipping_type":"other_department","missing_fields":missing_fields,"next_step":"ask_full_name_and_ci","handoff_required":False,"message":"Pedir nombre completo y CI."}
    return {"shipping_type":"other_department","missing_fields":[],"next_step":"handoff_admin","handoff_required":True,"message":"Nombre completo y CI recibidos. Derivar a administrador."}


# -----------------------------------------------------------------------------
# CATALOG
# -----------------------------------------------------------------------------

@app.get("/catalog")
def get_catalog(color: Optional[str] = None):
    if color:
        normalized = COLOR_ALIASES.get(color.strip().lower(), color.strip().lower())
        item = FOSTERS_CATALOG.get(normalized)
        if not item:
            return {"found":False,"color":color,"available_colors":[x["name"] for x in FOSTERS_CATALOG.values()]}
        return {"found":True,"product":"Henley Fosters","color":item["name"],"sizes":item["sizes"],"image_url":item["image_url"]}
    return {
        "found":True,
        "product":"Henley Fosters",
        "price_bs":FOSTERS_PRICE_BS,
        "colors":[{"name":x["name"],"sizes":x["sizes"],"image_url":x["image_url"]} for x in FOSTERS_CATALOG.values()],
    }


# -----------------------------------------------------------------------------
# PANCAKE PRODUCT SYNC
# -----------------------------------------------------------------------------

def build_pancake_variations():
    variations = []
    for color_key, color_data in FOSTERS_CATALOG.items():
        for size in color_data["sizes"]:
            variation_id = f"henley-{color_key}-{size.lower()}"
            variations.append({
                "api_variation_id": variation_id,
                "fields": [
                    {"name":"Color","value":color_data["name"],"id":""},
                    {"name":"Size","value":size,"id":""},
                ],
                "images": [color_data["image_url"]],
                "last_imported_price": FOSTERS_PRICE_BS,
                "retail_price": FOSTERS_PRICE_BS,
                "weight": 0,
                "barcode": variation_id.upper(),
                "custom_id": variation_id,
                "permalink": f"https://fosters-tools.onrender.com/catalog?color={color_key}",
            })
    return variations

@app.get("/products")
def get_products(
    page: int = Query(1, ge=1),
    pageSize: int = Query(50, ge=1, le=100),
):
    product = {
        "name": "Henley Fosters",
        "id": "fosters-henley",
        "permalink": "https://fosters-tools.onrender.com/catalog",
        "product_attributes": [
            {"name":"Color","values":[x["name"] for x in FOSTERS_CATALOG.values()],"id":""},
            {"name":"Size","values":["M","L","XL","XXL"],"id":""},
        ],
        "variations": build_pancake_variations(),
        "weight": 1,
        "custom_id": "FOSTERS-HENLEY",
        "variations_warehouses": [],
    }
    products = [{"product": product}]
    start = (page - 1) * pageSize
    end = start + pageSize
    return {"data": products[start:end], "total": len(products)}


@app.get("/products-test")
def get_products_test(
    page: int = Query(1, ge=1),
    pageSize: int = Query(50, ge=1, le=100),
):
    test_product = {
        "name": "Henley Fosters Test",
        "id": "fosters-henley-test",
        "permalink": "https://fosters-tools.onrender.com/catalog",
        "product_attributes": [
            {"name": "Color", "values": ["Negro"], "id": ""},
            {"name": "Size", "values": ["M"], "id": ""},
        ],
        "variations": [
            {
                "api_variation_id": "henley-test-negro-m",
                "fields": [
                    {"name": "Color", "value": "Negro", "id": ""},
                    {"name": "Size", "value": "M", "id": ""},
                ],
                "images": [],
                "last_imported_price": 300,
                "retail_price": 300,
                "weight": 0,
                "barcode": "HENLEY-TEST-NEGRO-M",
                "custom_id": "henley-test-negro-m",
                "permalink": "https://fosters-tools.onrender.com/catalog?color=negro",
            }
        ],
        "weight": 1,
        "custom_id": "FOSTERS-HENLEY-TEST",
        "variations_warehouses": [
            {
                "remain_quantity": 10,
                "warehouse_id": PANCAKE_WAREHOUSE_ID,
            }
        ],
    }

    products = [{"product": test_product}]
    start = (page - 1) * pageSize
    end = start + pageSize
    return {"data": products[start:end], "total": len(products)}


# -----------------------------------------------------------------------------
# TELEGRAM HANDOFF NOTIFICATIONS
# -----------------------------------------------------------------------------

class HandoffNotifyRequest(BaseModel):
    customer_name: Optional[str] = None
    phone: Optional[str] = None
    product: Optional[str] = "Henley"
    color: Optional[str] = None
    size: Optional[str] = None
    quantity: Optional[int] = 1
    city: Optional[str] = None
    reason: Optional[str] = None
    intent_level: Optional[str] = None
    summary: Optional[str] = None
    conversation_url: Optional[str] = None


def send_telegram_message(text: str, conversation_url: Optional[str] = None):
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")

    if not bot_token or not chat_id:
        raise HTTPException(
            status_code=503,
            detail="Telegram no está configurado. Faltan TELEGRAM_BOT_TOKEN o TELEGRAM_CHAT_ID."
        )

    payload = {
        "chat_id": chat_id,
        "text": text,
        "disable_web_page_preview": True,
    }

    if conversation_url and conversation_url.startswith(("http://", "https://")):
        payload["reply_markup"] = {
            "inline_keyboard": [[
                {"text": "Abrir conversación", "url": conversation_url}
            ]]
        }

    req = urllib_request.Request(
        f"https://api.telegram.org/bot{bot_token}/sendMessage",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urllib_request.urlopen(req, timeout=10) as response:
            telegram_response = json.loads(response.read().decode("utf-8"))
    except urllib_error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise HTTPException(status_code=502, detail=f"Telegram API error: {detail}")
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"No se pudo enviar a Telegram: {exc}")

    if not telegram_response.get("ok"):
        raise HTTPException(status_code=502, detail="Telegram rechazó la notificación.")

    return telegram_response


@app.post("/notify-handoff")
def notify_handoff(
    data: HandoffNotifyRequest,
    credentials: HTTPAuthorizationCredentials | None = Depends(telegram_bearer),
):
    if not credentials or credentials.scheme.lower() != "bearer" or credentials.credentials != API_TOKEN:
        raise HTTPException(status_code=401, detail="Unauthorized")

    quantity = data.quantity if data.quantity and data.quantity > 0 else 1

    order_parts = []
    if data.product:
        order_parts.append(data.product)
    if data.color:
        order_parts.append(data.color)
    if data.size:
        order_parts.append(data.size)

    order_text = " ".join(order_parts).strip() or "Sin producto definido"
    if quantity > 1:
        order_text = f"{quantity} x {order_text}"
    else:
        order_text = f"1 x {order_text}"

    reason_labels = {
        "payment_request": "Pidió QR / pago",
        "human_request": "Solicitó atención humana",
        "complaint": "Reclamo",
        "santa_cruz_shipping_ready": "Datos de entrega completos",
        "other_department_shipping_ready": "Datos de envío completos",
    }
    reason_text = reason_labels.get(data.reason or "", data.reason or "Derivación solicitada")

    lines = [
        "NUEVA DERIVACIÓN — FOSTERS",
        "",
        f"Cliente: {data.customer_name or 'Sin nombre'}",
        f"Pedido: {order_text}",
        f"Ciudad: {data.city or 'Sin definir'}",
        f"Motivo: {reason_text}",
        f"Intención: {data.intent_level or 'Sin clasificar'}",
    ]

    if data.phone:
        lines.append(f"Teléfono: {data.phone}")

    if data.summary:
        lines.extend(["", f"Resumen: {data.summary}"])

    telegram_response = send_telegram_message(
        "\n".join(lines),
        data.conversation_url,
    )

    result = telegram_response.get("result", {})
    return {
        "sent": True,
        "channel": "telegram",
        "message_id": result.get("message_id"),
        "chat_id": result.get("chat", {}).get("id"),
    }


# -----------------------------------------------------------------------------
# aguaMILANO — INITIAL SKILLS
# -----------------------------------------------------------------------------

AGUA_CAMISA_PRICE_BS = 350
AGUA_SHORT_PRICE_BS = 330
AGUA_ALPARGATA_PRICE_BS = 370

AGUA_SHIRT_MEASUREMENTS = {
    "M": {"width_cm": 55, "length_cm": 72},
    "L": {"width_cm": 60, "length_cm": 75},
    "XL": {"width_cm": 65, "length_cm": 77},
}

AGUA_CATALOG = {
    "camisa": {
        "name": "Camisa manga corta de lino",
        "price_bs": AGUA_CAMISA_PRICE_BS,
        "status": "active",
        "colors": ["Perla", "Azul"],
        "sizes": ["M", "L", "XL"],
        "measurements": AGUA_SHIRT_MEASUREMENTS,
    },
    "short": {
        "name": "Short de lino",
        "price_bs": AGUA_SHORT_PRICE_BS,
        "status": "active",
        "colors": ["Perla", "Azul"],
        "sizes": [],
        "measurements": None,
        "note": "Tabla de medidas pendiente. No recomendar talle automáticamente todavía.",
    },
    "alpargata": {
        "name": "Alpargatas",
        "price_bs": AGUA_ALPARGATA_PRICE_BS,
        "status": "coming_soon",
        "colors": [],
        "sizes": ["40", "41", "42"],
        "measurements": None,
        "note": "Próximo ingreso desde Argentina. No ofrecer como disponible hasta confirmar stock.",
    },
}

AGUA_PRODUCT_ALIASES = {
    "camisa": "camisa",
    "camisa lino": "camisa",
    "camisa de lino": "camisa",
    "manga corta": "camisa",
    "short": "short",
    "shorts": "short",
    "short lino": "short",
    "short de lino": "short",
    "alpargata": "alpargata",
    "alpargatas": "alpargata",
    "conjunto": "conjunto",
    "set": "conjunto",
}


def normalize_agua_product(product: Optional[str]) -> Optional[str]:
    if not product:
        return None
    key = product.strip().lower()
    return AGUA_PRODUCT_ALIASES.get(key, key)


@app.get("/agua/catalog")
def get_agua_catalog(
    product: Optional[str] = None,
    color: Optional[str] = None,
):
    normalized = normalize_agua_product(product)

    if normalized == "conjunto":
        return {
            "found": True,
            "product": "Conjunto camisa + short de lino",
            "status": "active",
            "price_bs": AGUA_CAMISA_PRICE_BS + AGUA_SHORT_PRICE_BS,
            "items": ["camisa", "short"],
            "colors": ["Perla", "Azul"],
            "note": "El conjunto son dos prendas independientes. El stock debe verificarse por cada prenda y variante.",
        }

    if normalized:
        item = AGUA_CATALOG.get(normalized)
        if not item:
            return {
                "found": False,
                "product": product,
                "available_products": [x["name"] for x in AGUA_CATALOG.values()],
            }

        if color:
            available = any(c.lower() == color.strip().lower() for c in item["colors"])
            return {
                "found": available,
                "product_key": normalized,
                "product": item["name"],
                "color": color,
                "available_colors": item["colors"],
                "price_bs": item["price_bs"],
                "status": item["status"],
                "sizes": item["sizes"],
                "measurements": item["measurements"],
                "note": item.get("note"),
            }

        return {
            "found": True,
            "product_key": normalized,
            **item,
        }

    return {
        "found": True,
        "brand": "aguaMILANO",
        "products": [
            {"product_key": key, **item}
            for key, item in AGUA_CATALOG.items()
        ],
        "matching_set": {
            "name": "Conjunto camisa + short de lino",
            "price_bs": AGUA_CAMISA_PRICE_BS + AGUA_SHORT_PRICE_BS,
            "colors": ["Perla", "Azul"],
        },
    }


@app.get("/agua/recommend-shirt-size")
def recommend_agua_shirt_size(
    height_cm: float = Query(..., description="Altura del cliente en cm"),
    weight_kg: float = Query(..., description="Peso del cliente en kg"),
    usual_size: Optional[str] = Query(None, description="Talle habitual del cliente"),
):
    usual = usual_size.upper().strip() if usual_size else None

    # Conservative initial heuristic until we accumulate real fit outcomes.
    # The real garment dimensions are always returned so the agent can ground the recommendation.
    if usual in AGUA_SHIRT_MEASUREMENTS:
        recommended = usual
        confidence = "high"
        reason = "Se prioriza el talle habitual del cliente y se valida con las medidas reales de la prenda."
    elif weight_kg <= 74:
        recommended = "M"
        confidence = "medium"
        reason = "Estimación inicial por altura y peso; conviene usar las medidas reales como referencia."
    elif weight_kg <= 90:
        recommended = "L"
        confidence = "medium"
        reason = "Estimación inicial por altura y peso; conviene usar las medidas reales como referencia."
    else:
        recommended = "XL"
        confidence = "medium"
        reason = "Estimación inicial por altura y peso; conviene usar las medidas reales como referencia."

    # Tall/slim edge case: prioritize garment length.
    if recommended == "M" and height_cm >= 188 and weight_kg >= 70:
        recommended = "L"
        confidence = "medium"
        reason = "Por la altura conviene subir a L para ganar largo, usando la tabla real como referencia."

    measurements = AGUA_SHIRT_MEASUREMENTS[recommended]
    return {
        "recommended_size": recommended,
        "confidence": confidence,
        "reason": reason,
        "height_cm": height_cm,
        "weight_kg": weight_kg,
        "usual_size": usual,
        "garment_width_cm": measurements["width_cm"],
        "garment_length_cm": measurements["length_cm"],
        "measurement_source": "tabla_real_agua_milano",
    }


class AguaStockRequest(BaseModel):
    product: Optional[str] = None
    color: Optional[str] = None
    size: Optional[str] = None
    quantity: int = 1


@app.post("/agua/check-stock")
def check_agua_stock(data: AguaStockRequest):
    product = normalize_agua_product(data.product)

    if product == "alpargata":
        return {
            "connected": False,
            "available": False,
            "status": "coming_soon",
            "product": "alpargata",
            "message": "Las alpargatas todavía no deben ofrecerse como disponibles hasta confirmar el ingreso.",
        }

    if product not in ("camisa", "short"):
        return {
            "connected": False,
            "available": None,
            "status": "invalid_product",
            "message": "Producto no reconocido para control de stock.",
        }

    return {
        "connected": False,
        "available": None,
        "status": "pos_integration_pending",
        "product": product,
        "color": data.color,
        "size": data.size,
        "quantity": max(data.quantity, 1),
        "message": "Contrato de stock listo. Falta conectar lectura de inventario del POS de Pancake antes de confirmar disponibilidad automáticamente.",
    }


class AguaOrderItem(BaseModel):
    product: str
    color: Optional[str] = None
    size: Optional[str] = None
    quantity: int = 1


class AguaOrderRequest(BaseModel):
    product: Optional[str] = None
    color: Optional[str] = None
    size: Optional[str] = None
    quantity: int = 1
    city: Optional[str] = None
    items: Optional[List[AguaOrderItem]] = None


@app.post("/agua/prepare-order")
def prepare_agua_order(data: AguaOrderRequest):
    raw_items = data.items or []
    if not raw_items and data.product:
        raw_items = [AguaOrderItem(product=data.product, color=data.color, size=data.size, quantity=data.quantity or 1)]

    if not raw_items:
        return {
            "ready_to_order": False,
            "missing_fields": ["product"],
            "next_step": "ask_product",
            "items": [],
            "total_bs": 0,
            "city": data.city,
        }

    normalized_items = []
    missing_fields = []
    total_bs = 0

    for idx, raw in enumerate(raw_items):
        product = normalize_agua_product(raw.product)
        qty = raw.quantity if raw.quantity and raw.quantity > 0 else 1

        if product == "conjunto":
            # Expand a matching set into its two physical POS items.
            for child in ("camisa", "short"):
                item_data = AGUA_CATALOG[child]
                normalized_items.append({
                    "product": child,
                    "product_name": item_data["name"],
                    "color": raw.color,
                    "size": raw.size,
                    "quantity": qty,
                    "unit_price_bs": item_data["price_bs"],
                    "subtotal_bs": item_data["price_bs"] * qty,
                    "stock_check_required": True,
                })
                total_bs += item_data["price_bs"] * qty
                if not raw.color:
                    missing_fields.append(f"items[{idx}].color")
                if not raw.size:
                    missing_fields.append(f"items[{idx}].size")
            continue

        item_data = AGUA_CATALOG.get(product or "")
        if not item_data:
            missing_fields.append(f"items[{idx}].product")
            continue

        if item_data["status"] != "active":
            normalized_items.append({
                "product": product,
                "product_name": item_data["name"],
                "status": item_data["status"],
                "quantity": qty,
            })
            missing_fields.append(f"items[{idx}].availability")
            continue

        if not raw.color:
            missing_fields.append(f"items[{idx}].color")
        if not raw.size:
            missing_fields.append(f"items[{idx}].size")

        subtotal = item_data["price_bs"] * qty
        total_bs += subtotal
        normalized_items.append({
            "product": product,
            "product_name": item_data["name"],
            "color": raw.color,
            "size": raw.size,
            "quantity": qty,
            "unit_price_bs": item_data["price_bs"],
            "subtotal_bs": subtotal,
            "stock_check_required": True,
        })

    # Stock is intentionally required before an order can be considered final.
    ready = len(missing_fields) == 0
    next_step = "check_stock" if ready else "collect_missing_fields"

    return {
        "ready_to_order": ready,
        "stock_check_required": ready,
        "missing_fields": sorted(set(missing_fields)),
        "next_step": next_step,
        "items": normalized_items,
        "total_bs": total_bs,
        "city": data.city,
    }


class AguaShippingRequest(BaseModel):
    city: Optional[str] = None
    department: Optional[str] = None
    order_confirmed: bool = False
    location_shared: bool = False
    full_name: Optional[str] = None
    ci: Optional[str] = None


@app.post("/agua/prepare-shipping")
def prepare_agua_shipping(data: AguaShippingRequest):
    destination = f"{data.city or ''} {data.department or ''}".strip().lower()
    is_santa_cruz = "santa cruz" in destination or destination == "scz"

    if not data.order_confirmed:
        return {
            "shipping_type": "not_ready",
            "next_step": "wait_for_order_confirmation",
            "missing_fields": [],
            "handoff_required": False,
        }

    if not destination:
        return {
            "shipping_type": "unknown",
            "next_step": "ask_destination",
            "missing_fields": ["city_or_department"],
            "handoff_required": False,
        }

    if is_santa_cruz:
        if not data.location_shared:
            return {
                "shipping_type": "santa_cruz",
                "next_step": "ask_location",
                "missing_fields": ["location"],
                "handoff_required": False,
            }
        return {
            "shipping_type": "santa_cruz",
            "next_step": "handoff_admin",
            "missing_fields": [],
            "handoff_required": True,
        }

    missing = []
    if not data.full_name:
        missing.append("full_name")
    if not data.ci:
        missing.append("ci")

    if missing:
        return {
            "shipping_type": "other_department",
            "next_step": "ask_full_name_and_ci",
            "missing_fields": missing,
            "handoff_required": False,
        }

    return {
        "shipping_type": "other_department",
        "next_step": "handoff_admin",
        "missing_fields": [],
        "handoff_required": True,
    }


class AguaNextActionRequest(BaseModel):
    product: Optional[str] = None
    color: Optional[str] = None
    size: Optional[str] = None
    quantity: int = 1
    city: Optional[str] = None
    department: Optional[str] = None
    wants_to_buy: bool = False
    asks_for_catalog: bool = False
    asks_for_size_help: bool = False
    asks_for_payment: bool = False
    asks_for_human: bool = False
    has_complaint: bool = False
    stock_checked: bool = False
    stock_available: Optional[bool] = None
    location_shared: bool = False
    full_name: Optional[str] = None
    ci: Optional[str] = None


@app.post("/agua/decide-next-action")
def decide_agua_next_action(data: AguaNextActionRequest):
    product = normalize_agua_product(data.product)

    if data.asks_for_payment or data.asks_for_human or data.has_complaint:
        reason = "payment_request" if data.asks_for_payment else "complaint" if data.has_complaint else "human_request"
        return {
            "next_action": "handoff",
            "priority": "critical",
            "should_handoff": True,
            "reason": reason,
            "missing_fields": [],
        }

    if data.asks_for_catalog:
        return {
            "next_action": "send_catalog",
            "priority": "normal",
            "should_handoff": False,
            "reason": "catalog_requested",
            "missing_fields": [],
        }

    if data.asks_for_size_help:
        if product == "short":
            return {
                "next_action": "short_size_manual_help",
                "priority": "high",
                "should_handoff": True,
                "reason": "short_measurements_pending",
                "missing_fields": [],
                "message_hint": "No recomendar talle de short automáticamente hasta cargar su tabla real.",
            }
        if product == "alpargata":
            return {
                "next_action": "ask_espadrille_size",
                "priority": "normal",
                "should_handoff": False,
                "reason": "espadrille_sizes_are_numeric",
                "missing_fields": ["size"],
                "available_sizes": ["40", "41", "42"],
            }
        return {
            "next_action": "recommend_shirt_size",
            "priority": "high",
            "should_handoff": False,
            "reason": "shirt_size_help_requested",
            "missing_fields": ["height_cm", "weight_kg"],
        }

    if data.wants_to_buy:
        if not product:
            return {"next_action":"ask_product","priority":"normal","should_handoff":False,"reason":"missing_product","missing_fields":["product"]}

        if product == "alpargata":
            return {
                "next_action": "coming_soon",
                "priority": "normal",
                "should_handoff": False,
                "reason": "espadrilles_not_yet_available",
                "missing_fields": [],
            }

        if not data.color:
            return {"next_action":"ask_color","priority":"normal","should_handoff":False,"reason":"missing_color","missing_fields":["color"]}
        if not data.size:
            return {"next_action":"ask_size","priority":"normal","should_handoff":False,"reason":"missing_size","missing_fields":["size"]}

        if not data.stock_checked:
            return {
                "next_action": "check_stock",
                "priority": "high",
                "should_handoff": False,
                "reason": "variant_defined_stock_not_checked",
                "missing_fields": [],
            }

        if data.stock_available is False:
            return {
                "next_action": "offer_alternative",
                "priority": "high",
                "should_handoff": False,
                "reason": "out_of_stock",
                "missing_fields": [],
            }

        if not data.city and not data.department:
            return {
                "next_action": "ask_destination",
                "priority": "high",
                "should_handoff": False,
                "reason": "order_ready_missing_destination",
                "missing_fields": ["city_or_department"],
            }

        destination = f"{data.city or ''} {data.department or ''}".strip().lower()
        is_santa_cruz = "santa cruz" in destination or destination == "scz"

        if is_santa_cruz:
            if not data.location_shared:
                return {"next_action":"ask_location","priority":"high","should_handoff":False,"reason":"santa_cruz_missing_location","missing_fields":["location"]}
            return {"next_action":"handoff","priority":"critical","should_handoff":True,"reason":"santa_cruz_shipping_ready","missing_fields":[]}

        missing = []
        if not data.full_name:
            missing.append("full_name")
        if not data.ci:
            missing.append("ci")

        if missing:
            return {"next_action":"ask_name_ci","priority":"high","should_handoff":False,"reason":"other_department_missing_data","missing_fields":missing}

        return {"next_action":"handoff","priority":"critical","should_handoff":True,"reason":"other_department_shipping_ready","missing_fields":[]}

    return {
        "next_action": "continue_sales",
        "priority": "normal",
        "should_handoff": False,
        "reason": "no_critical_action",
        "missing_fields": [],
    }


# -----------------------------------------------------------------------------
# DISCOUNTS
# -----------------------------------------------------------------------------

@app.get("/discount")
def get_discount(quantity: int):
    offers = {2:{"total":560,"unit_price":280},3:{"total":810,"unit_price":270},4:{"total":1050,"unit_price":262.5},5:{"total":1250,"unit_price":250}}
    offer = offers.get(quantity)
    if not offer:
        return {"found":False,"quantity":quantity,"message":"No hay una oferta oficial configurada para esa cantidad."}
    return {"found":True,"quantity":quantity,"total_bs":offer["total"],"unit_price_bs":offer["unit_price"],"message":f"{quantity} prendas por {offer['total']} Bs"}


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
        return {"stage":"handoff","intent_level":"high","should_handoff":True,"reason":"Caso que requiere atención humana."}
    if data.wants_to_buy and data.has_product and data.has_color and data.has_size:
        return {"stage":"ready_to_order","intent_level":"high","should_handoff":False,"reason":"Cliente con intención clara y variante definida."}
    if data.has_color or data.has_size or data.wants_to_buy or data.asks_for_discount:
        return {"stage":"interested","intent_level":"medium","should_handoff":False,"reason":"Cliente mostrando interés comercial."}
    if data.has_replied:
        return {"stage":"contacted","intent_level":"low","should_handoff":False,"reason":"Cliente ya interactuó con la atención."}
    return {"stage":"new","intent_level":"low","should_handoff":False,"reason":"Lead nuevo sin señales adicionales."}


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
    if data.asks_for_payment or data.asks_for_human or data.has_complaint:
        reason = "payment_request" if data.asks_for_payment else "complaint" if data.has_complaint else "human_request"
        return {"next_action":"handoff","priority":"critical","should_handoff":True,"reason":reason,"missing_fields":[],"message_hint":"Derivar al administrador y detener la IA."}

    if data.asks_for_size_help and not data.size:
        return {"next_action":"recommend_size","priority":"high","should_handoff":False,"reason":"size_help_requested","missing_fields":["height_cm","weight_kg"],"message_hint":"Pedir altura y peso si todavía no fueron proporcionados."}

    if data.asks_for_catalog and not data.color:
        return {"next_action":"send_catalog","priority":"normal","should_handoff":False,"reason":"catalog_requested","missing_fields":[],"message_hint":"Usar get_fosters_catalog y enviar todas las imágenes."}

    if data.asks_for_discount:
        if not data.quantity or data.quantity <= 1:
            return {"next_action":"ask_quantity_for_discount","priority":"normal","should_handoff":False,"reason":"discount_requested_without_quantity","missing_fields":["quantity"],"message_hint":"Preguntar cuántas prendas quiere llevar."}
        return {"next_action":"get_discount","priority":"normal","should_handoff":False,"reason":"discount_requested","missing_fields":[],"message_hint":"Usar get_fosters_discount."}

    if data.wants_to_buy:
        if not data.color:
            return {"next_action":"ask_color","priority":"normal","should_handoff":False,"reason":"missing_color","missing_fields":["color"],"message_hint":"Preguntar qué color quiere."}
        if not data.size:
            return {"next_action":"ask_size","priority":"normal","should_handoff":False,"reason":"missing_size","missing_fields":["size"],"message_hint":"Preguntar qué talle busca."}
        if not data.city and not data.department:
            return {"next_action":"ask_destination","priority":"high","should_handoff":False,"reason":"order_ready_missing_destination","missing_fields":["city_or_department"],"message_hint":"Preguntar si es para Santa Cruz o envío a otro departamento."}

        destination = f"{data.city or ''} {data.department or ''}".strip().lower()
        is_santa_cruz = "santa cruz" in destination or destination == "scz"
        if is_santa_cruz:
            if not data.location_shared:
                return {"next_action":"ask_location","priority":"high","should_handoff":False,"reason":"santa_cruz_missing_location","missing_fields":["location"],"message_hint":"Pedir ubicación para coordinar el envío."}
            return {"next_action":"handoff","priority":"critical","should_handoff":True,"reason":"santa_cruz_shipping_ready","missing_fields":[],"message_hint":"Ubicación recibida. Derivar al administrador."}

        missing_shipping = []
        if not data.full_name: missing_shipping.append("full_name")
        if not data.ci: missing_shipping.append("ci")
        if missing_shipping:
            return {"next_action":"ask_name_ci","priority":"high","should_handoff":False,"reason":"other_department_missing_data","missing_fields":missing_shipping,"message_hint":"Pedir únicamente nombre completo y CI."}
        return {"next_action":"handoff","priority":"critical","should_handoff":True,"reason":"other_department_shipping_ready","missing_fields":[],"message_hint":"Nombre y CI recibidos. Derivar al administrador."}

    return {"next_action":"continue_sales","priority":"normal","should_handoff":False,"reason":"no_critical_action","missing_fields":[],"message_hint":"Continuar la conversación comercial normalmente."}