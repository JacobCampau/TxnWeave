"""CSV Save and Load (csv-save-load.md): one sectioned UTF-8 file per investigation (BD9).

Export writes every saved document (placeholders are recreated on load, 5.4), joined through
export-local `ref` / `parent_ref` columns (BD10), and the effective settings last (BD33).
"""

import csv
import io
import re
from collections.abc import Sequence
from dataclasses import dataclass, field
from datetime import date, datetime, timezone

from pydantic import ValidationError
from sqlalchemy.orm import Session

from txnweave_api.config import MAX_IMPORT_BYTES
from txnweave_api.db import models
from txnweave_api.schemas.documents import (
    AnyDocumentOut,
    GiftCardHistoryEntryIn,
    GiftCardIn,
    GiftCardOut,
    MiscIn,
    MiscOut,
    OnlineOrderIn,
    OnlineOrderOut,
    PaymentIn,
    PaymentOut,
    TransactionIn,
    TransactionOut,
)
from txnweave_api.schemas.imports import ImportCounts, ImportProblem, ImportReport, ImportResult
from txnweave_api.schemas.investigation import InvestigationCreate
from txnweave_api.schemas.settings import DEFAULT_SETTINGS, DOCUMENT_TYPES, InvestigationSettingsIn, NodeStyles, TypeStyle
from txnweave_api.services import document_service, investigation_service, settings_service
from txnweave_api.services.document_service import DocumentIn, now_iso, require_investigation
from txnweave_api.services.errors import AppError
from txnweave_api.services.keys import transaction_key
from txnweave_api.services.money import MoneyCellError, format_money_cell, parse_money_cell
from txnweave_api.services.settings_service import find_clashes
from txnweave_api.services.titles import gift_card_title, online_order_title, transaction_title

MARKER = ["TXNWEAVE_SAVE", "format_version", "1"]  # BD12

# The column layout (5.10). Import matches headers by name.
COLUMNS: dict[str, list[str]] = {
    "transactions": ["ref", "transaction_number", "date", "time", "store_number", "register_number", "important", "notes"],
    "gift_cards": [
        "ref", "gift_card_number", "activation_transaction_number", "activation_date", "activation_time",
        "activation_store_number", "activation_amount ($)", "important", "notes",
    ],
    "online_orders": [
        "ref", "order_number", "placed_date", "placed_time", "customer_city", "customer_state",
        "pickup_store_number", "important", "notes",
    ],
    "misc": ["ref", "name", "date", "time", "transaction_number", "order_number", "important", "notes"],
    "payments": ["parent_ref", "type", "gift_card_number", "amount ($)"],
    "gift_card_history": ["parent_ref", "transaction_number", "date", "time", "store_number", "amount ($)"],
    "settings": ["setting", "color", "shape"],
}

REF_PREFIX = {"transaction": "T", "gift_card": "G", "online_order": "O", "misc": "M"}


# ---- Cell writing rules (5.5) ----


def _text(value: str | None) -> str:
    """Free text. A leading =, +, -, @, tab or carriage return could run as a spreadsheet
    formula, so it gets a ' prefix (import strips one again, 5.6)."""
    if not value:
        return ""
    return "'" + value if value[0] in "=+-@\t\r" else value


def _date(value: date | None) -> str:
    return value.strftime("%m-%d-%Y") if value else ""


def _money(cents: int | None) -> str:
    return "" if cents is None else format_money_cell(cents)  # never escaped (BD11)


def _bool(value: bool) -> str:
    return "true" if value else "false"


def _plain(value: str | None) -> str:
    """Digit strings, times and enum values: written as they are (no formula risk)."""
    return value or ""


# ---- Export ----


def _filename(name: str | None) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", (name or "").lower()).strip("-")
    return f"{slug or 'untitled-investigation'}.csv"


