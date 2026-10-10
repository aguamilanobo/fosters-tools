"""Operational extensions for Fosters Dispatch. All actions require an authorized Telegram Mini App or admin key."""
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from typing import Optional
from urllib import request as ur,parse as up,error as ue
from pathlib import Path
import os, json, re, time, secrets, sqlite3, hashlib
from dispatch import authorized, db, audit, parse_ticket, DATA_DIR, ADMIN_KEY

router=APIRouter()
def own(ticket_id):
    with db() as conn:
        row=conn.execute("SELECT * FROM tickets WHERE id=?",(ticket_id,)).fetchone()
    if not row: raise HTTPException(404,"Ticket inexistente")
    return dict(row)

def number(text):
    digits=re.sub("[^0-9]","",str(text or ""))
    if not 8<=len(digits)<=15: raise HTTPException(400,"Teléfono inválido")
    return digits

def botcake(psid):
    token=os.getenv("DISPATCH_BOTCAKE_TOKEN","").strip()
    page=os.getenv("DISPATCH_BOTCAKE_PAGE_ID","").strip()
    if not token or not re.fullmatch("[A-Za-z0-9_-]{5,100}",page):
        raise HTTPException(503,"Falta configuración de Botcake")
    if not re.fullmatch("wa_[0-9]{8,15}",psid):
        raise HTTPException(400,"Identificador inválido")
    url="https://botcake.io/api/public_api/v1/pages/"+page+"/customer/"+psid
    req=ur.Request(url,headers={"access-token":token,"Accept":"application/json"},method="GET")
    try:
        with ur.urlopen(req,timeout=20) as res:
            data=json.loads(res.read(400000))
    except ue.HTTPError as ex:
        raise HTTPException(502,"Botcake devolvió HTTP "+str(ex.code))
    except Exception as ex:
        print("[DISPATCH] botcake history error",type(ex).__name__)
        raise HTTPException(502,"Error consultando Botcake")
    if not isinstance(data,dict) or data.get("success") is not True:
        raise HTTPException(502,"Botcake no reconoció la consulta")
    return {"history_count":len(data["histories"]) if isinstance(data.get("histories"),list) else None,"psid":psid}

class MatchInput(BaseModel):
    phone: Optional[str]=None
class ConfirmInput(BaseModel):
    phone: str
    recipient_name: str
    order_ref: str
    note: Optional[str]=None

@router.post("/dispatch/ops/lookup/{ticket_id}")
async def lookup(ticket_id:int,request:Request,payload:MatchInput):
    actor=authorized(request)
    t=own(ticket_id)
    info=json.loads(t["extracted"])
    phone=number(payload.phone or info.get("phone"))
    candidate="wa_"+phone
    result=botcake(candidate)
    with db() as conn:
        audit(conn,ticket_id,"candidate_lookup",actor,{"psid_digest":hashlib.sha256(candidate.encode()).hexdigest()[:16]})
    return {"candidate_psid":candidate,"history_entries":result["history_count"],
       "identity_verified":False,"note":"La existencia del historial NO verifica el nombre, teléfono ni pedido. Confirmar manualmente."}

@router.post("/dispatch/ops/confirm/{ticket_id}")
async def confirm(ticket_id:int,request:Request,payload:ConfirmInput):
    actor=authorized(request)
    t=own(ticket_id)
    if t["message_status"]!="not_sent":
        raise HTTPException(409,"Ticket con estado de envío previo")
    if not payload.recipient_name.strip() or not payload.order_ref.strip():
        raise HTTPException(400,"Confirmar nombre y referencia de pedido")
    phone=number(payload.phone)
    psid="wa_"+phone
    botcake(psid)
    verified={"recipient_name":payload.recipient_name.strip(),
              "phone":phone,"order_ref":payload.order_ref.strip(),
              "psid":psid,"note":(payload.note or "")[:500]}
    with db() as conn:
        conn.execute("UPDATE tickets SET verified=?, matched_order=?, reviewer_id=?, reviewed_at=?, status='approved_not_sent' WHERE id=?",
         (json.dumps(verified,ensure_ascii=False),verified["order_ref"],actor,int(time.time()),ticket_id))
        audit(conn,ticket_id,"approved_with_psid",actor,
              {"phone_last4":phone[-4:],"order_ref":verified["order_ref"]})
    return {"status":"approved_not_sent","psid":psid,"sent":False}

