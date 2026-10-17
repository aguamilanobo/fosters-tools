"""FOSTERS product source of truth for website/API/Botcake flows.
Inventory here is NOT confirmed POS stock. No product images invented.
"""
from fastapi import APIRouter
from typing import Optional
import os, unicodedata

router=APIRouter()
SHARED_SIZES=["M","L","XL"]
COLORS=["Negro","Blanco","Celeste","Plomo","Beige"]
ALIASES={"negra":"Negro","negro":"Negro","blanca":"Blanco","blanco":"Blanco","azul":"Azul","navy":"Azul","azul marino":"Azul","celeste":"Celeste","plomo":"Plomo","gris":"Plomo","gris plomo":"Plomo","beige":"Beige","arena":"Beige","crema":"Beige"}
SIZE_REFERENCE={"M":"65–77 kg aprox.","L":"78–87 kg aprox.","XL":"87–110 kg aprox."}
PRODUCTS={
 "camisa-lino-brasilero":{
  "id":"camisa-lino-brasilero","name":"Camisa Fosters de lino brasilero",
  "material_label":"Lino brasilero","composition_certified":False,
  "closure":"Abotonadura completa, botones a lo largo del frente",
  "price_bs":300,"status":"active","colors":COLORS,"sizes":SHARED_SIZES,
  "inventory_status":"unverified","image_urls":{},
  "fit":"Misma horma y guía de tallas que la Henley anterior",
  "campaign_key":"lino-brasilero",
  "availability_note":"Colores anunciados; validar stock real y talles en Pancake antes de confirmar."
 },
 "henley":{
  "id":"henley","name":"Henley Fosters","material_label":"55% lino / 45% algodón",
  "closure":"Tres botones en el pecho",
  "price_bs":300,"status":"active","colors":["Negro","Blanco","Azul","Celeste","Beige"],
  "sizes":SHARED_SIZES,"inventory_status":"unverified","image_urls":{},
  "fit":"Horma clásica amplia","campaign_key":"henley",
  "availability_note":"Modelo reactivado; confirmar existencias por color y talle en Pancake antes de prometer stock."
 }
}
REMOVED_COLORS=["Verde","Marrón"]
def clean(value):
    s=unicodedata.normalize("NFKD",(value or "").strip().lower())
    return "".join(ch for ch in s if not unicodedata.combining(ch))
def product_key(text):
    x=clean(text)
    if x in ("lino_brasilero","lino-brasilero","camisa-lino-brasilero"): return "camisa-lino-brasilero"
    if any(k in x for k in ("henley","tres botones","3 botones")): return "henley"
    if any(k in x for k in ("brasilero","brasilera","botones completos","abotonadura completa","camisa","plomo")):return "camisa-lino-brasilero"
    return "camisa-lino-brasilero"
def card(key):
    p=PRODUCTS[key].copy()
    p["image_urls"]=dict(p["image_urls"])
    return p
def reply(key):
    p=PRODUCTS[key]
    if key=="henley":
        return "¡Hola! Las Henley Fosters cuestan 300 Bs. Son de lino y algodón, con tres botones en el pecho. Colores negro, blanco, azul marino, celeste y beige. ¿Qué talle y color buscás?"
    return "¡Hola! Nuestra nueva camisa Fosters de lino brasilero cuesta 300 Bs. Tiene botones en todo el frente y viene en negro, blanco, celeste, plomo y beige. Talles M, L y XL como referencia habitual (consultar stock por variante). ¿Qué talla y color buscás?"
@router.get("/fosters/products")
def products():
    return {"primary_product":"camisa-lino-brasilero","products":[card("camisa-lino-brasilero"),card("henley")],
      "removed_colors":REMOVED_COLORS,"stock_is_verified":False}
@router.get("/fosters/product")
def product(product:Optional[str]=None,color:Optional[str]=None):
    key=product_key(product or "")
    p=card(key)
    if color:
        normalized=ALIASES.get(clean(color))
        if normalized is None or normalized not in p["colors"]:
            return {"found":False,"reason":"color_not_offered","available_colors":p["colors"],"removed_colors":REMOVED_COLORS}
        p["selected_color"]=normalized
    return {"found":True,"product":p,"suggested_reply":reply(key)}
@router.get("/fosters/campaign-reply")
def campaign_reply(product:Optional[str]=None):
    key=product_key(product or "")
    return {"campaign_key":PRODUCTS[key]["campaign_key"],"product_id":key,
      "status":PRODUCTS[key]["status"],"suggested_reply":reply(key),
      "manual_botcake_flow_setup_required":True,
      "note":"El anuncio y sus fotos deben configurarse en Meta/Botcake; este endpoint no cambia los flujos de Botcake."}
