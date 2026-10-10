"""Fosters Dispatch: secure receipt intake, vision extraction and human review.
No customer messages are sent by this module.
"""
from fastapi import APIRouter, Request, HTTPException, Header
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from typing import Optional
from urllib import request as urlreq, parse as urlparse
from pathlib import Path
import os, json, sqlite3, hashlib, hmac, time, base64, secrets, mimetypes, re

router = APIRouter()
DATA_DIR = Path(os.getenv("DISPATCH_DATA_DIR", "/tmp/fosters-dispatch"))
DATA_DIR.mkdir(parents=True, exist_ok=True)
DB_PATH = DATA_DIR / "dispatch.sqlite3"
BOT_TOKEN = lambda: os.getenv("DISPATCH_TELEGRAM_BOT_TOKEN", "")
ADMIN_KEY = lambda: os.getenv("DISPATCH_ADMIN_KEY", "")
MAX_IMAGE = 12 * 1024 * 1024


def db():
    connection = sqlite3.connect(str(DB_PATH), timeout=10)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA journal_mode=WAL")
    connection.execute("""CREATE TABLE IF NOT EXISTS tickets (
        id INTEGER PRIMARY KEY AUTOINCREMENT, created_at INTEGER NOT NULL,
        source TEXT NOT NULL, chat_id TEXT, telegram_file_id TEXT,
        filename TEXT, mime_type TEXT, sha256 TEXT UNIQUE,
        status TEXT NOT NULL, extracted TEXT NOT NULL DEFAULT '{}',
        verified TEXT NOT NULL DEFAULT '{}', matched_order TEXT,
        reviewer_id TEXT, reviewed_at INTEGER, message_status TEXT NOT NULL DEFAULT 'not_sent',
        error TEXT
    )""")
    connection.execute("""CREATE TABLE IF NOT EXISTS audit (
        id INTEGER PRIMARY KEY AUTOINCREMENT, ticket_id INTEGER, action TEXT NOT NULL,
        actor TEXT NOT NULL, created_at INTEGER NOT NULL, details TEXT
    )""")
    connection.execute("""CREATE TABLE IF NOT EXISTS contacts (
        id TEXT PRIMARY KEY, name TEXT NOT NULL, phone TEXT, city TEXT,
        brand TEXT, order_ref TEXT, updated_at INTEGER NOT NULL
    )""")
    connection.commit()
    return connection


def admin(request: Request):
    expected = ADMIN_KEY()
    provided = request.headers.get("x-dispatch-admin-key", "")
    if not expected or not provided or not hmac.compare_digest(provided, expected):
        raise HTTPException(403, "Acceso no autorizado.")


def tg(method, payload):
    if not BOT_TOKEN():
        raise RuntimeError("Falta DISPATCH_TELEGRAM_BOT_TOKEN")
    req = urlreq.Request(
        "https://api.telegram.org/bot" + BOT_TOKEN() + "/" + method,
        data=json.dumps(payload).encode(), headers={"Content-Type": "application/json"},
        method="POST")
    with urlreq.urlopen(req, timeout=20) as resp:
        result = json.load(resp)
    if not result.get("ok"):
        raise RuntimeError("Telegram respondió con error")
    return result.get("result")


def tg_message(chat_id, text):
    try:
        tg("sendMessage", {"chat_id": chat_id, "text": text[:3500]})
    except Exception as ex:
        print("[DISPATCH] No se pudo responder por Telegram:", type(ex).__name__)


def audit(conn, ticket_id, action, actor, details=None):
    conn.execute("INSERT INTO audit(ticket_id,action,actor,created_at,details) VALUES(?,?,?,?,?)",
                 (ticket_id, action, str(actor), int(time.time()), json.dumps(details or {}, ensure_ascii=False)))


def parse_ticket(image_bytes, mime):
    api_key = os.getenv("OPENAI_API_KEY", "")
    if not api_key:
        return {}, "vision_not_configured"
    prompt = (
      "Lee este comprobante de transporte boliviano. Extrae EXCLUSIVAMENTE datos visibles. "
      "No inventes ni completes valores. Responde SOLO JSON con: "
      "recipient_name, phone, ci, destination, carrier, tracking_number, sender, shipment_date. "
      "Usa null si no se distingue o no aparece. Distingue remitente de destinatario."
    )
    payload = {
      "model": os.getenv("DISPATCH_VISION_MODEL", "gpt-4.1-mini"),
      "messages": [{"role":"user","content":[{"type":"text","text":prompt},
        {"type":"image_url","image_url":{"url":"data:"+mime+";base64,"+base64.b64encode(image_bytes).decode()}}]}],
      "response_format":{"type":"json_object"}, "max_tokens":500
    }
    req = urlreq.Request("https://api.openai.com/v1/chat/completions",
      data=json.dumps(payload).encode(), method="POST",
      headers={"Authorization":"Bearer "+api_key, "Content-Type":"application/json"})
    try:
        with urlreq.urlopen(req, timeout=55) as resp:
            response = json.load(resp)
        parsed = json.loads(response["choices"][0]["message"]["content"])
        allowed = ("recipient_name","phone","ci","destination","carrier","tracking_number","sender","shipment_date")
        return {k: parsed.get(k) for k in allowed}, None
    except Exception as ex:
        print("[DISPATCH] Vision error:", type(ex).__name__)
        return {}, "vision_failed"


