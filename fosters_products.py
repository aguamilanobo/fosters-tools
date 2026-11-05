"""FOSTERS sells only Henley. Media are original Botcake attachments, not URLs."""
from fastapi import APIRouter
from typing import Optional
import re
import unicodedata

router = APIRouter()
SIZES = ["M", "L", "XL"]
PRODUCTS = {
    "henley": {
        "id": "henley", "name": "Henley Fosters", "price_bs": 300,
        "material_label": "55% lino / 45% algodón", "closure": "Botones en el pecho",
        "fit": "Classic fit amplio", "status": "active",
        "colors": ["Negro", "Blanco", "Azul", "Celeste", "Beige"],
        "sizes": SIZES, "inventory_status": "unverified", "image_urls": {},
        "campaign_key": "henley",
        "availability_note": "Confirmar stock real por talle y color en Pancake POS.",
    }
}
COLOR_ALIASES = {
    "negra": "Negro", "negro": "Negro", "blanca": "Blanco", "blanco": "Blanco",
    "azul": "Azul", "navy": "Azul", "azul marino": "Azul", "celeste": "Celeste",
    "beige": "Beige", "crema": "Beige", "arena": "Beige",
}
PHOTO_ATTACHMENTS = {
    "Negro": "negra.png", "Blanco": "blanca.png", "Azul": "navy.png",
    "Celeste": "celeste.png", "Beige": "crema.png",
}


def clean(value):
    value = unicodedata.normalize("NFKD", str(value or "").strip().lower())
    return "".join(ch for ch in value if not unicodedata.combining(ch))


def contains_retired_product(value):
    # Block legacy IDs, natural-language requests and mixed orders too.
    return bool(re.search(r"short|bermuda|pantalon", clean(value)))


def product_key(text):
    value = clean(text).replace("_", " ").replace("-", " ")
    if contains_retired_product(value):
        return None
    if not value or value in {"henley", "henley fosters", "fosters henley", "camisa",
                              "camisa henley", "camisa henley fosters", "fosters"}:
        return "henley"
    return None


def unavailable_product():
    return {
        "found": False, "reason": "product_not_offered", "available_products": ["henley"],
        "next_action": "answer_product_unavailable", "should_handoff": False,
        "send_product_photos": False, "should_offer": False,
        "message": "Actualmente solo vendemos Henley Fosters.",
        "message_hint": "Actualmente solo vendemos Henley Fosters.",
    }


def media_plan(color=None):
    selected = COLOR_ALIASES.get(clean(color)) if color else None
    if color and not selected:
        return {"send_product_photos": False, "photo_attachments": [], "photo_count": 0}
    colors = [selected] if selected else list(PHOTO_ATTACHMENTS)
    return {
        "send_product_photos": True, "product": "henley", "color": selected,
        "photo_attachments": [{"color": c, "filename": PHOTO_ATTACHMENTS[c]} for c in colors],
        "photo_count": len(colors), "media_delivery": "botcake_flow_required", "media_sent": False,
        "message_hint": "Ejecutar el envío de los adjuntos originales indicados en Botcake; no limitarse a nombrar los colores. No afirmar envío hasta que la acción finalice.",
    }


def card(key):
    p = PRODUCTS[key].copy()
    p["colors"] = list(p["colors"])
    p["sizes"] = list(p["sizes"])
    p["image_urls"] = dict(p["image_urls"])
    p["photo_attachments"] = media_plan()["photo_attachments"]
    return p


def reply(key="henley"):
    return "Henley a 300 Bs: negro, blanco, azul, celeste y beige; M, L y XL. ¿Qué color y talle llevás?"


@router.get("/fosters/products")
def products():
    return {"primary_product": "henley", "products": [card("henley")], "stock_is_verified": False}


@router.get("/fosters/product")
def product(product: Optional[str] = None, color: Optional[str] = None):
    key = product_key(product)
    if key is None:
        return unavailable_product()
    p = card(key)
    if color:
        selected = COLOR_ALIASES.get(clean(color))
        if selected not in p["colors"]:
            return {"found": False, "reason": "color_not_offered", "product_id": key,
                    "available_colors": p["colors"], "send_product_photos": False}
        p["selected_color"] = selected
    return {"found": True, "product": p, "suggested_reply": reply(key)}


@router.get("/fosters/campaign-reply")
def campaign_reply(product: Optional[str] = None):
    if product_key(product) is None:
        return {**unavailable_product(), "status": "inactive"}
    return {
        **media_plan(), "campaign_key": "henley", "product_id": "henley", "status": "active",
        "suggested_reply": reply(), "manual_botcake_flow_setup_required": True,
        "note": "Vincular estos cinco adjuntos a la apertura de Botcake. Esta API no ejecuta el envío multimedia.",
    }
