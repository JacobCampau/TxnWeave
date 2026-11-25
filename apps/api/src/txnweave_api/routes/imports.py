"""CSV Save and Load endpoints (api.md "Endpoints", csv-save-load.md). Thin: the work is in
csv_service."""

from typing import Annotated

from fastapi import APIRouter, File, Query, Response, UploadFile

from txnweave_api.config import MAX_IMPORT_BYTES
from txnweave_api.db.database import SessionDep
from txnweave_api.schemas.imports import ImportReport, ImportResult
from txnweave_api.services import csv_service

router = APIRouter(prefix="/investigations", tags=["csv"])


@router.get("/{investigation_id}/export.csv")
def export_csv(investigation_id: int, session: SessionDep) -> Response:
    filename, text = csv_service.export_csv(session, investigation_id)
    return Response(
        content=text.encode("utf-8"),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.post("/import", response_model=ImportReport | ImportResult)
def import_csv(
    session: SessionDep,
    response: Response,
    file: Annotated[UploadFile, File()],
    dry_run: Annotated[bool, Query()],
):
    """Dry run: 200 with the report. Otherwise: 201 with the new investigation and the report.
    A missing file part is FastAPI's own 422."""
    data = file.file.read(MAX_IMPORT_BYTES + 1)  # one byte over is enough to know it's too big
    result = csv_service.import_csv(session, data, dry_run)
    if not dry_run:
        response.status_code = 201
    return result