def read_telegram_file(file_id):
    info = tg("getFile", {"file_id":file_id})
    path = info.get("file_path", "")
    if not path:
        raise ValueError("Telegram no entregó ruta")
    if info.get("file_size", 0) > MAX_IMAGE:
        raise ValueError("Imagen demasiado grande")
    url = "https://api.telegram.org/file/bot" + BOT_TOKEN() + "/" + path
    with urlreq.urlopen(url, timeout=25) as resp:
        binary = resp.read(MAX_IMAGE + 1)
    if len(binary) > MAX_IMAGE: raise ValueError("Imagen demasiado grande")
    return binary


def ingest(raw, source, file_id=None, chat_id=None, filename=None):
    if not raw or len(raw)>MAX_IMAGE: raise ValueError("Imagen vacía o demasiado grande")
    if raw.startswith(b"\xff\xd8\xff"):
        mime, ext = "image/jpeg", ".jpg"
    elif raw.startswith(b"\x89PNG\r\n\x1a\n"):
        mime, ext = "image/png", ".png"
    elif raw.startswith(b"RIFF") and raw[8:12] == b"WEBP":
        mime, ext = "image/webp", ".webp"
    else: raise ValueError("Formato de imagen no admitido")
    digest = hashlib.sha256(raw).hexdigest()
    with db() as conn:
        previous=conn.execute("SELECT id FROM tickets WHERE sha256=?", (digest,)).fetchone()
        if previous: return int(previous["id"]), True
        now = int(time.time())
        cur=conn.execute("""INSERT INTO tickets
          (created_at,source,chat_id,telegram_file_id,filename,mime_type,sha256,status)
          VALUES(?,?,?,?,?,?,?,?)""",
          (now,source,str(chat_id) if chat_id else None,file_id,filename,mime,digest,"processing"))
        ticket_id = cur.lastrowid
        audit(conn,ticket_id,"received",source)
    (DATA_DIR / (str(ticket_id)+ext)).write_bytes(raw)
    extracted, error = parse_ticket(raw, mime)
    with db() as conn:
        conn.execute("UPDATE tickets SET status=?, extracted=?,error=? WHERE id=?",
          ("needs_review" if not error else "needs_extraction",
           json.dumps(extracted,ensure_ascii=False),error,ticket_id))
        audit(conn,ticket_id,"extracted" if not error else "extraction_pending","system",{"error":error})
    return ticket_id, False


def verify_telegram(init_data):
    params=dict(urlparse.parse_qsl(init_data,keep_blank_values=True))
    signature=params.pop("hash",None)
    if not signature or not BOT_TOKEN(): raise HTTPException(401,"Abrí desde Telegram.")
    check="\n".join(k+"="+params[k] for k in sorted(params))
    secret=hmac.new(b"WebAppData",BOT_TOKEN().encode(),hashlib.sha256).digest()
    candidate=hmac.new(secret,check.encode(),hashlib.sha256).hexdigest()
    if not hmac.compare_digest(signature,candidate): raise HTTPException(403,"Firma inválida.")
    try:
        user=json.loads(params["user"])
        if abs(time.time()-int(params["auth_date"])) > 86400: raise ValueError()
    except Exception: raise HTTPException(401,"Sesión expirada.")
    allowed={part.strip() for part in os.getenv("DISPATCH_ALLOWED_USER_IDS","").split(",") if part.strip()}
    if not allowed or str(user.get("id")) not in allowed:
        raise HTTPException(403,"Usuario no autorizado.")
    return str(user["id"])


def authorized(request):
    key = request.headers.get("x-dispatch-admin-key","")
    if ADMIN_KEY() and key and hmac.compare_digest(key,ADMIN_KEY()):
        return "admin"
    return verify_telegram(request.headers.get("x-telegram-init-data",""))


