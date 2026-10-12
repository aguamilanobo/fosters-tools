"""Read-only Pancake ad attribution diagnostic for Fosters. No customer records are returned."""
from fastapi import APIRouter, Request, HTTPException
from urllib import request as ur, parse as up, error as ue
from dispatch import authorized
import os, json, re

router=APIRouter()

def safe_keys(obj):
    return sorted(str(k)[:64] for k in obj.keys())[:40] if isinstance(obj,dict) else []

def request_pancake(page,token):
    endpoint="https://pages.fm/api/public_api/v2/pages/"+up.quote(page,safe="")+"/conversations"
    url=endpoint+"?"+up.urlencode({"page_access_token":token,"type":"INBOX"})
    req=ur.Request(url,headers={"Accept":"application/json","User-Agent":"FostersTools/1.0"},method="GET")
    try:
        with ur.urlopen(req,timeout=15) as response:
            status=response.status
            raw=response.read(1000000)
        return status,json.loads(raw)
    except ue.HTTPError as exc:
        return exc.code, None
    except (ue.URLError,TimeoutError,ValueError) as exc:
        return None,None

def summarize(payload):
    if not isinstance(payload,dict):
        return {"response_type":type(payload).__name__,"response_keys":[],"sample_count":0,
                "attribution_key_paths":[],"ad_ids":[]}
    conversations=None
    for field in ("conversations","data","items"):
        obj=payload.get(field)
        if isinstance(obj,list): conversations=obj;break
        if isinstance(obj,dict):
            for nested in ("conversations","items","data"):
                if isinstance(obj.get(nested),list):conversations=obj[nested];break
        if conversations is not None:break
    conversations=(conversations or [])[:15]
    paths=set();ids=set()
    def walk(node,prefix="",depth=0):
        if depth>4:return
        if isinstance(node,dict):
            for key,value in node.items():
                k=str(key).lower()
                path=prefix+"."+str(key) if prefix else str(key)
                if any(x in k for x in ("ad_id","adid","referral","campaign_id","source_id","ads_id")):
                    paths.add(path[:120])
                    if ("ad_id" in k or k in ("adid","ads_id")) and isinstance(value,(str,int)):
                        v=str(value)
                        if re.fullmatch(r"[0-9]{5,30}",v):ids.add(v)
                if isinstance(value,(dict,list)):walk(value,path,depth+1)
        elif isinstance(node,list):
            for item in node[:3]:walk(item,prefix+"[]",depth+1)
    for item in conversations:walk(item)
    return {"response_type":"dict","response_keys":safe_keys(payload),
            "sample_count":len(conversations),"attribution_key_paths":sorted(paths)[:35],
            "ad_ids":sorted(ids)[:15],
            "note":"IDs de anuncios solamente; nunca datos personales. La presencia del ID no demuestra que Botcake lo reciba antes de responder."}

@router.post("/fosters/ads/diagnostic")
async def ads_diagnostic(request:Request):
    authorized(request)
    token=os.getenv("PANCAKE_PAGE_ACCESS_TOKEN","").strip() or os.getenv("PANCAKE_API_TOKEN","").strip()
    page=os.getenv("FOSTERS_PANCAKE_PAGE_ID","").strip() or "waba_59175253561"
    if not token:
        return {"ready":False,"reason":"missing_token","needs":"PANCAKE_PAGE_ACCESS_TOKEN","mutated":False}
    if not re.fullmatch(r"[A-Za-z0-9_-]{4,80}",page):
        raise HTTPException(400,"ID de página inválido")
    status,data=request_pancake(page,token)
    if data is None:
        return {"ready":False,"http_status":status,"reason":"request_failed_or_non_json",
                "hints":["Verificar que PANCAKE_API_TOKEN sea Page Access Token de pages.fm",
                         "Verificar FOSTERS_PANCAKE_PAGE_ID; un ID WABA puede no coincidir con el ID de página usado por esta API"],
                "page_id":page,"mutated":False}
    brief=summarize(data)
    return {"ready":status==200 and data.get("success") is not False,
            "http_status":status,"api_success":data.get("success"),"page_id":page,
            "token_configured":True,"mutated":False,**brief}
