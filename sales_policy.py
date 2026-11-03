"""Shared customer-facing store information; no extra sales step on location queries."""
from fastapi import APIRouter

router = APIRouter()
LOCATION_REPLY = (
    "Somos tienda online de Santa Cruz, no tenemos tienda física. "
    "Realizamos envíos a domicilio en Santa Cruz y por transporte a todo Bolivia."
)


def location_response():
    return {
        "next_action": "answer_store_location",
        "priority": "high",
        "should_handoff": False,
        "reason": "store_location_requested",
        "missing_fields": [],
        "message": LOCATION_REPLY,
        "message_hint": LOCATION_REPLY,
        "stop_after_reply": True,
    }


@router.get("/store-info")
def store_info():
    return location_response()