@router.post("/dispatch/telegram/webhook")
async def telegram_webhook(request:Request):
    expected=os.getenv("DISPATCH_TELEGRAM_WEBHOOK_SECRET","")
    provided=request.headers.get("x-telegram-bot-api-secret-token","")
    if not expected or not hmac.compare_digest(expected,provided):
        raise HTTPException(403,"Webhook no autorizado")
    event=await request.json()
    msg=event.get("message") or event.get("channel_post") or {}
    chat=msg.get("chat") or {}
    chat_id=chat.get("id")
    user=(msg.get("from") or {}).get("id")
    allowed={x.strip() for x in os.getenv("DISPATCH_ALLOWED_USER_IDS","").split(",") if x.strip()}
    if str(user) not in allowed: return {"ok":True,"ignored":"unauthorized_sender"}
    allowed_chat=os.getenv("DISPATCH_TELEGRAM_CHAT_ID","")
    if allowed_chat and str(chat_id)!=allowed_chat: return {"ok":True,"ignored":"wrong_chat"}
    if not (msg.get("photo") or msg.get("document")):
        if (msg.get("text") or "").startswith("/start"):
            tg_message(chat_id,"Fosters Dispatch listo. Mandame fotos de tickets y revisalos en el panel de Telegram.")
        return {"ok":True}
    photo=msg.get("photo") or []
    doc=msg.get("document") or {}
    if photo:
        file_id=photo[-1]["file_id"]
    elif str(doc.get("mime_type","")).startswith("image/"):
        file_id=doc.get("file_id")
    else:
        tg_message(chat_id,"Mandame una foto o una imagen como archivo.")
        return {"ok":True}
    try:
        raw=read_telegram_file(file_id)
        ticket_id,duplicate=ingest(raw,"telegram",file_id=file_id,chat_id=chat_id)
        tg_message(chat_id,("Ya estaba cargado" if duplicate else "Ticket recibido")+" #"+str(ticket_id)+". Revisalo en el Panel Dispatch antes de enviarlo.")
    except Exception as ex:
        tg_message(chat_id,"No pude procesar la imagen. Revisá formato y tamaño.")
        print("[DISPATCH] Ticket error:",type(ex).__name__)
    return {"ok":True}


class DispatchTicketReview(BaseModel):
    recipient_name: Optional[str]=None
    phone: Optional[str]=None
    ci: Optional[str]=None
    destination: Optional[str]=None
    carrier: Optional[str]=None
    tracking_number: Optional[str]=None
    matched_order: Optional[str]=None


@router.post("/dispatch/api/list")
async def tickets_list(request:Request):
    authorized(request)
    with db() as conn:
        rows=conn.execute("""SELECT id,created_at,source,status,extracted,verified,matched_order,
                        reviewer_id,reviewed_at,message_status,error
                        FROM tickets ORDER BY id DESC LIMIT 100""").fetchall()
    return {"tickets":[{**dict(r),"extracted":json.loads(r["extracted"]),
      "verified":json.loads(r["verified"])} for r in rows],
      "send_enabled":False, "mode":"review_only"}


@router.post("/dispatch/api/review/{ticket_id}")
async def ticket_review(ticket_id:int,request:Request,payload:DispatchTicketReview):
    actor=authorized(request)
    with db() as conn:
        row=conn.execute("SELECT id FROM tickets WHERE id=?", (ticket_id,)).fetchone()
        if not row: raise HTTPException(404,"Ticket inexistente")
        values=payload.dict(exclude_none=True)
        if not values.get("recipient_name") or not values.get("matched_order"):
            raise HTTPException(400,"Debés confirmar destinatario y referencia del pedido.")
        conn.execute("""UPDATE tickets SET verified=?,matched_order=?,reviewer_id=?,reviewed_at=?,
                        status='approved_not_sent' WHERE id=?""",
                     (json.dumps(values,ensure_ascii=False),values["matched_order"],actor,int(time.time()),ticket_id))
        audit(conn,ticket_id,"review_approved",actor,values)
    return {"ok":True,"status":"approved_not_sent","sent":False}


@router.post("/dispatch/api/send/{ticket_id}")
async def ticket_send(ticket_id:int,request:Request):
    authorized(request)
    raise HTTPException(501, "Envío deshabilitado hasta verificar y conectar la API de Pancake/WhatsApp.")


@router.post("/dispatch/admin/setup")
async def setup(request:Request):
    admin(request)
    if not BOT_TOKEN() or not os.getenv("DISPATCH_TELEGRAM_WEBHOOK_SECRET"):
        raise HTTPException(503,"Faltan variables de Telegram.")
    base=os.getenv("DISPATCH_PUBLIC_URL","https://fosters-tools.onrender.com").rstrip("/")
    result=tg("setWebhook",{"url":base+"/dispatch/telegram/webhook",
       "secret_token":os.getenv("DISPATCH_TELEGRAM_WEBHOOK_SECRET"),
       "allowed_updates":["message"]})
    return {"ok":bool(result),"webhook_url":base+"/dispatch/telegram/webhook"}


