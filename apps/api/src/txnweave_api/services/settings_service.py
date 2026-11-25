"""Investigation settings: get with defaults, replace, reset (api.md section 7, BD29 to BD31)."""

from sqlalchemy.orm import Session

from txnweave_api.db import models
from txnweave_api.schemas.settings import (
    DEFAULT_SETTINGS,
    DOCUMENT_TYPES,
    InvestigationSettingsIn,
    InvestigationSettingsOut,
    NodeStyles,
    TypeStyle,
)
from txnweave_api.services.document_service import now_iso, require_investigation
from txnweave_api.services.errors import AppError


def _to_out(settings: InvestigationSettingsIn) -> InvestigationSettingsOut:
    return InvestigationSettingsOut(**settings.model_dump(), is_default=settings == DEFAULT_SETTINGS)


def _from_row(row: models.InvestigationSettings) -> InvestigationSettingsIn:
    styles = {
        doc_type: TypeStyle(color=getattr(row, f"{doc_type}_color"), shape=getattr(row, f"{doc_type}_shape"))
        for doc_type in DOCUMENT_TYPES
    }
    return InvestigationSettingsIn(node_styles=NodeStyles(**styles), important_edge_color=row.important_edge_color)


def find_clashes(settings: InvestigationSettingsIn) -> list[str]:
    """The document types that share a (color, shape) pair with another type (BD29)."""
    by_style: dict[tuple[str, str], list[str]] = {}
    for doc_type in DOCUMENT_TYPES:
        style: TypeStyle = getattr(settings.node_styles, doc_type)
        by_style.setdefault((style.color, style.shape), []).append(doc_type)
    return [doc_type for group in by_style.values() if len(group) > 1 for doc_type in group]


def get_settings(session: Session, investigation_id: int) -> InvestigationSettingsOut:
    """Never fails because no row exists: no row means the defaults (7.1)."""
    require_investigation(session, investigation_id)
    row = session.get(models.InvestigationSettings, investigation_id)
    return _to_out(_from_row(row) if row else DEFAULT_SETTINGS)


def replace_settings(
    session: Session, investigation_id: int, data: InvestigationSettingsIn
) -> InvestigationSettingsOut:
    """Create or replace the row (7.2). Settings are exported (BD33), so this is a change."""
    investigation = require_investigation(session, investigation_id)
    clashes = find_clashes(data)
    if clashes:
        raise AppError(
            422,
            "indistinct_styles",
            "Two or more document types have the same color and shape.",
            types=clashes,
        )

    now = now_iso()
    write_settings_row(session, investigation, data, now)
    investigation.updated_at = now
    session.commit()
    return _to_out(data)


def write_settings_row(
    session: Session, investigation: models.Investigation, data: InvestigationSettingsIn, now: str
) -> None:
    """Create or update the row without committing or checking distinctness. replace_settings
    and the CSV import (which checks distinctness itself, 5.9) both use it. The investigation
    must already have its id (flushed)."""
    row = session.get(models.InvestigationSettings, investigation.id)
    if row is None:
        row = models.InvestigationSettings(investigation_id=investigation.id)
        session.add(row)
    for doc_type in DOCUMENT_TYPES:
        style: TypeStyle = getattr(data.node_styles, doc_type)
        setattr(row, f"{doc_type}_color", style.color)
        setattr(row, f"{doc_type}_shape", style.shape)
    row.important_edge_color = data.important_edge_color
    row.updated_at = now


def reset_settings(session: Session, investigation_id: int) -> InvestigationSettingsOut:
    """Delete the row if there is one, and count that as a change (7.3)."""
    investigation = require_investigation(session, investigation_id)
    row = session.get(models.InvestigationSettings, investigation_id)
    if row is not None:
        session.delete(row)
        investigation.updated_at = now_iso()
        session.commit()
    return _to_out(DEFAULT_SETTINGS)
