"""Public Fosters catalog. Hidden legacy products are never returned by public routes.
Stock is NOT validated against Pancake POS and images require separate Botcake setup.
"""
from fastapi import APIRouter
from typing import Optional
import unicodedata

router=APIRouter()
SIZES=["M","L","XL"]
PRODUCTS={
 "henley":{
  "id":"henley","name":"Henley Fosters","price_bs":300,
  "material_label":"55% lino / 45% algodón","closure":"Tres botones en el pecho",
  "fit":"Classic fit amplio","status":"active",
  "colors":["Negro","Blanco","Azul","Celeste","Beige"],
  "sizes":SIZES,"inventory_status":"unverified","image_urls":{},
  "campaign_key":"henley",
  "availability_note":"Confirmar stock real por talle y color en Pancake POS."
 },
 "shorts-lino":{
  "id":"shorts-lino","name":"Shorts de lino Fosters","price_bs":300,
  "material_label":"Lino","status":"active",
  "colors":["Azul","Negro","Perla","Beige"],"sizes":SIZES,
  "measurements_cm":{
   "M":{"numeric_equivalent":"36 / 38","length":47,"width":33},
   "L":{"numeric_equivalent":"40 / 42","length":48,"width":35},
   "XL":{"numeric_equivalent":"44 / 46","length":49,"width":38}
  },
  "measurement_note":"Ancho y largo informados para la prenda; el punto exacto de medición del ancho no está confirmado.",
  "inventory_status":"unverified","image_urls":{},
  "campaign_key":"shorts-lino",
  "availability_note":"Confirmar stock real por talle y color en Pancake POS."
 }
}
# Preserved only for historic configuration/reference; NEVER presented to clients.
HIDDEN_PRODUCTS={
 "camisa-lino-brasilero":{
  "id":"camisa-lino-brasilero","name":"Camisa lino brasilero",
  "status":"hidden","price_bs":300,
  "colors":["Negro","Blanco","Celeste","Plomo","Beige"]
 }
}
COLOR_ALIASES={"negra":"Negro","negro":"Negro","blanca":"Blanco","blanco":"Blanco",
 "azul":"Azul","navy":"Azul","azul marino":"Azul","celeste":"Celeste",
 "beige":"Beige","crema":"Beige","arena":"Beige","perla":"Perla",
 "blanco perla":"Perla"}
def clean(value):
    x=unicodedata.normalize("NFKD",str(value or "").strip().lower())
    return "".join(ch for ch in x if not unicodedata.combining(ch))
def product_key(text):
    x=clean(text)
    if any(k in x for k in ("short","bermuda","pantalon corto")):
        return "shorts-lino"
    return "henley"
def card(key):
    p=PRODUCTS[key].copy()
    p["colors"]=list(p["colors"])
    p["sizes"]=list(p["sizes"])
    p["image_urls"]=dict(p["image_urls"])
    if "measurements_cm" in p:
        p["measurements_cm"]={k:dict(v) for k,v in p["measurements_cm"].items()}
    return p
def reply(key):
    if key=="shorts-lino":
        return "Hola querido, los shorts de lino Fosters están a 300 Bs. Tenemos azul, negro, perla y beige, en M, L y XL. ¿Qué talla y color buscás?"
    return "Hola querido, las Henley Fosters están a 300 Bs. Tenemos negro, blanco, azul, celeste y beige, en M, L y XL. ¿Qué talle y color buscás?"
@router.get("/fosters/products")
def products():
    return {"primary_product":"henley","products":[card("henley"),card("shorts-lino")],
        "stock_is_verified":False}
@router.get("/fosters/product")
def product(product:Optional[str]=None,color:Optional[str]=None):
    key=product_key(product or "")
    p=card(key)
    if color:
        selected=COLOR_ALIASES.get(clean(color))
        if selected not in p["colors"]:
            return {"found":False,"reason":"color_not_offered","product_id":key,
                    "available_colors":p["colors"]}
        p["selected_color"]=selected
    return {"found":True,"product":p,"suggested_reply":reply(key)}
@router.get("/fosters/campaign-reply")
def campaign_reply(product:Optional[str]=None):
    key=product_key(product or "")
    return {"campaign_key":PRODUCTS[key]["campaign_key"],"product_id":key,
     "status":"active","suggested_reply":reply(key),
     "manual_botcake_flow_setup_required":True,
     "note":"Configurar anuncios y fotos reales en Botcake; el endpoint no modifica automatizaciones."}
