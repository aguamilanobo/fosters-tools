"""aguaMILANO standalone sales skills, only alpargatas. No POS or stock integration.
State stays in Botcake User Fields; these routes return suggested field updates.
"""
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional, List
import unicodedata

router = APIRouter(prefix="/agua/v2", tags=["aguaMILANO sales-only"])
PRICE = 300
COLORS = ["Beige", "Ocre", "Chocolate", "Verde", "Azul Marino"]
SIZES = {
 "40":{"foot_cm":25,"br":"38","us":"7"},
 "41":{"foot_cm":26,"br":"39.5","us":"8"},
 "42":{"foot_cm":27,"br":"40","us":"8.5"},
}
USER_FIELDS = ["agua_producto","agua_color","agua_talle","agua_cantidad","agua_ciudad","agua_nombre_completo","agua_ci","agua_ubicacion","agua_etapa","agua_derivado"]

def norm(v):
 x=unicodedata.normalize("NFKD",str(v or "").strip().lower())
 return "".join(c for c in x if not unicodedata.combining(c))
def color_of(raw):
 return next((c for c in COLORS if norm(c)==norm(raw)),None)
def size_of(raw):
 raw=str(raw or "").strip()
 return raw if raw in SIZES else None

class Lead(BaseModel):
 color:Optional[str]=None
 size:Optional[str]=None
 quantity:Optional[int]=1
 city:Optional[str]=None
 full_name:Optional[str]=None
 ci:Optional[str]=None
 location_shared:bool=False
 wants_to_buy:bool=False
 asks_for_human:bool=False
 asks_for_payment:bool=False
 has_complaint:bool=False

@router.get("/catalog")
def catalog():
 return {"product_key":"alpargata","name":"Alpargatas aguaMILANO",
         "price_bs":PRICE,"colors":COLORS,"sizes":SIZES,
         "stock_tracking":False,"stock_verified":False,
         "user_fields":USER_FIELDS,
         "note":"Bot comercial sin POS. Sin promesas de stock ni reservas."}

@router.get("/size")
def size(usual_size:Optional[str]=None,foot_cm:Optional[float]=None,us_size:Optional[str]=None,br_size:Optional[str]=None):
 matches=[]
 for eu,data in SIZES.items():
  if usual_size and str(usual_size).strip()==eu: matches.append(eu)
  if foot_cm is not None and abs(foot_cm-data["foot_cm"])<0.01: matches.append(eu)
  if us_size and norm(us_size)==norm(data["us"]): matches.append(eu)
  if br_size and norm(br_size)==norm(data["br"]): matches.append(eu)
 matches=list(dict.fromkeys(matches))
 if len(matches)==1:
  eu=matches[0]
  return {"recommended_size":eu,"equivalence":SIZES[eu],"confidence":"reference_only",
          "message":f"Según nuestra tabla, te corresponde el {eu}. ¿Qué color buscás?"}
 return {"recommended_size":None,"available_sizes":SIZES,
         "next_action":"ask_foot_measurement_or_handoff",
         "message":"Tenemos 40 (25 cm), 41 (26 cm) y 42 (27 cm). ¿Cuánto mide tu pie?"}

@router.post("/next-action")
def next_action(data:Lead):
 if data.asks_for_human or data.asks_for_payment or data.has_complaint:
  return {"next_action":"handoff","should_handoff":True,"reason":"customer_request"}
 if not data.wants_to_buy:
  return {"next_action":"show_catalog","should_handoff":False}
 if not color_of(data.color):
  return {"next_action":"ask_color","should_handoff":False,"available_colors":COLORS}
 if not size_of(data.size):
  return {"next_action":"ask_size","should_handoff":False,"available_sizes":list(SIZES)}
 if not data.city:
  return {"next_action":"ask_city","should_handoff":False}
 if "santa cruz" in norm(data.city) or norm(data.city)=="scz":
  if not data.location_shared:
   return {"next_action":"ask_location","should_handoff":False}
  return {"next_action":"handoff","should_handoff":True,"reason":"scz_location_received"}
 missing=[]
 if not data.full_name: missing.append("full_name")
 if not data.ci: missing.append("ci")
 if missing:
  return {"next_action":"ask_name_ci","missing_fields":missing,"should_handoff":False}
 return {"next_action":"handoff","should_handoff":True,"reason":"outside_scz_details_received"}

@router.post("/prepare-order")
def prepare_order(data:Lead):
 color=color_of(data.color);size=size_of(data.size)
 missing=[]
 if not color: missing.append("color")
 if not size: missing.append("size")
 qty=data.quantity if data.quantity and data.quantity>0 else 1
 if qty>100: return {"ready_to_order":False,"error":"quantity_requires_human_review"}
 return {"ready_to_order":not missing,"product_key":"alpargata",
         "product_name":"Alpargatas aguaMILANO","color":color,"size":size,
         "quantity":qty,"unit_price_bs":PRICE,"total_bs":PRICE*qty,
         "missing_fields":missing,"stock_checked":False,"stock_check_required":False,
         "payment_confirmed":False,"order_created":False,
         "user_fields_to_set":{"agua_producto":"alpargata",
                               **({"agua_color":color} if color else {}),
                               **({"agua_talle":size} if size else {}),
                               "agua_cantidad":str(qty)},
         "next_action":"ask_city" if not missing else "collect_missing_fields",
         "note":"Solo prepara datos para Botcake. No crea orden ni contacta POS."}

@router.post("/shipping")
def shipping(data:Lead):
 if not data.city:
  return {"next_action":"ask_city","should_handoff":False}
 if "santa cruz" in norm(data.city) or norm(data.city)=="scz":
  return {"next_action":"handoff" if data.location_shared else "ask_location",
          "should_handoff":data.location_shared,
          "missing_fields":[] if data.location_shared else ["location"]}
 missing=[k for k,v in (("full_name",data.full_name),("ci",data.ci)) if not v]
 return {"next_action":"ask_name_ci" if missing else "handoff",
         "should_handoff":not missing,"missing_fields":missing}