@router.post("/dispatch/ops/audit/{ticket_id}")
async def ticket_audit(ticket_id:int,request:Request):
    authorized(request)
    own(ticket_id)
    with db() as conn:
        rows=conn.execute("SELECT action,actor,created_at FROM audit WHERE ticket_id=? ORDER BY id DESC LIMIT 30",(ticket_id,)).fetchall()
    return {"history":[dict(x) for x in rows]}

@router.post("/dispatch/ops/retry-vision/{ticket_id}")
async def retry_vision(ticket_id:int,request:Request):
    actor=authorized(request)
    t=own(ticket_id)
    if t["status"] in ("approved_not_sent","sent","sending"):
        raise HTTPException(409,"No se permite reprocesar tickets aprobados o enviados")
    ext={"image/jpeg":".jpg","image/png":".png","image/webp":".webp"}.get(t["mime_type"])
    path=DATA_DIR/(str(ticket_id)+(ext or ""))
    if not path.is_file():raise HTTPException(410,"La foto se perdió del almacenamiento. Configurá un disco persistente.")
    with db() as conn:
        changed=conn.execute("UPDATE tickets SET status='processing' WHERE id=? AND status!='processing'",(ticket_id,))
        if not changed.rowcount:raise HTTPException(409,"Procesamiento ya en curso")
        audit(conn,ticket_id,"vision_retry",actor)
    parsed,error=parse_ticket(path.read_bytes(),t["mime_type"])
    with db() as conn:
        conn.execute("UPDATE tickets SET extracted=?,error=?,status=? WHERE id=?",
            (json.dumps(parsed,ensure_ascii=False),error,
             "needs_review" if not error else "needs_extraction",ticket_id))
    return {"ok":not bool(error),"status":"needs_review" if not error else "needs_extraction",
            "error":error,"extracted":parsed}

@router.post("/dispatch/ops/health")
async def ops_health(request:Request):
    authorized(request)
    marker=DATA_DIR/(".health-"+secrets.token_hex(5))
    try:
        marker.write_text("ok")
        marker.unlink()
        storage_writable=True
    except Exception:storage_writable=False
    with db() as conn:
        status=[dict(r) for r in conn.execute("SELECT status,count(*) AS count FROM tickets GROUP BY status")]
    path=str(DATA_DIR)
    is_ephemeral=(path.startswith("/tmp/") or path=="/tmp")
    return {"storage_writable":storage_writable,
           "ephemeral_storage":is_ephemeral,
           "persistent_storage_verified":False,
           "data_directory":path,
           "send_enabled":False,
           "counts":status,
           "note":"Persistencia no verificada: no cargar comprobantes reales hasta configurar disco o storage externo."}

@router.post("/dispatch/ops/summary")
async def ops_summary(request:Request):
    authorized(request)
    with db() as conn:
        rows=conn.execute("SELECT id,status,message_status,extracted,verified,created_at FROM tickets ORDER BY id DESC LIMIT 100").fetchall()
    items=[]
    for r in rows:
        ex=json.loads(r["extracted"])
        ve=json.loads(r["verified"])
        items.append({"id":r["id"],"status":r["status"],"message_status":r["message_status"],
           "name":ve.get("recipient_name") or ex.get("recipient_name"),
           "phone_last4":str(ve.get("phone") or ex.get("phone") or "")[-4:],
           "carrier":ex.get("carrier"),"created_at":r["created_at"]})
    return {"tickets":items,"send_enabled":False}