@router.get("/dispatch",response_class=HTMLResponse)
def dashboard():
    return """<!DOCTYPE html><html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
    <title>Fosters Dispatch</title><script src="https://telegram.org/js/telegram-web-app.js"></script>
    <style>body{background:#0b0b0b;color:#f3f1ea;font:15px Arial;margin:0}.wrap{max-width:760px;margin:auto;padding:22px}h1{font:24px Georgia;letter-spacing:2px}.card{background:#191919;border:1px solid #333;border-radius:14px;padding:18px;margin:12px 0}input{background:#111;color:white;border:1px solid #555;border-radius:6px;padding:10px;width:100%;box-sizing:border-box;margin:4px 0 12px}button{background:#f0eede;color:#111;border:0;border-radius:8px;padding:11px 15px;font-weight:bold}.muted{color:#aaa}.alert{color:#edbe75}.err{color:#fa9999}small{color:#aaa}</style></head>
    <body><div class="wrap"><h1>FOSTERS DISPATCH</h1><p class="alert">Modo seguro · revisión manual · envío WhatsApp todavía deshabilitado</p>
    <button onclick="checkPancake()">Comprobar conexión Pancake</button> <button onclick="checkBotcake()">Probar conexión Botcake</button> <button onclick="testContact()">Probar contacto propio</button> <button onclick="checkBearer()">Probar token Bearer</button><p id="pancakeResult" class="muted"></p><button onclick="health()">Estado del sistema</button> <button onclick="prepareTestSend()">Preparar envío de prueba</button><p id="testSendStatus" class="muted"></p><p id="health"></p><div id="list">Cargando tickets…</div><p id="msg"></p></div>
    <script>
    const tg=window.Telegram&&Telegram.WebApp;if(tg){tg.ready();tg.expand()}
    const auth=tg?tg.initData:'';
    function esc(v){return String(v==null?'':v).replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]))}
    async function api(path,body){const r=await fetch(path,{method:'POST',headers:{'Content-Type':'application/json','X-Telegram-Init-Data':auth},body:JSON.stringify(body||{})});const j=await r.json();if(!r.ok)throw Error(j.detail||'Error');return j}
    async function load(){try{const res=await api('/dispatch/api/list');document.getElementById('list').innerHTML=res.tickets.map(t=>{const x=Object.assign({},t.extracted,t.verified);return '<div class="card"><b>#'+t.id+' · '+esc(t.status)+'</b><p class="muted">Ticket recibido '+new Date(t.created_at*1000).toLocaleString()+'</p>'+['recipient_name','phone','destination','carrier','tracking_number','matched_order'].map(k=>'<label><small>'+k+'</small><input data-id="'+t.id+'" data-field="'+k+'" value="'+esc(k==='matched_order'?t.matched_order:x[k])+'"></label>').join('')+'<button onclick="findClient('+t.id+')">Buscar en Botcake</button> <button onclick="approveSafe('+t.id+')">Confirmar cliente y pedido</button> <button onclick="retryTicket('+t.id+')">Releer foto con IA</button> <button onclick="previewTicket('+t.id+')">Ver foto</button><p id="ticket-'+t.id+'" class="muted"></p></div>'}).join('')||'<p>No hay tickets. Enviá fotos al bot.</p>'}catch(e){document.getElementById('msg').textContent=e.message}}
    async function approve(id){const p={};document.querySelectorAll('[data-id="'+id+'"]').forEach(el=>p[el.dataset.field]=el.value);try{await api('/dispatch/api/review/'+id,p);document.getElementById('msg').textContent='Asociación guardada. No se envió ningún mensaje.';load()}catch(e){document.getElementById('msg').textContent=e.message}}
    async function checkBearer(){const el=document.getElementById('pancakeResult');el.textContent='Verificando autenticación Bearer…';try{const d=await api('/dispatch/api/pancake/check-bearer');el.textContent='Bearer · HTTP '+(d.http_status||'?')+' · API success: '+String(d.api_success)+' · error_code: '+(d.api_error_code||'-')+' · claves: '+(d.response_keys||[]).join(', ')+(d.valid?' · CONECTADO':' · SIN VALIDAR')}catch(e){el.textContent='Error: '+e.message}}
    async function testContact(){const phone=prompt('Número personal de prueba con código país, por ejemplo +549...');if(!phone)return;const el=document.getElementById('pancakeResult');el.textContent='Consultando identificador, sin enviar mensajes…';try{const d=await api('/dispatch/api/botcake/test-contact',{phone});el.textContent='Contacto prueba: '+(d.candidate_id||'-')+' · HTTP '+(d.http_status||'-')+' · API success '+String(d.api_success)+' · registros '+String(d.history_entries)+' · Identidad NO verificada. '+(d.reason||'')}catch(e){el.textContent='Error: '+e.message}}
    async function checkBotcake(){const el=document.getElementById('pancakeResult');el.textContent='Consultando Botcake, solo lectura…';try{const d=await api('/dispatch/api/botcake/check');el.textContent=d.connected?'Botcake API conectada · consulta de palabras clave OK · SOLO LECTURA':'Botcake pendiente · '+(d.reason||'respuesta no validada')+' · HTTP '+(d.http_status||'?')+' · tipo respuesta '+(d.response_type||'-')+' · claves '+(d.response_keys||[]).join(',')+' · status_code '+(d.status_code||'-')+' · error tipo '+(d.api_error_kind||'-')+' · error código '+(d.api_error_code_nested||'-')+' · campos error '+(d.error_fields||[]).join(',')+' · success '+String(d.api_success)+' · código '+(d.api_error_code||'-')+' · token '+(d.token_present===false?'falta':'configurado')+' · página '+(d.page_present===false?'falta':'configurada')}catch(e){el.textContent='Error Botcake: '+e.message}}
    async function checkPancake(){const el=document.getElementById('pancakeResult');el.textContent='Consultando Pancake (solo lectura)…';try{const d=await api('/dispatch/api/pancake/check');el.textContent=d.connected?'Conexión correcta. Conversaciones en muestra: '+d.conversations_in_sample:'HTTP '+(d.http_status||'?')+' · Estructura: '+(d.response_type||'?')+' · Claves: '+(d.response_keys||[]).join(', ')+' · data: '+(d.data_type||'?')+' · success: '+String(d.api_success)+' · error_code: '+(d.api_error_code||'no disponible')}catch(e){el.textContent='Error: '+e.message}}
    async function prepareTestSend(){const el=document.getElementById('testSendStatus');try{
      const mode=confirm('PRUEBA CONTROLADA: Aceptar = TEXTO (recomendado para diagnosticar). Cancelar = no enviar nada.');
      if(!mode){el.textContent='Cancelado. Sin envío.';return}
      const d=await api('/dispatch/test-send/prepare');
      el.textContent='Preparado: un MENSAJE DE TEXTO a WhatsApp terminado en '+d.last4+'. Vence en 5 minutos.';
      if(!confirm('Confirmación final: ¿enviar exactamente UN TEXTO de prueba a tu WhatsApp terminado en '+d.last4+'?')){el.textContent='Cancelado. No se envió nada.';return}
      el.textContent='Enviando una única prueba…';
      const r=await api('/dispatch/test-send/confirm',{challenge:d.challenge,confirmed:true,mode:'text'});
      el.textContent='Botcake: '+r.result+' · ID '+r.attempt_id+' · tipo '+(r.test_mode||'-')+' · status '+(r.provider_status||'-')+' · error '+(r.provider_error_summary||'-')+' · código '+(r.error_code||r.provider_error_code||'-')+'. Revisá WhatsApp antes de cualquier repetición.';
    }catch(e){el.textContent='Error: '+e.message}}
    async function health(){try{const d=await api('/dispatch/ops/health');document.getElementById('health').textContent=d.ephemeral_storage?'ATENCIÓN: almacenamiento temporal, los tickets pueden perderse al reiniciar Render. Envíos bloqueados.':'Almacenamiento: '+d.data_directory+' · persistencia no verificada. Envíos bloqueados.'}catch(e){document.getElementById('health').textContent=e.message}}
    function readField(id,k){const el=document.querySelector('[data-id="'+id+'"][data-field="'+k+'"]');return el?el.value.trim():''}
    function note(id,v){const el=document.getElementById('ticket-'+id);if(el)el.textContent=v}
    async function findClient(id){try{note(id,'Consultando Botcake…');const d=await api('/dispatch/ops/lookup/'+id,{phone:readField(id,'phone')});note(id,'Candidato: '+d.candidate_psid+' · Registros: '+String(d.history_entries)+' · IDENTIDAD NO VERIFICADA. Comprobá nombre y pedido manualmente.')}catch(e){note(id,'Error: '+e.message)}}
    async function approveSafe(id){const p={phone:readField(id,'phone'),recipient_name:readField(id,'recipient_name'),order_ref:readField(id,'matched_order')};if(!confirm('¿Confirmaste manualmente que el teléfono, nombre y pedido corresponden a esta persona? NO se enviará nada.'))return;try{const d=await api('/dispatch/ops/confirm/'+id,p);note(id,'Aprobado, sin enviar: '+d.psid);setTimeout(load,1500)}catch(e){note(id,'Error: '+e.message)}}
    async function retryTicket(id){if(!confirm('Volver a analizar la imagen con IA? Puede tener costo de API.'))return;try{note(id,'Analizando…');const d=await api('/dispatch/ops/retry-vision/'+id);note(id,d.ok?'Foto procesada correctamente':'Error: '+d.error);setTimeout(load,1500)}catch(e){note(id,'Error: '+e.message)}}
    async function previewTicket(id){try{const d=await api('/dispatch/api/image/'+id);const w=window.open('','_blank');if(!w){note(id,'Permití popups');return;}const img=w.document.createElement('img');img.src=d.data_url;img.style.maxWidth='100%';w.document.body.appendChild(img)}catch(e){note(id,e.message)}}
    load();setInterval(load,20000);
    </script></body></html>"""

