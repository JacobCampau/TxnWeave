"""Document endpoints, nested under an investigation (api.md "Endpoints", B3, B9).

Thin: the work is in document_service. `doc_id` is text because placeholders have IDs like
"ph-transaction-5d0e7c21a9f4".
"""

from typing import Annotated

from fastapi import APIRouter, Body, Query, Response

from txnweave_api.db.database import SessionDep
from txnweave_api.schemas.common import DocumentStatus, DocumentType
from txnweave_api.schemas.documents import DocumentIn, DocumentOut
from txnweave_api.services import document_service

router = APIRouter(prefix="/investigations/{investigation_id}/documents", tags=["documents"])


@router.get("", response_model=list[DocumentOut])
def list_documents(
    investigation_id: int,
    session: SessionDep,
    type: Annotated[list[DocumentType] | None, Query()] = None,
    status: DocumentStatus | None = None,
):
    return document_service.list_documents(session, investigation_id, type, status)


@router.get("/{doc_id}", response_model=DocumentOut)
def get_document(investigation_id: int, doc_id: str, session: SessionDep):
    return document_service.get_document(session, investigation_id, doc_id)


@router.post("", response_model=DocumentOut, status_code=201)
def create_document(investigation_id: int, body: Annotated[DocumentIn, Body()], session: SessionDep):
    return document_service.create_document(session, investigation_id, body)


@router.put("/{doc_id}", response_model=DocumentOut)
def update_document(investigation_id: int, doc_id: str, body: Annotated[DocumentIn, Body()], session: SessionDep):
    return document_service.update_document(session, investigation_id, doc_id, body)


@router.delete("/{doc_id}", status_code=204)
def delete_document(investigation_id: int, doc_id: str, session: SessionDep):
    document_service.delete_document(session, investigation_id, doc_id)
    return Response(status_code=204)