def _document_rows(docs: Sequence[AnyDocumentOut]) -> tuple[dict[str, list[list[str]]], dict[str, str]]:
    """The four document sections, plus each document's ref by id."""
    sections: dict[str, list[list[str]]] = {"transactions": [], "gift_cards": [], "online_orders": [], "misc": []}
    refs: dict[str, str] = {}
    counts = {doc_type: 0 for doc_type in REF_PREFIX}

    for doc in docs:  # already in the 3.12 order, so refs are stable for the same data
        counts[doc.type] += 1
        ref = f"{REF_PREFIX[doc.type]}{counts[doc.type]}"
        refs[doc.id] = ref
        tail = [_bool(doc.important), _text(doc.notes)]
        if isinstance(doc, TransactionOut):
            sections["transactions"].append(
                [ref, _plain(doc.transaction_number), _date(doc.date), _plain(doc.time),
                 _plain(doc.store_number), _plain(doc.register_number), *tail]
            )
        elif isinstance(doc, GiftCardOut):
            a = doc.activation
            sections["gift_cards"].append(
                [ref, _plain(doc.gift_card_number), _plain(a.transaction_number if a else None),
                 _date(a.date if a else None), _plain(a.time if a else None),
                 _plain(a.store_number if a else None), _money(a.amount_cents if a else None), *tail]
            )
        elif isinstance(doc, OnlineOrderOut):
            sections["online_orders"].append(
                [ref, _plain(doc.order_number), _date(doc.placed_date), _plain(doc.placed_time),
                 _text(doc.customer_city), _text(doc.customer_state), _plain(doc.pickup_store_number), *tail]
            )
        else:
            sections["misc"].append(
                [ref, _text(doc.name), _date(doc.date), _plain(doc.time),
                 _plain(doc.transaction_number), _plain(doc.order_number), *tail]
            )
    return sections, refs


def _payment_row(parent_ref: str, payment: PaymentOut) -> list[str]:
    return [parent_ref, payment.type, _plain(payment.gift_card_number), _money(payment.amount_cents)]


def _settings_rows(settings: InvestigationSettingsIn) -> list[list[str]]:
    rows = []
    for doc_type in DOCUMENT_TYPES:
        style = getattr(settings.node_styles, doc_type)
        rows.append([doc_type, style.color, style.shape])
    rows.append(["important_edge", settings.important_edge_color, ""])
    return rows


def build_csv(name: str | None, exported_at: str, docs: Sequence[AnyDocumentOut], settings: InvestigationSettingsIn) -> str:
    """Pure: the whole file as text, with a UTF-8 BOM (5.1)."""
    ordered = sorted(docs, key=document_service.document_order)
    sections, refs = _document_rows(ordered)

    # Child rows follow their parent's order and their own row order (5.10).
    sections["payments"] = [
        _payment_row(refs[doc.id], payment)
        for doc in ordered
        if isinstance(doc, (TransactionOut, OnlineOrderOut, MiscOut))
        for payment in doc.payments
    ]
    sections["gift_card_history"] = [
        [refs[doc.id], _plain(h.transaction_number), _date(h.date), _plain(h.time), _plain(h.store_number), _money(h.amount_cents)]
        for doc in ordered
        if isinstance(doc, GiftCardOut)
        for h in doc.history
    ]
    sections["settings"] = _settings_rows(settings)

    out = io.StringIO()
    writer = csv.writer(out)
    writer.writerow(MARKER)
    writer.writerow(["investigation_name", _text(name), "exported_at", exported_at])
    for section, columns in COLUMNS.items():
        writer.writerow([])
        writer.writerow(["section", section])
        writer.writerow(columns)
        writer.writerows(sections[section])
    return "﻿" + out.getvalue()


def export_csv(session: Session, investigation_id: int) -> tuple[str, str]:
    """GET .../export.csv: (filename, file text). Sets `last_exported_at` (B16), which clears
    `has_unsaved_changes` until the next change."""
    investigation = require_investigation(session, investigation_id)
    docs = document_service.saved_documents(session, investigation_id)
    settings = settings_service.get_settings(session, investigation_id)

    now = now_iso()
    exported_at = datetime.fromisoformat(now).astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    text = build_csv(investigation.name, exported_at, docs, settings)  # Out extends In
    investigation.last_exported_at = now
    session.commit()
    return _filename(investigation.name), text


# ---- Import (5.2, 5.6 to 5.10) ----


@dataclass
class _Row:
    number: int  # row number in the file, counting from 1
    cells: dict[str, str]  # by header name; a column missing from the header is absent


@dataclass
class _Child:
    row: _Row
    data: dict


@dataclass
class _DocEntry:
    section: str
    row: _Row
    doc_type: str
    ref: str
    children: list[_Child] = field(default_factory=list)


class _Report:
    """Collects problems and counts while the file is read."""

    def __init__(self) -> None:
        self.problems: list[ImportProblem] = []
        self.skipped: set[tuple[str, int]] = set()

    def error(self, section: str, row: int, column: str | None, code: str, message: str) -> None:
        self.problems.append(ImportProblem(severity="error", section=section, row=row, field=column, code=code, message=message))
        self.skipped.add((section, row))

    def warning(self, section: str, row: int | None, column: str | None, code: str, message: str) -> None:
        self.problems.append(ImportProblem(severity="warning", section=section, row=row, field=column, code=code, message=message))