@router.post("/dispatch/api/image/{ticket_id}")
async def dispatch_image(ticket_id:int, request:Request):
    authorized(request)
    with db() as conn:
        row=conn.execute("SELECT mime_type FROM tickets WHERE id=?",(ticket_id,)).fetchone()
    if not row: raise HTTPException(404,"Ticket inexistente")
    ext={"image/jpeg":".jpg","image/png":".png","image/webp":".webp"}.get(row["mime_type"])
    if not ext: raise HTTPException(404,"Formato de imagen desconocido")
    path=DATA_DIR/(str(ticket_id)+ext)
    if not path.exists(): raise HTTPException(404,"Imagen perdida; configurar almacenamiento persistente")
    return {"data_url":"data:"+row["mime_type"]+";base64,"+base64.b64encode(path.read_bytes()).decode()}


class DispatchContact(BaseModel):
    id: str
    name: str
    phone: Optional[str]=None
    city: Optional[str]=None
    brand: Optional[str]=None
    order_ref: Optional[str]=None


@router.post("/dispatch/admin/import-contacts")
async def dispatch_import_contacts(request:Request, records:list[DispatchContact]):
    admin(request)
    if len(records)>500: raise HTTPException(400,"Máximo 500 contactos por lote")
    with db() as conn:
        for r in records:
            if not r.id.strip() or not r.name.strip(): continue
            conn.execute("""INSERT OR REPLACE INTO contacts
              (id,name,phone,city,brand,order_ref,updated_at)
              VALUES(?,?,?,?,?,?,?)""",
              (r.id,r.name,r.phone,r.city,r.brand,r.order_ref,int(time.time())))
    return {"ok":True,"received":len(records)}


