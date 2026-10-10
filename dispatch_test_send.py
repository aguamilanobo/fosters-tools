"""Explicitly confirmed one-recipient Botcake image test. No customer tickets are sent."""
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import Response
from urllib import request as urlreq, error as urlerr
from dispatch import authorized, db, audit
import os,re,time,secrets,sqlite3,json,zlib,struct,hashlib

router=APIRouter()
def png_chunk(tag,data):
    return struct.pack(">I",len(data))+tag+data+struct.pack(">I",zlib.crc32(tag+data)&0xffffffff)

def test_png():
    # Clearly synthetic black/white test pattern, never contains real customer information.
    width,height=420,210
    chunks=[]
    for y in range(height):
        row=bytearray()
        for x in range(width):
            black=x<6 or x>=width-6 or y<6 or y>=height-6 or (70<y<140 and (x//14+y//14)%2==0)
            row.extend((28,28,28) if black else (250,250,250))
        chunks.append(b"\x00"+bytes(row))
    return b"\x89PNG\r\n\x1a\n"+png_chunk(b"IHDR",struct.pack(">IIBBBBB",width,height,8,2,0,0,0))+png_chunk(b"IDAT",zlib.compress(b"".join(chunks),6))+png_chunk(b"IEND",b"")

@router.get("/dispatch/test-image.png")
def test_image():
    return Response(test_png(),media_type="image/png",headers={"Cache-Control":"public, max-age=300","X-Content-Type-Options":"nosniff"})

def setup(conn):
    conn.execute("""CREATE TABLE IF NOT EXISTS dispatch_test_sends (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      actor TEXT NOT NULL, challenge_hash TEXT NOT NULL UNIQUE,
      target TEXT NOT NULL, created INTEGER NOT NULL,
      expires INTEGER NOT NULL, consumed INTEGER NOT NULL DEFAULT 0,
      status TEXT NOT NULL DEFAULT 'prepared', response_code TEXT)""")
    conn.commit()

def test_target():
    digits=re.sub("[^0-9]","",os.getenv("DISPATCH_TEST_WHATSAPP",""))
    if not 8<=len(digits)<=15:raise HTTPException(503,"Configurar DISPATCH_TEST_WHATSAPP")
    return digits

@router.post("/dispatch/test-send/prepare")
async def test_prepare(request:Request):
    actor=authorized(request)
    dest=test_target()
    if not os.getenv("DISPATCH_BOTCAKE_TOKEN") or not os.getenv("DISPATCH_BOTCAKE_PAGE_ID"):
        raise HTTPException(503,"Falta Botcake")
    challenge=secrets.token_urlsafe(28)
    h=hashlib.sha256(challenge.encode()).hexdigest()
    with db() as conn:
        setup(conn)
        conn.execute("INSERT INTO dispatch_test_sends(actor,challenge_hash,target,created,expires) VALUES(?,?,?,?,?)",
          (actor,h,dest,int(time.time()),int(time.time())+300))
    return {"challenge":challenge,"last4":dest[-4:],"expires_seconds":300,
      "warning":"UNA imagen de prueba al WhatsApp autorizado. Nunca tickets de clientes."}

@router.post("/dispatch/test-send/confirm")
async def test_confirm(request:Request):
    actor=authorized(request)
    body=await request.json()
    challenge=str(body.get("challenge",""))
    consent=body.get("confirmed") is True
    if not consent or len(challenge)>100:raise HTTPException(400,"Confirmación requerida")
    dest=test_target()
    h=hashlib.sha256(challenge.encode()).hexdigest()
    with db() as conn:
        setup(conn)
        cur=conn.execute("""UPDATE dispatch_test_sends SET consumed=1,status='attempting'
          WHERE challenge_hash=? AND actor=? AND target=? AND consumed=0 AND expires>?""",
          (h,actor,dest,int(time.time())))
        if cur.rowcount!=1:raise HTTPException(409,"Autorización vencida o ya utilizada")
        row=conn.execute("SELECT id FROM dispatch_test_sends WHERE challenge_hash=?",(h,)).fetchone()
        attempt_id=row["id"]
    page=os.getenv("DISPATCH_BOTCAKE_PAGE_ID","").strip()
    if not re.fullmatch("[A-Za-z0-9_-]{5,100}",page):raise HTTPException(503,"Canal Botcake no válido")
    token=os.getenv("DISPATCH_BOTCAKE_TOKEN","")
    public_url=os.getenv("DISPATCH_PUBLIC_URL","https://fosters-tools.onrender.com").rstrip("/")
    payload={"psid":"wa_"+dest,"data":{"version":"v2","content":{"messages":[{"type":"image","url":public_url+"/dispatch/test-image.png"}]}}}
    req=urlreq.Request("https://botcake.io/api/public_api/v1/pages/"+page+"/flows/send_content",
       data=json.dumps(payload).encode(),method="POST",
       headers={"access-token":token,"Content-Type":"application/json","Accept":"application/json"})
    status="unknown"
    response_code=""
    provider_status=None
    provider_error_type=None
    provider_error_code=None
    try:
        with urlreq.urlopen(req,timeout=20) as res:
            data=json.loads(res.read(20000))
        if isinstance(data,dict):
            provider_status=str(data.get("status_code"))[:30] if data.get("status_code") is not None else None
            err=data.get("error")
            provider_error_type=type(err).__name__ if err is not None else None
            if isinstance(err,dict):
                provider_error_code=str(err.get("code"))[:30] if err.get("code") is not None else None
        if isinstance(data,dict) and data.get("success") is True:
            status="accepted"
        else:
            status="rejected"
            response_code=str(data.get("error_code") or data.get("status_code") or "")[:30] if isinstance(data,dict) else ""
    except urlerr.HTTPError as exc:
        status="rejected";response_code="HTTP_"+str(exc.code)
    except Exception as exc:
        print("[DISPATCH] Test-send ambiguous response:",type(exc).__name__)
        status="unknown"
    with db() as conn:
        conn.execute("UPDATE dispatch_test_sends SET status=?,response_code=? WHERE id=?",
           (status,response_code,attempt_id))
    return {"result":status,"attempt_id":attempt_id,"error_code":response_code,
     "provider_status":provider_status,"provider_error_type":provider_error_type,"provider_error_code":provider_error_code,
     "delivery_confirmed":False,
     "note":"Aceptado significa aceptado por Botcake, NO entregado en WhatsApp. No reintentar automáticamente si es desconocido."}