DOCUMENT_SECTIONS = {"transactions": "transaction", "gift_cards": "gift_card", "online_orders": "online_order", "misc": "misc"}
_DOC_MODELS = {"transaction": TransactionIn, "gift_card": GiftCardIn, "online_order": OnlineOrderIn, "misc": MiscIn}
_DATE_CELL = re.compile(r"^(\d{2})-(\d{2})-(\d{4})$")
_TRUE, _FALSE = {"true", "yes", "1"}, {"false", "no", "0", ""}


class _CellError(Exception):
    def __init__(self, column: str, code: str, message: str) -> None:
        self.column, self.code, self.message = column, code, message


def _read_rows(data: bytes) -> list[list[str]]:
    """Size, encoding and the marker (5.7, 5.8, BD34), before anything is parsed."""
    if len(data) > MAX_IMPORT_BYTES:
        raise AppError(413, "file_too_large", "This file is larger than 5 MB.")
    try:
        text = data.decode("utf-8-sig")  # also removes a BOM
        rows = list(csv.reader(io.StringIO(text, newline="")))
    except (UnicodeDecodeError, csv.Error):
        raise AppError(422, "unreadable_file", "This file could not be read.") from None

    first = rows[0] if rows else []
    if first[:3] != MARKER or any(cell.strip() for cell in first[3:]):
        raise AppError(422, "not_a_txnweave_file", "This file is not a TxnWeave save file.")
    return rows


def _cell(text: str) -> str:
    """One leading ' is stripped from any cell (5.6): it is the export's formula escape."""
    return text[1:] if text.startswith("'") else text


def _split_sections(rows: list[list[str]], report: _Report) -> dict[str, list[_Row]]:
    """5.10: a `section,<name>` row, then a header row, then data rows. Fully blank rows are
    separators. A section that appears twice is read as one."""
    sections: dict[str, list[_Row]] = {name: [] for name in COLUMNS}
    current: str | None = None  # None: before the first section, or in an unknown one
    header: list[str] | None = None
    for number, row in enumerate(rows[2:], start=3):
        if not any(cell.strip() for cell in row):
            continue
        if row[0].strip() == "section":
            name = row[1].strip() if len(row) > 1 else ""
            current = name if name in COLUMNS else None
            header = None
            if current is None:
                report.warning(name, number, None, "unknown_section", "Unknown section; its rows were skipped")
            continue
        if current is None:
            continue
        if header is None:
            header = [cell.strip() for cell in row]
            continue
        cells: dict[str, str] = {}
        for index, column in enumerate(header):
            if column:  # the first column with a name wins
                cells.setdefault(column, _cell(row[index]) if index < len(row) else "")
        sections[current].append(_Row(number, cells))
    return sections


def _put(out: dict, key: str, row: _Row, column: str, kind: str = "text") -> None:
    """Copy one cell into the model input. A blank or missing cell is left out, so a required
    field reports `missing_required` and an optional one becomes null."""
    value = row.cells.get(column, "").strip()
    if not value:
        return
    if kind == "date":
        match = _DATE_CELL.match(value)
        if match is None:
            raise _CellError(column, "invalid_format", "Must be a date like 03-14-2026")
        month, day, year = match.groups()
        out[key] = f"{year}-{month}-{day}"  # an impossible date like 02-30 fails validation
    elif kind == "money":
        try:
            out[key] = parse_money_cell(value)
        except MoneyCellError as error:
            raise _CellError(column, error.code, str(error)) from None
    else:
        out[key] = value


def _important(row: _Row, section: str, report: _Report) -> bool:
    value = row.cells.get("important", "").strip().lower()
    if value in _TRUE:
        return True
    if value not in _FALSE:
        report.warning(section, row.number, "important", "invalid_format", "Must be true or false; imported as false")
    return False


def _document_input(entry: _DocEntry, report: _Report) -> dict:
    row, out = entry.row, {"type": entry.doc_type}
    if entry.doc_type == "transaction":
        _put(out, "transaction_number", row, "transaction_number")
        _put(out, "date", row, "date", "date")
        _put(out, "time", row, "time")
        _put(out, "store_number", row, "store_number")
        _put(out, "register_number", row, "register_number")
    elif entry.doc_type == "gift_card":
        _put(out, "gift_card_number", row, "gift_card_number")
        activation: dict = {}
        _put(activation, "transaction_number", row, "activation_transaction_number")
        _put(activation, "date", row, "activation_date", "date")
        _put(activation, "time", row, "activation_time")
        _put(activation, "store_number", row, "activation_store_number")
        _put(activation, "amount_cents", row, "activation_amount ($)", "money")
        out["activation"] = activation
    elif entry.doc_type == "online_order":
        _put(out, "order_number", row, "order_number")
        _put(out, "placed_date", row, "placed_date", "date")
        _put(out, "placed_time", row, "placed_time")
        _put(out, "customer_city", row, "customer_city")
        _put(out, "customer_state", row, "customer_state")
        _put(out, "pickup_store_number", row, "pickup_store_number")
    else:
        _put(out, "name", row, "name")
        _put(out, "date", row, "date", "date")
        _put(out, "time", row, "time")
        _put(out, "transaction_number", row, "transaction_number")
        _put(out, "order_number", row, "order_number")
    _put(out, "notes", row, "notes")
    out["important"] = _important(row, entry.section, report)
    return out