def _dispatch_norm(value):
    import unicodedata
    source=unicodedata.normalize("NFKD",str(value or ""))
    return "".join(ch.lower() for ch in source if ch.isalnum() and not unicodedata.combining(ch))


@router.post("/dispatch/api/suggestions/{ticket_id}")
async def dispatch_suggestions(ticket_id:int, request:Request):
    authorized(request)
    with db() as conn:
        ticket=conn.execute("SELECT extracted FROM tickets WHERE id=?",(ticket_id,)).fetchone()
        if not ticket: raise HTTPException(404,"Ticket inexistente")
        contacts=conn.execute("SELECT id,name,phone,city,brand,order_ref FROM contacts ORDER BY updated_at DESC LIMIT 5000").fetchall()
    extracted=json.loads(ticket["extracted"])
    name=_dispatch_norm(extracted.get("recipient_name"))
    phone=_dispatch_norm(extracted.get("phone"))
    city=_dispatch_norm(extracted.get("destination"))
    results=[]
    for r in contacts:
        score=0
        if phone and _dispatch_norm(r["phone"])==phone: score+=60
        if name and _dispatch_norm(r["name"])==name: score+=30
        elif name and (name in _dispatch_norm(r["name"]) or _dispatch_norm(r["name"]) in name): score+=15
        if city and _dispatch_norm(r["city"]) and (city in _dispatch_norm(r["city"]) or _dispatch_norm(r["city"]) in city): score+=10
        if score: results.append({**dict(r),"score":score})
    results.sort(key=lambda x:x["score"],reverse=True)
    return {"candidates":results[:10],"automatic_send":False,
       "note":"Coincidencias orientativas, requieren revisión; datos importados manualmente."}


