"""FOSTERS WhatsApp catalog and product-specific Botcake media plans."""
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
    },
    "polo": {
        "id": "polo", "name": "Polo Fosters", "price_bs": 300,
        "material_label": "Algodón texturizado", "status": "active",
        "colors": ["Negro", "Blanco", "Azul", "Celeste", "Beige", "Gris"],
        "sizes": SIZES, "inventory_status": "unverified", "image_urls": {},
        "campaign_key": "polo",
        "availability_note": "Confirmar stock real por talle y color en Pancake POS.",
    },
}
COLOR_ALIASES = {
    "negra": "Negro", "negro": "Negro", "blanca": "Blanco", "blanco": "Blanco",
    "azul": "Azul", "navy": "Azul", "azul marino": "Azul", "celeste": "Celeste",
    "beige": "Beige", "beige claro": "Beige", "crema": "Beige", "arena": "Beige",
    "gris": "Gris", "gris claro": "Gris", "plomo": "Gris", "plomo claro": "Gris",
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
    matches = [key for key, pattern in (("henley", r"\bhenleys?\b"),
                                       ("polo", r"\bpolos?\b"))
               if re.search(pattern, value)]
    return matches[0] if len(matches) == 1 else None


def needs_product_choice(text):
    value = clean(text)
    return (not value or value in {"general", "fosters", "camisa", "camisas"}
            or bool(re.search(r"\bhenleys?\b", value) and re.search(r"\bpolos?\b", value)))


def general_reply():
    return {
        "next_action": "ask_product", "campaign_key": "general", "product_id": None,
        "status": "active", "available_products": list(PRODUCTS),
        "missing_fields": ["product"], "should_handoff": False,
        "send_product_photos": False, "photo_attachments": [], "photo_count": 0,
        "suggested_reply": "Hola querido, estás en la tienda de Fosters. Tenemos dos productos activos: Henley de lino y Polo de algodón texturizado. ¿Qué producto estás buscando?",
    }


def unavailable_product():
    return {
        "found": False, "reason": "product_not_offered", "available_products": list(PRODUCTS),
        "next_action": "answer_product_unavailable", "should_handoff": False,
        "send_product_photos": False, "should_offer": False,
        "message": "Tenemos Henley de lino y Polo de algodón texturizado Fosters.",
        "message_hint": "Tenemos Henley de lino y Polo de algodón texturizado Fosters.",
    }


def media_plan(color=None, product="henley"):
    key = product_key(product)
    if key is None:
        return general_reply() if needs_product_choice(product) else unavailable_product()
    selected = COLOR_ALIASES.get(clean(color)) if color else None
    if color and selected not in PRODUCTS[key]["colors"]:
        return {"send_product_photos": False, "photo_attachments": [], "photo_count": 0}
    colors = [selected] if selected else PRODUCTS[key]["colors"]
    return {
        "send_product_photos": True, "product": key, "color": selected,
        "photo_attachments": [{"color": c, "filename": PHOTO_ATTACHMENTS[c],
                               "attachment_key": "henley_" + clean(c)} if key == "henley" else
                              {"color": c, "filename": None,
                               "attachment_key": "polo_" + clean(c),
                               "binding_required": True} for c in colors],
        "media_bindings_required": key == "polo",
        "photo_count": len(colors), "media_delivery": "botcake_flow_required", "media_sent": False,
        "message_hint": "Ejecutar el envío de los adjuntos originales indicados en Botcake; no limitarse a nombrar los colores. No afirmar envío hasta que la acción finalice.",
    }


def card(key):
    p = PRODUCTS[key].copy()
    p["colors"] = list(p["colors"])
    p["sizes"] = list(p["sizes"])
    p["image_urls"] = dict(p["image_urls"])
    p["photo_attachments"] = media_plan(product=key)["photo_attachments"]
    return p


def reply(key="henley"):
    if key == "henley":
        return "Henley a 300 Bs: negro, blanco, azul, celeste y beige; M, L y XL. ¿Qué color y talle llevás?"
    return "Hola querido, estas son las Polo de algodón texturizado de Fosters, a 300 Bs: negro, blanco, azul, celeste, beige y gris; M, L y XL. ¿Qué talla y color buscás?"


@router.get("/fosters/products")
def products():
    return {"primary_product": None, "products": [card(key) for key in PRODUCTS],
            "stock_is_verified": False, "sales_channel": "whatsapp", "web_orders_enabled": False}


@router.get("/fosters/product")
def product(product: Optional[str] = None, color: Optional[str] = None):
    key = product_key(product)
    if key is None:
        if needs_product_choice(product):
            return {"found": False, "reason": "product_required", **general_reply()}
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
    key = product_key(product)
    if key is None:
        if needs_product_choice(product):
            return general_reply()
        return {**unavailable_product(), "status": "inactive"}
    return {
        **media_plan(product=key), "campaign_key": key, "product_id": key, "status": "active",
        "suggested_reply": reply(key), "manual_botcake_flow_setup_required": True,
        "send_size_chart": True,
        "size_chart": {"attachment_key": "fosters_size_chart", "binding_required": True},
        "note": "Vincular fotos y tabla originales en Botcake. Esta API prepara el plan; no envía medios.",
    }