def _child_input(section: str, row: _Row) -> dict:
    out: dict = {}
    if section == "payments":
        _put(out, "type", row, "type")
        _put(out, "gift_card_number", row, "gift_card_number")
    else:
        _put(out, "transaction_number", row, "transaction_number")
        _put(out, "date", row, "date", "date")
        _put(out, "time", row, "time")
        _put(out, "store_number", row, "store_number")
    _put(out, "amount_cents", row, "amount ($)", "money")
    return out


def _report_validation(error: ValidationError, section: str, row: int, report: _Report) -> None:
    """Pydantic's errors as problems. Its messages never contain the rejected value."""
    for item in error.errors():
        loc = [str(part) for part in item["loc"]]
        column = "_".join(loc).replace("amount_cents", "amount ($)")
        kind = item["type"]
        if kind == "missing":
            report.error(section, row, column, "missing_required", "Required")
        elif kind == "too_short" and loc == ["payments"]:
            report.error(section, row, "payments", "missing_required", "Needs at least 1 valid payment row")
        elif kind in {"greater_than", "greater_than_equal", "less_than", "less_than_equal"}:
            report.error(section, row, column, "out_of_range", item["msg"])
        else:
            report.error(section, row, column, "invalid_format", item["msg"])


def _natural_key(doc: DocumentIn) -> tuple | None:
    """The in-file duplicate check (5.7) uses the same keys as B14. Misc has none."""
    if isinstance(doc, TransactionIn):
        return ("transaction", *transaction_key(doc))
    if isinstance(doc, GiftCardIn):
        return ("gift_card", doc.gift_card_number)
    if isinstance(doc, OnlineOrderIn):
        return ("online_order", doc.order_number)
    return None


def _title(doc: DocumentIn) -> str:
    if isinstance(doc, TransactionIn):
        return transaction_title(doc.transaction_number, doc.date, doc.store_number, doc.register_number)
    if isinstance(doc, GiftCardIn):
        return gift_card_title(doc.gift_card_number)  # last 4 digits only (B13)
    return online_order_title(doc.order_number)  # type: ignore[union-attr]


def _read_documents(sections: dict[str, list[_Row]], report: _Report) -> list[DocumentIn]:
    entries: list[_DocEntry] = []
    by_ref: dict[str, _DocEntry] = {}
    for section, doc_type in DOCUMENT_SECTIONS.items():
        for row in sections[section]:
            ref = row.cells.get("ref", "").strip()
            if ref and ref in by_ref:
                report.error(section, row.number, "ref", "invalid_format", f"Duplicate ref {ref}; the first row with it was kept")
                continue
            entry = _DocEntry(section, row, doc_type, ref)
            entries.append(entry)
            if ref:
                by_ref[ref] = entry

    # Child rows are checked on their own first, so one bad payment doesn't hide the others.
    for section, child_model in (("payments", PaymentIn), ("gift_card_history", GiftCardHistoryEntryIn)):
        for row in sections[section]:
            parent_ref = row.cells.get("parent_ref", "").strip()
            parent = by_ref.get(parent_ref)
            fits = parent is not None and (parent.doc_type == "gift_card") == (section == "gift_card_history")
            if not fits:
                report.error(section, row.number, "parent_ref", "unknown_parent_ref", f"No matching document row has ref {parent_ref or '(blank)'}")
                continue
            try:
                data = _child_input(section, row)
                child_model.model_validate(data)
            except _CellError as error:
                report.error(section, row.number, error.column, error.code, error.message)
                continue
            except ValidationError as error:
                _report_validation(error, section, row.number, report)
                continue
            parent.children.append(_Child(row, data))

    documents: list[DocumentIn] = []
    seen: dict[tuple, int] = {}
    for entry in entries:
        document = _validate_document(entry, report)
        if document is not None:
            key = _natural_key(document)
            if key is not None and key in seen:
                report.error(entry.section, entry.row.number, None, "duplicate_key", f"Duplicate of row {seen[key]} ({_title(document)})")
                document = None
            elif key is not None:
                seen[key] = entry.row.number
        if document is None:
            child_section = "gift_card_history" if entry.doc_type == "gift_card" else "payments"
            for child in entry.children:
                report.error(child_section, child.row.number, "parent_ref", "parent_skipped", f"Its document row {entry.ref} was skipped")
        else:
            documents.append(document)
    return documents


