"""Controlled Botcake media send: test-only, explicit operator confirmation, one attempt per approval."""
import os, re, json, time, secrets, sqlite3
from urllib import request as ur, error as ue
from fastapi import APIRouter, Request, HTTPException
from pydantic import BaseModel
from dispatch import db, authorized, audit

router=APIRouter()

def setup(conn):
    conn.execute("""CREATE TABLE IF NOT EXISTS dispatch_send_tests(
     id TEXT PRIMARY KEY, recipient_psid TEXT NOT NULL, image_url TEXT NOT NULL,
     created_at INTEGER NOT NULL, expires_at INTEGER NOT NULL,
     approved_by TEXT NOT NULL, status TEXT NOT NULL,
     provider_result TEXT, attempted_at INTEGER)""")

def config():
    number=re.sub("[^0-9]","",os.getenv("DISPATCH_TEST_WHATSAPP",""))
    media_url=os.getenv("DISPATCH_TEST_IMAGE_URL","").strip()
    page=os.getenv("DISPATCH_BOTCAKE_PAGE_ID","").strip()
    token=os.getenv("DISPATCH_BOTCAKE_TOKEN","").strip()
    if not (8<=len(number)<=15 and media_url.startswith("https://")
        and re.fullmatch("[a-zA-Z0-9_-]{5,100}",page or "") and token):
        raise HTTPException(503,"Faltan DISPATCH_TEST_WHATSAPP, DISPATCH_TEST_IMAGE_URL o credenciales Botcake")
    if len(media_url)>1000 or "#" in media_url or "@" in media_url or "?" in media_url:
        raise HTTPException(400,"Usá URL HTTPS pública, sin parámetros, credenciales ni fragmentos")
    return "wa_"+number,media_url,page,token

@router.post("/dispatch/test-send/prepare")
async def prepare(request:Request):
    actor=authorized(request)
    psid,url,_,_=config()
    test_id=secrets.token_urlsafe(24)
    now=int(time.time())
    with db() as conn:
        setup(conn)
        conn.execute("INSERT INTO dispatch_send_tests(id,recipient_psid,image_url,created_at,expires_at,approved_by,status) VALUES(?,?,?,?,?,?,?)",
          (test_id,psid,url,now,now+300,actor,"prepared"))
        audit(conn,None,"test_send_prepared",actor,{"recipient_last4":psid[-4:]})
    return {"approval_id":test_id,"expires_seconds":300,"recipient_last4":psid[-4:],
       "image_url":url,"message_type":"image","send_mode":"one_test_only",
       "warning":"Revisá que este sea TU WhatsApp y que la imagen sea ficticia. Confirmar ejecutará UN envío real."}

class Confirm(BaseModel):
    approval_id:str
    consent_phrase:str

@router.post("/dispatch/test-send/execute")
async def execute(request:Request,payload:Confirm):
    actor=authorized(request)
    if payload.consent_phrase!="ENVIAR PRUEBA A MI WHATSAPP":
        raise HTTPException(400,"Confirmación explícita incorrecta")
    psid,url,page,token=config()
    now=int(time.time())
    with db() as conn:
        setup(conn)
        conn.execute("BEGIN IMMEDIATE")
        row=conn.execute("SELECT * FROM dispatch_send_tests WHERE id=?",(payload.approval_id,)).fetchone()
        if not row or row["approved_by"]!=actor or row["status"]!="prepared" or row["expires_at"]<now:
            raise HTTPException(409,"Aprobación inexistente, expirada o ya utilizada")
        if row["recipient_psid"]!=psid or row["image_url"]!=url:
            raise HTTPException(409,"Cambió la configuración; prepará otra prueba")
        conn.execute("UPDATE dispatch_send_tests SET status='attempted',attempted_at=? WHERE id=?",(now,payload.approval_id))
        audit(conn,None,"test_send_attempted",actor,{"recipient_last4":psid[-4:]})
    endpoint="https://botcake.io/api/public_api/v1/pages/"+page+"/flows/send_content"
    post={"psid":psid,"data":{"version":"v2","content":{"messages":[{"type":"image","url":url}],"actions":[],"quick_replies":[]}}}
    req=ur.Request(endpoint,data=json.dumps(post).encode(),method="POST",
       headers={"access-token":token,"Content-Type":"application/json","Accept":"application/json"})
    outcome="unknown"
    details={"ok":False,"status":"unknown","message":"Envío intentado; comprobá WhatsApp antes de reintentar."}
    try:
        with ur.urlopen(req,timeout=25) as resp:
            answer=json.loads(resp.read(128000))
            outcome="accepted" if isinstance(answer,dict) and answer.get("success") is True else "rejected"
            details={"ok":outcome=="accepted","status":outcome,
              "provider_success":answer.get("success") if isinstance(answer,dict) else None,
              "provider_code":str(answer.get("error_code"))[:40] if isinstance(answer,dict) and answer.get("error_code") else None,
              "message":"Botcake aceptó la solicitud; verificá recepción en WhatsApp." if outcome=="accepted" else "Botcake no confirmó el envío. No reintentes hasta verificar WhatsApp."}
    except ue.HTTPError as exc:
        outcome="rejected"
        details={"ok":False,"status":outcome,"http_status":exc.code,
          "message":"Botcake respondió error. No reintentes sin comprobar WhatsApp."}
    except Exception as exc:
        print("[DISPATCH] send test ambiguous:",type(exc).__name__)
    with db() as conn:
        conn.execute("UPDATE dispatch_send_tests SET status=?,provider_result=? WHERE id=?",
            (outcome,json.dumps(details),payload.approval_id))
        audit(conn,None,"test_send_completed",actor,{"outcome":outcome})
    return details

@router.post("/dispatch/test-send/status")
async def status(request:Request):
    authorized(request)
    with db() as conn:
        setup(conn)
        row=conn.execute("SELECT status,created_at,attempted_at FROM dispatch_send_tests ORDER BY created_at DESC LIMIT 1").fetchone()
    return {"latest_test":dict(row) if row else None,"bulk_send_enabled":False,"real_ticket_send_enabled":False}
