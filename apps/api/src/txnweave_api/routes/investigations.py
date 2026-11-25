"""Investigation endpoints (api.md "Endpoints"). Thin: the work is in investigation_service."""

from fastapi import APIRouter, Response

from txnweave_api.db.database import SessionDep
from txnweave_api.schemas.investigation import InvestigationCreate, InvestigationOut, InvestigationUpdate
from txnweave_api.services import investigation_service

router = APIRouter(prefix="/investigations", tags=["investigations"])


@router.get("", response_model=list[InvestigationOut])
def list_investigations(session: SessionDep):
    return investigation_service.list_investigations(session)


@router.post("", response_model=InvestigationOut, status_code=201)
def create_investigation(session: SessionDep, body: InvestigationCreate | None = None):
    return investigation_service.create_investigation(session, body or InvestigationCreate())


@router.get("/{investigation_id}", response_model=InvestigationOut)
def get_investigation(investigation_id: int, session: SessionDep):
    return investigation_service.get_investigation(session, investigation_id)


@router.patch("/{investigation_id}", response_model=InvestigationOut)
def rename_investigation(investigation_id: int, body: InvestigationUpdate, session: SessionDep):
    return investigation_service.rename_investigation(session, investigation_id, body)


@router.delete("/{investigation_id}", status_code=204)
def delete_investigation(investigation_id: int, session: SessionDep):
    investigation_service.delete_investigation(session, investigation_id)
    return Response(status_code=204)
