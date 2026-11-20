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
    return {**result, 'stock_check_required': False, 'fulfillment_model': 'dropshipping',
            'response_style': 'one_short_paragraph', 'max_response_words': 25}