def _validate_document(entry: _DocEntry, report: _Report) -> DocumentIn | None:
    try:
        data = _document_input(entry, report)
    except _CellError as error:
        report.error(entry.section, entry.row.number, error.column, error.code, error.message)
        return None
    children = [child.data for child in entry.children]
    data["history" if entry.doc_type == "gift_card" else "payments"] = children
    try:
        return _DOC_MODELS[entry.doc_type].model_validate(data)
    except ValidationError as error:
        _report_validation(error, entry.section, entry.row.number, report)
        return None


def _read_settings(rows: list[_Row], report: _Report) -> InvestigationSettingsIn:
    """5.9: settings never stop documents importing. A bad entry keeps its default."""
    styles = {doc_type: getattr(DEFAULT_SETTINGS.node_styles, doc_type) for doc_type in DOCUMENT_TYPES}
    edge_color = DEFAULT_SETTINGS.important_edge_color
    seen: set[str] = set()
    for row in rows:
        name, color, shape = (row.cells.get(column, "").strip() for column in ("setting", "color", "shape"))
        if name in seen:
            report.warning("settings", row.number, "setting", "invalid_setting", "Duplicate setting; the first one was kept")
            continue
        seen.add(name)
        try:
            if name in DOCUMENT_TYPES:
                styles[name] = TypeStyle(color=color, shape=shape)
            elif name == "important_edge":
                if shape:
                    raise ValueError("important_edge has no shape")
                edge_color = InvestigationSettingsIn(node_styles=DEFAULT_SETTINGS.node_styles, important_edge_color=color).important_edge_color
            else:
                report.warning("settings", row.number, "setting", "invalid_setting", "Unknown setting; it was ignored")
        except (ValidationError, ValueError):
            report.warning("settings", row.number, None, "invalid_setting", "Not a valid color or shape; the default is used")

    settings = InvestigationSettingsIn(node_styles=NodeStyles(**styles), important_edge_color=edge_color)
    if find_clashes(settings):
        report.warning("settings", None, None, "indistinct_styles", "Two document types looked the same; all node styles use the defaults")
        settings = InvestigationSettingsIn(node_styles=DEFAULT_SETTINGS.node_styles, important_edge_color=edge_color)
    return settings


def _name(rows: list[list[str]]) -> str | None:
    """Row 2 gives the name. A missing or malformed row 2 means no name, with no problem."""
    if len(rows) < 2 or not rows[1] or rows[1][0].strip() != "investigation_name" or len(rows[1]) < 2:
        return None
    try:
        return InvestigationCreate(name=_cell(rows[1][1])).name or None
    except ValidationError:
        return None


def import_csv(session: Session, data: bytes, dry_run: bool) -> ImportReport | ImportResult:
    """POST /investigations/import. Always a new investigation (BD13). A dry run writes
    nothing; otherwise the valid rows are written in one transaction."""
    rows = _read_rows(data)
    report = _Report()
    sections = _split_sections(rows, report)
    documents = _read_documents(sections, report)
    settings = _read_settings(sections["settings"], report)

    section_order = list(COLUMNS)
    report.problems.sort(key=lambda p: (section_order.index(p.section) if p.section in section_order else -1, p.row or 0))
    counts = ImportCounts(
        rows_read=sum(len(sections[name]) for name in COLUMNS if name != "settings"),
        documents_imported=len(documents),
        rows_skipped=len(report.skipped),
    )
    result = ImportReport(counts=counts, problems=report.problems)
    if dry_run:
        return result

    now = now_iso()
    # A just-loaded investigation matches its file, so it starts with no unsaved changes (B16).
    investigation = models.Investigation(name=_name(rows), created_at=now, updated_at=now, last_exported_at=now)
    session.add(investigation)
    session.flush()  # gives the investigation its id
    for document in documents:
        document_service.insert_document(session, investigation, document, now)
    if settings != DEFAULT_SETTINGS:  # all defaults: no settings row (BD30)
        settings_service.write_settings_row(session, investigation, settings, now)
    session.commit()
    return ImportResult(investigation=investigation_service.to_out(session, investigation), report=result)
