from fastapi import APIRouter, Depends, HTTPException

from app.domain.risk import KNOWN_BEHAVIOURS
from app.schemas import Feedback, FeedbackCreate
from app.security import get_storage, require_user
from app.storage.base import Row, Storage

router = APIRouter()


@router.post("", response_model=Feedback, status_code=201,
             summary="Operator corrects a misclassified behaviour (used to retrain the model)")
def create_feedback(body: FeedbackCreate, user: Row = Depends(require_user), storage: Storage = Depends(get_storage)):
    if storage.get_event(body.event_id) is None:
        raise HTTPException(404, "event not found")
    if body.corrected_behaviour not in KNOWN_BEHAVIOURS:
        raise HTTPException(422, f"unknown behaviour; expected one of {sorted(KNOWN_BEHAVIOURS)}")
    row = storage.insert_feedback({"event_id": body.event_id, "user_id": user["user_id"],
                                   "corrected_behaviour": body.corrected_behaviour, "note": body.note})
    return row
