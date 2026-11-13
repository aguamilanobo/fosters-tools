"""Fosters channel policy. Legacy web tooling is retained, but inactive."""
import re


def is_web_order(message=None, web_order=False):
    return web_order or bool(re.search(
        r"fostersbolivia\.shop|shopify|hola\s+fosters[,!\s]*quiero\s+hacer\s+este\s+pedido",
        message or "", re.IGNORECASE))


def disabled_web_order():
    return {
        "next_action": "handoff", "reason": "web_orders_disabled",
        "sales_channel": "whatsapp", "web_orders_enabled": False,
        "should_handoff": True, "priority": "critical", "missing_fields": [],
        "send_product_photos": False, "order_created": False,
        "message_hint": "Los pedidos web están desactivados. Derivar para revisión humana sin crear, modificar, cobrar ni cancelar pedidos web.",
    }
