"""Fosters-only sales wording and variant parsing; no inventory lookup."""
import re

from fosters_products import COLOR_ALIASES, PRODUCTS, clean

HANDOFF_REPLY = "Perfecto, querido. Enseguida te contacta alguien del equipo."
LOCATION_REPLY = "Somos tienda online de Santa Cruz. Enviamos a domicilio y a todo Bolivia."


def selected_colors(value, product):
    if not value or product not in PRODUCTS:
        return []
    raw = clean(value)
    parts = [raw] if raw in COLOR_ALIASES else re.split(r"\s*(?:[,;/+&]|\by\b)\s*", raw)
    result = []
    for part in parts:
        color = COLOR_ALIASES.get(part.strip())
        if color not in PRODUCTS[product]['colors']:
            return []
        if color not in result:
            result.append(color)
    return result


def shipping_question(missing):
    if missing == ['full_name']:
        return "¿Me pasás tu nombre completo?"
    if missing == ['ci']:
        return "¿Me pasás tu CI?"
    return "¿Me pasás tu nombre completo y CI?"


def sales_policy(result):
    if result.get('opening_required'):
        return {**result, 'stock_check_required': False, 'fulfillment_model': 'dropshipping',
                'response_style': 'complete_product_opening', 'max_response_words': None}
    return {**result, 'stock_check_required': False, 'fulfillment_model': 'dropshipping',
            'response_style': 'one_short_paragraph', 'max_response_words': 25}


def is_entry_message(value):
    """Recover ordinary ad greetings when the caller forgets is_opening.

    The caller must still pass the real per-product opening_sent state. We never
    interpret a shipping/payment/support request as a new commercial opening.
    """
    value = clean(value)
    if re.search(r'\b(qr|pago|pagar|pagado|comprobante|reclamo|devolucion|envio|envios|entrega|'
                 r'ubicacion|direccion|local|descuento|promocion|humano|asesor|administrador|'
                 r'cancelar|cambiar|cambio|pedido|problema|estafa)\b', value):
        return False
    return bool(re.search(r'\b(hola|buenas|buenos|precio|precios|valor|info|informacion|detalles|interesado|interesada|interesa)\b', value)
                or re.search(r'\bcuanto\b.*\b(cuesta|cuestan|sale|salen|vale|valen)\b', value)
                or (re.search(r'\bquiero\b', value) and re.search(r'\b(henleys?|polos?)\b', value)))
