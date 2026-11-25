"""Investigation settings endpoints (BD31). Thin: the work is in settings_service."""

from fastapi import APIRouter

from txnweave_api.db.database import SessionDep
from txnweave_api.schemas.settings import InvestigationSettingsIn, InvestigationSettingsOut
from txnweave_api.services import settings_service

router = APIRouter(prefix="/investigations/{investigation_id}/settings", tags=["settings"])


@router.get("", response_model=InvestigationSettingsOut)
def get_settings(investigation_id: int, session: SessionDep):
    return settings_service.get_settings(session, investigation_id)


@router.put("", response_model=InvestigationSettingsOut)
def replace_settings(investigation_id: int, body: InvestigationSettingsIn, session: SessionDep):
    return settings_service.replace_settings(session, investigation_id, body)


@router.delete("", response_model=InvestigationSettingsOut)
def reset_settings(investigation_id: int, session: SessionDep):
    """Resets to the defaults and returns them, so the client needs no second call."""
    return settings_service.reset_settings(session, investigation_id)
