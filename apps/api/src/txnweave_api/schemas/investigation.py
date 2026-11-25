"""Investigation schemas (api.md "Investigation entity", BD32)."""

import datetime as dt
from typing import Annotated

from pydantic import BaseModel, ConfigDict, StringConstraints

# Trimmed, at most 200 characters. An empty name is stored as null ("Untitled investigation").
InvestigationName = Annotated[str, StringConstraints(strip_whitespace=True, max_length=200)] | None


class InvestigationCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: InvestigationName = None


class InvestigationUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: InvestigationName  # required, but may be null


class InvestigationOut(BaseModel):
    id: int
    name: str | None
    created_at: dt.datetime
    updated_at: dt.datetime
    last_exported_at: dt.datetime | None
    document_count: int  # saved documents
    incomplete_count: int  # placeholders
    has_unsaved_changes: bool  # B16
