from fastapi import FastAPI, Query, Header, HTTPException

app = FastAPI()

API_TOKEN = "fosters_bot_2026"


@app.get("/")
def root():
    return {"status": "ok", "service": "fosters-tools"}


@app.get("/recommend-size")
def recommend_size(
    height_cm: float = Query(..., description="Altura del cliente en cm"),
    weight_kg: float = Query(..., description="Peso del cliente en kg"),
    usual_size: str | None = Query(None, description="Talle habitual del cliente"),
    authorization: str | None = Header(None),
):
    if authorization != f"Bearer {API_TOKEN}":
        raise HTTPException(status_code=401, detail="Unauthorized")

    if weight_kg < 65:
        recommended = "M"
        confidence = "medium"
        reason = "M es el talle más chico disponible actualmente."

    elif weight_kg <= 77:
        recommended = "M"
        confidence = "high"
        reason = "Por peso corresponde principalmente M."

        if height_cm >= 188 and weight_kg >= 73:
            recommended = "L"
            confidence = "medium"
            reason = "Por altura conviene subir a L para asegurar el largo."

    elif weight_kg <= 86:
        recommended = "L"
        confidence = "high"
        reason = "Por peso corresponde principalmente L."

    elif weight_kg <= 110:
        recommended = "XL"
        confidence = "high"
        reason = "Por peso corresponde principalmente XL."

    else:
        recommended = "XL"
        confidence = "low"
        reason = "XL es el talle más grande disponible; conviene confirmar medidas."

    if usual_size:
        usual_size = usual_size.upper()

    return {
        "recommended_size": recommended,
        "confidence": confidence,
        "reason": reason,
        "height_cm": height_cm,
        "weight_kg": weight_kg,
        "usual_size": usual_size,
    }