@router.post("/dispatch/api/pancake/check")
async def dispatch_pancake_check(request:Request):
    """Read-only API connection test, no customer data or credentials exposed."""
    authorized(request)
    token=os.getenv("PANCAKE_API_TOKEN","")
    page=os.getenv("DISPATCH_PANCAKE_PAGE_ID","")
    if not token or not page:
        return {"connected":False,"reason":"missing_configuration","token_present":bool(token),"page_present":bool(page)}
    if not re.fullmatch(r"[A-Za-z0-9_-]{5,100}",page):
        return {"connected":False,"reason":"invalid_page_identifier"}
    endpoint="https://pages.fm/api/public_api/v2/pages/"+urlparse.quote(page,safe="")+"/conversations"
    url=endpoint+"?"+urlparse.urlencode({"page_access_token":token})
    req=urlreq.Request(url,headers={"Accept":"application/json","User-Agent":"FostersDispatch/0.1"},method="GET")
    try:
        with urlreq.urlopen(req,timeout=20) as response:
            raw=response.read(512*1024)
            status=response.status
        body=json.loads(raw)
        conversations=body.get("conversations") if isinstance(body,dict) else None
        return {"connected":status==200 and isinstance(conversations,list),
                "http_status":status,
                "conversations_in_sample":len(conversations) if isinstance(conversations,list) else None,
                "response_keys":list(body.keys())[:15] if isinstance(body,dict) else [],
                "response_type":type(body).__name__,
                "api_success":body.get('success') if isinstance(body,dict) and isinstance(body.get('success'),bool) else None,
                "api_error_code":str(body.get("error_code"))[:60] if isinstance(body,dict) and body.get("success") is False else None,
                "reason":"pancake_rejected_request" if isinstance(body,dict) and body.get("success") is False else None,
                "data_type":type(body.get('data')).__name__ if isinstance(body,dict) and 'data' in body else None,
                "note":"Solo lectura. No se muestran ni guardan datos de clientes."}
    except urlreq.HTTPError as exc:
        return {"connected":False,"http_status":exc.code,
                "reason":"permission_or_page_error" if exc.code in (401,403,404) else "pancake_http_error",
                "note":"Verificar tipo de token (page access token) e identificador de página. No se envió nada."}
    except Exception as exc:
        print("[DISPATCH] Pancake read-only diagnostic failed:",type(exc).__name__)
        return {"connected":False,"reason":"network_or_response_error",
                "note":"Revisar Render Logs. No se envió nada."}

@router.post("/dispatch/api/pancake/check-bearer")
async def dispatch_pancake_check_bearer(request:Request):
    """Diagnostic only. Confirm whether public token is accepted as Bearer by this endpoint.
    Never return token, messages, customer details, or raw Pancake response.
    """
    authorized(request)
    token=os.getenv("PANCAKE_API_TOKEN","").strip()
    page=os.getenv("DISPATCH_PANCAKE_PAGE_ID","").strip()
    if not token or not re.fullmatch(r"[A-Za-z0-9_-]{5,100}",page):
        return {"valid":False,"reason":"missing_or_invalid_config"}
    endpoint="https://pages.fm/api/public_api/v2/pages/"+urlparse.quote(page,safe="")+"/conversations"
    req=urlreq.Request(endpoint,
        headers={"Accept":"application/json","Authorization":"Bearer "+token,
                 "User-Agent":"FostersDispatch/0.1"},method="GET")
    try:
        with urlreq.urlopen(req,timeout=15) as response:
            status=response.status
            raw=response.read(512*1024)
        body=json.loads(raw)
        keys=list(body.keys())[:12] if isinstance(body,dict) else []
        accepted=isinstance(body,dict) and body.get("success") is not False and isinstance(body.get("conversations"),list)
        return {"valid":accepted,"http_status":status,
                "api_success":body.get("success") if isinstance(body,dict) and isinstance(body.get("success"),bool) else None,
                "api_error_code":str(body.get("error_code"))[:30] if isinstance(body,dict) and body.get("success") is False else None,
                "response_keys":keys,
                "explanation":"Prueba de lectura únicamente; respuesta sin datos de clientes. Endpoint puede requerir token de página."}
    except urlreq.HTTPError as exc:
        return {"valid":False,"http_status":exc.code,"reason":"http_error"}
    except Exception as exc:
        print("[DISPATCH] Bearer diagnostic error:",type(exc).__name__)
        return {"valid":False,"reason":"network_or_invalid_response"}

