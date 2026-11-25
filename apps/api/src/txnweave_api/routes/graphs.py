"""Graph endpoint (api.md "Endpoints", graph-output.md). Thin: the work is in graph_service."""

from fastapi import APIRouter

from txnweave_api.db.database import SessionDep
from txnweave_api.schemas.graph import GraphOut
from txnweave_api.services import graph_service

router = APIRouter(prefix="/investigations/{investigation_id}/graph", tags=["graph"])


@router.get("", response_model=GraphOut)
def get_graph(investigation_id: int, session: SessionDep):
    return graph_service.get_graph(session, investigation_id)
