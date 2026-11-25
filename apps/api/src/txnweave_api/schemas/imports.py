"""The CSV import report (csv-save-load.md "ImportReport").

A report exists only for files with a valid marker (BD34). Messages never hold more than the
last 4 digits of a card number (B13).
"""

from typing import Literal

from pydantic import BaseModel

from txnweave_api.schemas.investigation import InvestigationOut

ProblemCode = Literal[
    "invalid_format",
    "missing_required",
    "out_of_range",
    "duplicate_key",
    "unknown_parent_ref",
    "parent_skipped",
    "invalid_setting",
    "indistinct_styles",
    "unknown_section",
]


class ImportProblem(BaseModel):
    severity: Literal["error", "warning"]  # error: the row was skipped; warning: it was imported
    section: str
    row: int | None  # the row number in the file, counting from 1
    field: str | None  # a column name
    code: ProblemCode
    message: str


class ImportCounts(BaseModel):
    rows_read: int
    documents_imported: int
    rows_skipped: int


class ImportReport(BaseModel):
    format_version: int = 1
    counts: ImportCounts
    problems: list[ImportProblem]


class ImportResult(BaseModel):
    """The response to a real (not dry-run) import: 201."""

    investigation: InvestigationOut
    report: ImportReport
