from fastapi import APIRouter, Depends

from app.core.deps import get_current_user
from app.models import User
from app.schemas import AIImproveIn, AIImproveOut
from app.services.ai import improve_text

router = APIRouter(prefix="/ai", tags=["ai"])


@router.post("/improve", response_model=AIImproveOut)
def improve(payload: AIImproveIn, _user: User = Depends(get_current_user)):
    improved, provider = improve_text(payload.kind, payload.text, payload.tone)
    return AIImproveOut(original=payload.text, improved=improved, provider=provider)
