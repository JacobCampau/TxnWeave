"""Investigations: create, list, get, rename and delete (api.md section 1, BD32)."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from txnweave_api.db import models
from txnweave_api.schemas.investigation import InvestigationCreate, InvestigationOut, InvestigationUpdate
from txnweave_api.services import document_service
from txnweave_api.services.document_service import now_iso, require_investigation


def to_out(session: Session, investigation: models.Investigation) -> InvestigationOut:
    documents = document_service.list_documents(session, investigation.id)
    saved_count = sum(1 for doc in documents if doc.status == "complete")

    # B16: "unsaved" means changed since the last CSV save. Timestamps are ISO text in the same
    # format, so comparing the strings compares the times.
    exported_at = investigation.last_exported_at
    if exported_at is None:
        has_unsaved_changes = saved_count > 0
    else:
        has_unsaved_changes = investigation.updated_at > exported_at

    return InvestigationOut(
        id=investigation.id,
        name=investigation.name,
        created_at=investigation.created_at,
        updated_at=investigation.updated_at,
        last_exported_at=exported_at,
        document_count=saved_count,
        incomplete_count=len(documents) - saved_count,
        has_unsaved_changes=has_unsaved_changes,
    )


def list_investigations(session: Session) -> list[InvestigationOut]:
    """Newest `updated_at` first: "Resume last session" uses the first one (api.md 1.2)."""
    rows = session.scalars(
        select(models.Investigation).order_by(models.Investigation.updated_at.desc(), models.Investigation.id.desc())
    )
    return [to_out(session, row) for row in rows]


def create_investigation(session: Session, data: InvestigationCreate) -> InvestigationOut:
    now = now_iso()
    investigation = models.Investigation(name=data.name or None, created_at=now, updated_at=now)
    session.add(investigation)
    session.commit()
    return to_out(session, investigation)


def get_investigation(session: Session, investigation_id: int) -> InvestigationOut:
    return to_out(session, require_investigation(session, investigation_id))


def rename_investigation(session: Session, investigation_id: int, data: InvestigationUpdate) -> InvestigationOut:
    """BD32: trimmed (by the schema); empty becomes null. The name is exported, so a rename
    counts as a change (updated_at)."""
    investigation = require_investigation(session, investigation_id)
    investigation.name = data.name or None
    investigation.updated_at = now_iso()
    session.commit()
    return to_out(session, investigation)


def delete_investigation(session: Session, investigation_id: int) -> None:
    """Cascades to all its documents (api.md 1.3)."""
    session.delete(require_investigation(session, investigation_id))
    session.commit()
