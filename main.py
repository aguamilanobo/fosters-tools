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
