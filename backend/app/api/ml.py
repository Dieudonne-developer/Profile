from typing import Any, Callable

from fastapi import APIRouter, File, HTTPException, UploadFile
from pydantic import BaseModel, Field
import httpx

from app.core.config import get_settings

router = APIRouter(prefix="/ml", tags=["machine-learning"])

# Fitted on the demo study-hours dataset in notebooks/NTARINDWA_ML_Colab_Backend.ipynb
SCORE_INTERCEPT = 40.12
SCORE_SLOPE = 6.47
LEAF_CLASSES = ["Cordana", "Healthy", "Pestalotiopsis", "Sigatoka"]

# Set by the Colab notebook in MODE=full so leaf inference stays in-process.
inprocess_leaf: Callable[[bytes], Any] | None = None


class ScoreIn(BaseModel):
    hours: float = Field(ge=0, le=24)


class ScoreOut(BaseModel):
    hours: float
    predicted_score: float
    model: str
    backend: str
    note: str


@router.get("/status")
def ml_status():
    settings = get_settings()
    colab = (settings.ml_backend_url or "").rstrip("/")
    inprocess = inprocess_leaf is not None
    return {
        "score_model": "local-linear-regression",
        "leaf_backend": "colab-inprocess" if inprocess else ("colab" if colab else "unavailable"),
        "colab_connected": bool(colab or inprocess),
        "classes": LEAF_CLASSES,
        "notebook": "notebooks/NTARINDWA_ML_Colab_Backend.ipynb",
    }


@router.post("/predict/score", response_model=ScoreOut)
def predict_score(payload: ScoreIn):
    predicted = SCORE_INTERCEPT + SCORE_SLOPE * payload.hours
    predicted = round(min(100.0, max(0.0, predicted)), 2)
    return ScoreOut(
        hours=payload.hours,
        predicted_score=predicted,
        model="ordinary least squares linear regression",
        backend="fastapi-local",
        note="Demo model: examination score from weekly study hours. Same coefficients as the Colab notebook.",
    )


@router.post("/predict/leaf")
async def predict_leaf(file: UploadFile = File(...)):
    settings = get_settings()
    colab = (settings.ml_backend_url or "").rstrip("/")
    contents = await file.read()
    if len(contents) > 5 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="Please upload an image smaller than 5 MB.")
    if inprocess_leaf is not None:
        try:
            return inprocess_leaf(contents)
        except Exception as exc:
            raise HTTPException(status_code=400, detail="Could not classify that image.") from exc
    if not colab:
        raise HTTPException(
            status_code=503,
            detail=(
                "Banana-leaf inference runs on Google Colab (GPU). "
                "Open notebooks/NTARINDWA_ML_Colab_Backend.ipynb, start the Colab server cell, "
                "then set ML_BACKEND_URL in backend/.env to the printed proxy URL."
            ),
        )
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{colab}/predict/leaf",
                files={"file": (file.filename or "leaf.jpg", contents, file.content_type or "image/jpeg")},
            )
    except httpx.RequestError as exc:
        raise HTTPException(
            status_code=503,
            detail=f"Could not reach the Colab ML server. Start the notebook runtime. ({exc.__class__.__name__})",
        ) from exc
    if response.status_code >= 400:
        raise HTTPException(status_code=502, detail="Colab returned an error while classifying the leaf image.")
    return response.json()