@router.post("/dispatch/api/botcake/check")
async def dispatch_botcake_check(request:Request):
    """Read-only Botcake API probe: no customer records or tokens returned."""
    authorized(request)
    token=os.getenv("DISPATCH_BOTCAKE_TOKEN","").strip()
    page=os.getenv("DISPATCH_BOTCAKE_PAGE_ID","").strip()
    if not token or not page:
        return {"connected":False,"reason":"missing_configuration",
                "token_present":bool(token),"page_present":bool(page)}
    if not re.fullmatch(r"[a-zA-Z0-9_-]{5,100}",page):
        return {"connected":False,"reason":"invalid_page_id"}
    endpoint="https://botcake.io/api/public_api/v1/pages/"+urlparse.quote(page,safe="")+"/keywords"
    req=urlreq.Request(endpoint,headers={"Accept":"application/json",
        "access-token":token,"User-Agent":"FostersDispatch/0.1"},method="GET")
    try:
        with urlreq.urlopen(req,timeout=20) as response:
            status=response.status
            raw=response.read(512*1024)
        body=json.loads(raw)
        wrapped=body.get("response") if isinstance(body,dict) else None
        customers=wrapped if isinstance(wrapped,list) else (body.get("data") if isinstance(body,dict) and isinstance(body.get("data"),list) else None)
        rejected=isinstance(body,dict) and body.get("success") is False
        accepted=(status==200 and not rejected and isinstance(body,dict) and body.get("success") is True and isinstance(body.get("data"),list))
        return {"connected":accepted,"http_status":status,
           "api_success":body.get("success") if isinstance(body,dict) else None,
           "api_error_code":str(body.get("error_code"))[:60] if isinstance(body,dict) and rejected and body.get("error_code") else None,
           "response_keys":list(body.keys())[:12] if isinstance(body,dict) else [],
           "response_type":type(wrapped).__name__,
           "status_code":str(body.get("status_code"))[:30] if isinstance(body,dict) and body.get("status_code") is not None else None,
           "api_error_kind":type(body.get("error")).__name__ if isinstance(body,dict) and body.get("error") is not None else None,
           "api_error_code_nested":str(body["error"].get("code"))[:30] if isinstance(body,dict) and isinstance(body.get("error"),dict) and body["error"].get("code") is not None else None,
           "error_fields": [k for k in ("error","errors","message","detail","code") if isinstance(body,dict) and k in body],
           "customer_count":None,
           "records_count":len(body.get("data")) if accepted else None,
           "reason":"api_rejected" if rejected else ("unrecognized_response" if not accepted else None),
           "note":"Solo lectura: no se muestran ni se almacenan datos de clientes."}
    except urlreq.HTTPError as exc:
        return {"connected":False,"http_status":exc.code,"reason":"http_error"}
    except Exception as exc:
        print("[DISPATCH] Botcake diagnostic error:",type(exc).__name__)
        return {"connected":False,"reason":"network_or_response_error"}

class DispatchTestPhone(BaseModel):
    phone: str


@router.post("/dispatch/api/botcake/test-contact")
async def dispatch_botcake_test_contact(request:Request, payload:DispatchTestPhone):
    """Read-only candidate lookup, never treats a successful response as verified identity."""
    authorized(request)
    token=os.getenv("DISPATCH_BOTCAKE_TOKEN","").strip()
    page=os.getenv("DISPATCH_BOTCAKE_PAGE_ID","").strip()
    if not token or not re.fullmatch(r"[A-Za-z0-9_-]{5,100}",page):
        raise HTTPException(503,"Configuración de Botcake incompleta")
    digits=re.sub(r"[^0-9]","",payload.phone)
    if not 8 <= len(digits) <= 15:
        raise HTTPException(400,"Número internacional inválido")
    candidate="wa_"+digits
    endpoint="https://botcake.io/api/public_api/v1/pages/"+urlparse.quote(page,safe="")+"/customer/"+urlparse.quote(candidate,safe="")
    req=urlreq.Request(endpoint,headers={"access-token":token,"Accept":"application/json",
                "User-Agent":"FostersDispatch/0.1"},method="GET")
    try:
        with urlreq.urlopen(req,timeout=20) as resp:
            body=json.loads(resp.read(256*1024))
            status=resp.status
        success=body.get("success") if isinstance(body,dict) else None
        histories=body.get("histories") if isinstance(body,dict) else None
        return {"http_status":status,"api_success":success,
                "candidate_id":candidate,
                "history_entries":len(histories) if isinstance(histories,list) else None,
                "response_keys":list(body.keys())[:10] if isinstance(body,dict) else [],
                "identity_verified":False,
                "note":"Este endpoint devuelve historial de operaciones por PSID; no confirma identidad del destinatario. No se envió ningún mensaje."}
    except urlreq.HTTPError as exc:
        return {"http_status":exc.code,"candidate_id":candidate,"identity_verified":False,
                "reason":"botcake_http_error"}
    except Exception as exc:
        print("[DISPATCH] Botcake test contact:",type(exc).__name__)
        return {"candidate_id":candidate,"identity_verified":False,"reason":"network_or_response_error"}
