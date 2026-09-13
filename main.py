from fastapi import FastAPI, Query, Header, HTTPException

app = FastAPI()

API_TOKEN = "fosters_bot_2026"


@app.get("/")
def root():
    return {"status": "ok", "service": "fosters-tools"}


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
        reason = "XL es el talle más grande disponible; conviene confirmar medidas."

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

from pydantic import BaseModel
from typing import Optional, List

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
        "next_step": (
            "ready"
            if ready_to_order
            else f"ask_for_{missing_fields[0]}"
        )
    }
    from pydantic import BaseModel
from typing import Optional, List


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
            "message": "No pedir datos de envío todavía."
        }

    if is_santa_cruz:
        if not data.location_shared:
            return {
                "shipping_type": "santa_cruz",
                "missing_fields": ["location"],
                "next_step": "ask_location",
                "handoff_required": False,
                "message": "Pedir ubicación para coordinar el envío."
            }

        return {
            "shipping_type": "santa_cruz",
            "missing_fields": [],
            "next_step": "handoff_admin",
            "handoff_required": True,
            "message": "Ubicación recibida. Derivar a administrador."
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
            "message": "Pedir nombre completo y CI."
        }

    return {
        "shipping_type": "other_department",
        "missing_fields": [],
        "next_step": "handoff_admin",
        "handoff_required": True,
        "message": "Nombre completo y CI recibidos. Derivar a administrador."
    }

from typing import Optional

FOSTERS_CATALOG = {
    "navy": {
        "name": "navy",
        "image_url": "https://content.pancake.vn/user-content2.botcake.vn/2026/9/9/0a3d94035bd27b49047864197f5c3724017ac0fe.png"
    },
    "celeste": {
        "name": "celeste",
        "image_url": "https://content.pancake.vn/user-content2.botcake.vn/2026/9/9/5d9217a7149d62bcfeff3edbaf83091bfc22f661.png"
    },
    "blanca": {
        "name": "blanca",
        "image_url": "https://content.pancake.vn/user-content2.botcake.vn/2026/9/9/3d7da6940f4817961c6f58400d329ac7c66874d9.png"
    },
    "crema": {
        "name": "crema",
        "image_url": "https://content.pancake.vn/user-content2.botcake.vn/2026/9/9/bf954fea7e166081bfcec3c599301ca8e23e855f.png"
    },
    "negra": {
        "name": "negra",
        "image_url": "https://content.pancake.vn/user-content2.botcake.vn/2026/9/9/ae053b22c7ea2916219184518d0e10a1942790d1.png"
    },
    "marron": {
        "name": "marron",
        "image_url": "https://content.pancake.vn/user-content2.botcake.vn/2026/9/9/7a380b7ad438eba299085eb37d986d264eadd7ee.png"
    },
    "verde": {
        "name": "verde",
        "image_url": "https://content.pancake.vn/user-content2.botcake.vn/2026/9/9/288305bcae4d8fc5471e78bd9914fdd2b3b49840.png"
    }
}


@app.get("/catalog")
def get_catalog(color: Optional[str] = None):
    if color:
        normalized = color.strip().lower()

        aliases = {
            "azul": "navy",
            "azul marino": "navy",
            "marino": "navy",
            "blanco": "blanca",
            "negro": "negra",
            "marrón": "marron",
            "cafe": "marron",
            "café": "marron",
            "beige": "crema",
            "arena": "crema",
        }

        normalized = aliases.get(normalized, normalized)

        item = FOSTERS_CATALOG.get(normalized)

        if not item:
            return {
                "found": False,
                "color": color,
                "available_colors": list(FOSTERS_CATALOG.keys())
            }

        return {
            "found": True,
            "product": "Henley Fosters",
            "color": item["name"],
            "image_url": item["image_url"]
        }

    return {
        "found": True,
        "product": "Henley Fosters",
        "colors": list(FOSTERS_CATALOG.values())
    }

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
            "message": "No hay una oferta oficial configurada para esa cantidad."
        }

    return {
        "found": True,
        "quantity": quantity,
        "total_bs": offer["total"],
        "unit_price_bs": offer["unit_price"],
        "message": f"{quantity} prendas por {offer['total']} Bs"
    }

from pydantic import BaseModel
from typing import Optional


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
            "reason": "Caso que requiere atención humana."
        }

    if data.wants_to_buy and data.has_product and data.has_color and data.has_size:
        return {
            "stage": "ready_to_order",
            "intent_level": "high",
            "should_handoff": False,
            "reason": "Cliente con intención clara y variante definida."
        }

    if data.has_color or data.has_size or data.wants_to_buy or data.asks_for_discount:
        return {
            "stage": "interested",
            "intent_level": "medium",
            "should_handoff": False,
            "reason": "Cliente mostrando interés comercial."
        }

    if data.has_replied:
        return {
            "stage": "contacted",
            "intent_level": "low",
            "should_handoff": False,
            "reason": "Cliente ya interactuó con la atención."
        }

    return {
        "stage": "new",
        "intent_level": "low",
        "should_handoff": False,
        "reason": "Lead nuevo sin señales adicionales."
    }
