"""Read-only product resolution from Meta ad metadata; never changes Botcake users."""
import hmac
import json
import os
import re
from typing import Optional
from urllib import error, parse, request

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, Field


class AdSourceRequest(BaseModel):
    ad_id: Optional[str] = Field(default=None, max_length=30)


def name_products(value):
    return {key for key, pattern in (("henley", r"\bhenleys?\b"),
                                     ("polo", r"\bpolos?\b"))
            if re.search(pattern, str(value or ""), re.IGNORECASE)}


def fallback(reason):
    return {"resolved": False, "product": None, "campaign_key": "general",
            "next_action": "ask_product", "reason": reason,
            "should_set_product": False, "mutated": False}


def classify_metadata(data, ad_id):
    if not isinstance(data, dict) or data.get("id") != ad_id:
        return fallback("invalid_meta_response")
    campaign = data.get("campaign")
    campaign_name = campaign.get("name") if isinstance(campaign, dict) else None
    choices = name_products(data.get("name")) | name_products(campaign_name)
    if len(choices) != 1:
        return fallback("ambiguous_ad_product" if choices else "product_not_in_ad_names")
    product = choices.pop()
    return {"resolved": True, "product": product, "campaign_key": product,
            "next_action": "use_product_opening", "reason": "meta_ad_metadata",
            "should_set_product": True, "mutated": False, "ad_id": ad_id}


class NoRedirect(request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def fetch_ad(ad_id, token, version):
    query = parse.urlencode({"fields": "id,name,campaign{id,name}"})
    url = "https://graph.facebook.com/" + version + "/" + ad_id + "?" + query
    req = request.Request(url, headers={"Authorization": "Bearer " + token,
                                       "Accept": "application/json"})
    # Keep credentials on the fixed Meta host and preserve inherited proxy/TLS trust.
    with request.build_opener(NoRedirect()).open(req, timeout=10) as response:
        raw = response.read(65537)
        if len(raw) > 65536:
            raise ValueError("Oversized Meta response")
        return json.loads(raw)


def resolve_ad(ad_id):
    if ad_id is None or ad_id == "":
        return fallback("missing_ad_id")
    if not re.fullmatch(r"[0-9]{5,30}", ad_id):
        raise HTTPException(400, "ad_id debe ser el ID numérico real del anuncio")
    token = os.getenv("META_ADS_ACCESS_TOKEN", "").strip()
    version = os.getenv("META_GRAPH_API_VERSION", "").strip()
    if not token:
        return fallback("meta_credentials_missing")
    if not re.fullmatch(r"v[0-9]+\.0", version):
        return fallback("meta_api_version_missing_or_invalid")
    try:
        data = fetch_ad(ad_id, token, version)
    except error.HTTPError as exc:
        result = fallback("meta_access_denied" if exc.code in (400, 401, 403)
                          else "meta_request_failed")
        result["upstream_http_status"] = exc.code
        return result
    except (error.URLError, TimeoutError, OSError, ValueError):
        return fallback("meta_request_failed")
    if isinstance(data, dict) and "error" in data:
        return fallback("meta_request_failed")
    return classify_metadata(data, ad_id)


def make_router(api_token):
    router = APIRouter()
    bearer = HTTPBearer(auto_error=False)

    def authenticate(credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer)):
        if (not credentials or credentials.scheme.lower() != "bearer"
                or not hmac.compare_digest(credentials.credentials.encode(), api_token.encode())):
            raise HTTPException(401, "Unauthorized")

    @router.post("/fosters/ads/resolve", dependencies=[Depends(authenticate)])
    def resolve(payload: AdSourceRequest):
        return resolve_ad(payload.ad_id)

    return router
