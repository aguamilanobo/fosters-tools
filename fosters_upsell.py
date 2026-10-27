"""FOSTERS contextual shorts upsell. Stateless: Botcake User Fields persist the status.
No POS writes, no stock promises, no photo URLs, no automatic customer messages.
"""
from fastapi import APIRouter
from pydantic import BaseModel, Field
from typing import Optional
import unicodedata

router=APIRouter(prefix="/fosters/upsell",tags=["FOSTERS upsell"])
SHIRT_PRICE=300
SHORT_REGULAR=270  # commercial campaign proposal; confirm before activation
SHORT_UPSELL=250
SHORT_COLORS=["Azul","Negro","Blanco","Beige"]
SHORT_SIZES=["M","L","XL"]
STATUS_VALUES=["not_offered","offered","accepted","declined","completed"]
MATCHES={
 "azul":["Azul","Blanco"],
 "navy":["Azul","Blanco"],
 "azul marino":["Azul","Blanco"],
 "negro":["Negro","Blanco"],
 "blanco":["Blanco","Azul"],
 "celeste":["Blanco","Azul"],
 "beige":["Beige","Azul"],
 "crema":["Beige","Azul"],
}
FIELDS=["fosters_upsell_estado","fosters_upsell_color","fosters_upsell_talle","fosters_upsell_cantidad","fosters_upsell_oferta_id"]

def n(v):
 s=unicodedata.normalize("NFKD",str(v or "").strip().lower())
 return "".join(c for c in s if not unicodedata.combining(c))
def suggested(c):
 return MATCHES.get(n(c),["Blanco","Azul"])
def selected_color(v):
 normalized=n(v)
 if normalized in ("perla","blanco perla"): normalized="blanco"
 if normalized in ("azul marino","navy"): normalized="azul"
 return next((x for x in SHORT_COLORS if n(x)==normalized),None)

class OfferRequest(BaseModel):
 product:str="henley"
 shirt_color:Optional[str]=None
 shirt_size:Optional[str]=None
 shirt_quantity:int=Field(default=1,ge=1,le=100)
 buying_intent:bool=False
 upsell_status:str="not_offered"
 already_handed_off:bool=False
 customer_requested_no_offers:bool=False

class DecisionRequest(BaseModel):
 decision:str
 offer_id:Optional[str]=None
 upsell_status:str="offered"
 short_color:Optional[str]=None
 short_size:Optional[str]=None
 short_quantity:int=Field(default=1,ge=1,le=100)
 shirt_quantity:int=Field(default=1,ge=1,le=100)
 other_discounts_applied:bool=False

@router.get("/config")
def config():
 return {"upsell_product":"shorts-lino","price_bs":SHORT_UPSELL,
  "regular_price_bs":SHORT_REGULAR,"requires_henley_purchase":True,
  "shirts_price_bs":SHIRT_PRICE,"allowed_colors":SHORT_COLORS,
  "allowed_sizes":SHORT_SIZES,"discount_stacking_allowed":False,
  "required_user_fields":FIELDS,"offer_id":"henley-shorts-250-v1",
  "notes":"Tarifa comercial propuesta; verificar autorización, margen, stock real y Botcake antes del lanzamiento. No envía mensajes ni fotos."}

@router.post("/offer")
def offer(data:OfferRequest):
 eligible=(n(data.product) in ("henley","henley fosters")
  and data.buying_intent and bool(data.shirt_color) and data.shirt_size in ("M","L","XL")
  and n(data.upsell_status) in ("","not_offered","sin_dato")
  and not data.already_handed_off and not data.customer_requested_no_offers)
 if not eligible:
  return {"should_offer":False,"reason":"not_eligible_or_already_offered",
   "next_action":"continue_original_purchase","user_fields_to_set":{}}
 picks=suggested(data.shirt_color)
 return {"should_offer":True,"offer_id":"henley-shorts-250-v1",
  "regular_price_bs":SHORT_REGULAR,"upsell_price_bs":SHORT_UPSELL,
  "shirt_color":data.shirt_color,"recommended_short_colors":picks,
  "available_short_colors":SHORT_COLORS,"short_sizes":SHORT_SIZES,
  "send_short_photos":picks,"send_photos_once":True,
  "message":f"Querido, como llevás una Henley {data.shirt_color}, te puedo dejar nuestros nuevos shorts de lino a 250 Bs en vez de 270 Bs. {picks[0]} o {picks[1]} combinan muy bien. ¿Querés verlos?",
  "user_fields_to_set":{"fosters_upsell_estado":"offered",
                         "fosters_upsell_oferta_id":"henley-shorts-250-v1"},
  "next_action":"await_upsell_decision","do_not_handoff_yet":True}

@router.post("/decision")
def decision(data:DecisionRequest):
 action=n(data.decision)
 if n(data.upsell_status) in ("declined","completed"):
  return {"accepted":False,"next_action":"continue_original_purchase",
   "reason":"already_finalized","user_fields_to_set":{}}
 if action in ("no","rechazo","rechazar","declined","decline","paso"):
  return {"accepted":False,"next_action":"continue_original_purchase",
   "user_fields_to_set":{"fosters_upsell_estado":"declined"},
   "do_not_offer_again":True}
 if action not in ("si","acepto","aceptar","yes","accepted","accept"):
  return {"accepted":False,"next_action":"clarify_upsell_decision","user_fields_to_set":{}}
 if data.other_discounts_applied:
  return {"accepted":False,"next_action":"human_review_promotions",
   "reason":"non_stacking_promotion","user_fields_to_set":{}}
 color=selected_color(data.short_color)
 size=str(data.short_size or "").strip().upper()
 if not color or size not in SHORT_SIZES:
  missing=[]
  if not color:missing.append("short_color")
  if size not in SHORT_SIZES:missing.append("short_size")
  return {"accepted":True,"ready_for_total":False,
   "next_action":"ask_short_details","missing_fields":missing,
   "allowed_colors":SHORT_COLORS,"allowed_sizes":SHORT_SIZES,
   "user_fields_to_set":{"fosters_upsell_estado":"accepted"}}
 total=data.shirt_quantity*SHIRT_PRICE+data.short_quantity*SHORT_UPSELL
 return {"accepted":True,"ready_for_total":True,
  "shirt_subtotal_bs":data.shirt_quantity*SHIRT_PRICE,
  "short_subtotal_bs":data.short_quantity*SHORT_UPSELL,
  "total_bs":total,"upsell_unit_price_bs":SHORT_UPSELL,
  "short_item":{"product":"shorts-lino","color":color,"size":size,
                "quantity":data.short_quantity,"unit_price_bs":SHORT_UPSELL},
  "next_action":"continue_shipping_or_handoff",
  "user_fields_to_set":{"fosters_upsell_estado":"completed",
   "fosters_upsell_color":color,"fosters_upsell_talle":size,
   "fosters_upsell_cantidad":str(data.short_quantity),
   "fosters_upsell_oferta_id":"henley-shorts-250-v1"},
  "stock_verified":False,"order_created":False,
  "note":"No crear ni confirmar pedido desde esta skill. El humano valida variantes y total."}
