"""Documents: create, update, delete, list and get (api.md section 2), the duplicate-key check
(B14, BD4), and conversion between ORM rows and schemas.

Every successful write commits straight away and updates the investigation's `updated_at`
(api.md 2.6, B2). Placeholders are never stored: list and get run the relationship resolution
over the saved documents each time (B4).
"""

from collections.abc import Sequence
from datetime import date, datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from txnweave_api.db import models
from txnweave_api.schemas.common import DocumentStatus, DocumentType
from txnweave_api.schemas.documents import (
    AnyDocumentOut,
    GiftCardActivationOut,
    GiftCardHistoryEntryOut,
    GiftCardIn,
    GiftCardOut,
    MiscIn,
    MiscOut,
    OnlineOrderIn,
    OnlineOrderOut,
    PaymentOut,
    TransactionIn,
    TransactionOut,
)
from txnweave_api.services.errors import AppError, not_found
from txnweave_api.services.keys import transaction_key
from txnweave_api.services.relationship_service import resolve
from txnweave_api.services.titles import gift_card_title, online_order_title, transaction_title

DocumentIn = TransactionIn | GiftCardIn | OnlineOrderIn | MiscIn

TYPE_ORDER: list[DocumentType] = ["transaction", "gift_card", "online_order", "misc"]


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def require_investigation(session: Session, investigation_id: int) -> models.Investigation:
    investigation = session.get(models.Investigation, investigation_id)
    if investigation is None:
        raise not_found("Investigation")
    return investigation


# ---- Reading ----


def _load_saved(session: Session, investigation_id: int) -> list[models.Document]:
    statement = (
        select(models.Document)
        .where(models.Document.investigation_id == investigation_id)
        .options(
            selectinload(models.Document.transaction),
            selectinload(models.Document.gift_card),
            selectinload(models.Document.online_order),
            selectinload(models.Document.misc),
            selectinload(models.Document.payments),
            selectinload(models.Document.history_entries),
        )
        .order_by(models.Document.id)
    )
    return list(session.scalars(statement))


def to_out(row: models.Document) -> AnyDocumentOut:
    """A saved document as its `*Out` schema, with its title (BD24). `referenced_by` is filled
    in later by list_documents."""
    base = {
        "id": str(row.id),
        "investigation_id": row.investigation_id,
        "status": "complete",
        "important": row.important,
        "notes": row.notes,
        "created_at": row.created_at,
        "updated_at": row.updated_at,
    }
    payments = [
        PaymentOut(type=p.type, gift_card_number=p.gift_card_number, amount_cents=p.amount_cents)
        for p in row.payments
    ]

    if row.transaction is not None:
        t = row.transaction
        on = date.fromisoformat(t.date)
        return TransactionOut(
            **base,
            type="transaction",
            title=transaction_title(t.transaction_number, on, t.store_number, t.register_number),
            transaction_number=t.transaction_number,
            date=on,
            time=t.time,
            store_number=t.store_number,
            register_number=t.register_number,
            payments=payments,
        )

    if row.gift_card is not None:
        g = row.gift_card
        return GiftCardOut(
            **base,
            type="gift_card",
            title=gift_card_title(g.gift_card_number),
            gift_card_number=g.gift_card_number,
            activation=GiftCardActivationOut(
                transaction_number=g.activation_transaction_number,
                date=date.fromisoformat(g.activation_date),
                time=g.activation_time,
                store_number=g.activation_store_number,
                amount_cents=g.activation_amount_cents,
            ),
            history=[
                GiftCardHistoryEntryOut(
                    transaction_number=h.transaction_number,
                    date=date.fromisoformat(h.date),
                    time=h.time,
                    store_number=h.store_number,
                    amount_cents=h.amount_cents,
                )
                for h in row.history_entries
            ],
        )

    if row.online_order is not None:
        o = row.online_order
        return OnlineOrderOut(
            **base,
            type="online_order",
            title=online_order_title(o.order_number),
            order_number=o.order_number,
            placed_date=date.fromisoformat(o.placed_date),
            placed_time=o.placed_time,
            customer_city=o.customer_city,
            customer_state=o.customer_state,
            pickup_store_number=o.pickup_store_number,
            payments=payments,
        )

    m = row.misc
    assert m is not None, f"document {row.id} has no detail row"
    return MiscOut(
        **base,
        type="misc",
        title=m.name,
        name=m.name,
        date=date.fromisoformat(m.date),
        time=m.time,
        transaction_number=m.transaction_number,
        order_number=m.order_number,
        payments=payments,
    )


def document_order(doc: AnyDocumentOut) -> tuple:
    """3.12: by type, then by key tuple or name, then by id. The graph uses it too."""
    if isinstance(doc, TransactionOut):
        key: tuple = (
            doc.transaction_number or "",
            doc.date.isoformat() if doc.date else "",
            doc.store_number or "",
            doc.register_number or "",
        )
    elif isinstance(doc, GiftCardOut):
        key = (doc.gift_card_number or "",)
    elif isinstance(doc, OnlineOrderOut):
        key = (doc.order_number or "",)
    else:
        key = (doc.name or "",)
    id_key = (0, int(doc.id), "") if doc.id.isdigit() else (1, 0, doc.id)
    return (TYPE_ORDER.index(doc.type), key, id_key)


def saved_documents(session: Session, investigation_id: int) -> list[AnyDocumentOut]:
    """Every saved document of the investigation (no placeholders). 404 if it doesn't exist."""
    require_investigation(session, investigation_id)
    return [to_out(row) for row in _load_saved(session, investigation_id)]


def list_documents(
    session: Session,
    investigation_id: int,
    types: Sequence[DocumentType] | None = None,
    status: DocumentStatus | None = None,
) -> list[AnyDocumentOut]:
    """Saved documents and placeholders, each with its `referenced_by` (api.md GET documents)."""
    saved = saved_documents(session, investigation_id)
    resolution = resolve(investigation_id, saved)

    documents = [
        doc.model_copy(update={"referenced_by": resolution.referenced_by.get(doc.id, [])})
        for doc in [*saved, *resolution.placeholders]
    ]
    if types:
        documents = [doc for doc in documents if doc.type in types]
    if status:
        documents = [doc for doc in documents if doc.status == status]
    return sorted(documents, key=document_order)


def get_document(session: Session, investigation_id: int, doc_id: str) -> AnyDocumentOut:
    """Works for placeholder IDs too (api.md)."""
    for doc in list_documents(session, investigation_id):
        if doc.id == doc_id:
            return doc
    raise not_found("Document")


# ---- Writing ----


def _saved_row(session: Session, investigation_id: int, doc_id: str) -> models.Document:
    """The saved document to change or delete. Placeholders can't be changed (api.md 2.5)."""
    require_investigation(session, investigation_id)
    if doc_id.startswith("ph-"):
        raise AppError(
            409,
            "placeholder_not_editable",
            "Incomplete documents can't be changed or deleted. Save a new document to complete it.",
        )
    row = session.get(models.Document, int(doc_id)) if doc_id.isdigit() else None
    if row is None or row.investigation_id != investigation_id:
        raise not_found("Document")
    return row


def _check_unique(session: Session, investigation_id: int, data: DocumentIn, exclude_id: int | None) -> None:
    """B14 / BD4: a key that already belongs to another saved document in the same investigation
    is a 409 with `existing_id`. Matching a placeholder is never a conflict (that's promotion)."""
    D = models.Document
    existing_id: int | None = None
    message = ""

    if isinstance(data, TransactionIn):
        T = models.TransactionDetails
        rows = session.execute(
            select(D.id, T.store_number, T.register_number)
            .join(T, T.document_id == D.id)
            .where(
                D.investigation_id == investigation_id,
                T.transaction_number == data.transaction_number,
                T.date == data.date.isoformat(),
            )
        ).all()
        wanted = transaction_key(data)
        for doc_id, store, register in rows:
            # The full key tuple: a blank register counts as "" (BD1).
            if doc_id != exclude_id and (store, register or "") == wanted[2:]:
                existing_id = doc_id
                break
        message = "A transaction with this number, date, store and register already exists."

    elif isinstance(data, GiftCardIn):
        G = models.GiftCardDetails
        existing_id = session.scalar(
            select(D.id)
            .join(G, G.document_id == D.id)
            .where(D.investigation_id == investigation_id, G.gift_card_number == data.gift_card_number, D.id != (exclude_id or -1))
        )
        message = "A gift card with this number already exists."  # never echo the number (B13)

    elif isinstance(data, OnlineOrderIn):
        O = models.OnlineOrderDetails
        existing_id = session.scalar(
            select(D.id)
            .join(O, O.document_id == D.id)
            .where(D.investigation_id == investigation_id, O.order_number == data.order_number, D.id != (exclude_id or -1))
        )
        message = "An online order with this number already exists."

    # Misc has no key (B14).
    if existing_id is not None:
        raise AppError(409, "duplicate_key", message, existing_id=str(existing_id))


def _apply_fields(row: models.Document, data: DocumentIn) -> None:
    """Copy a validated body onto the row. Child rows are replaced wholesale (persistence
    "Updates"); the 1:1 detail row is updated in place so its primary key never clashes."""
    row.notes = data.notes
    row.important = data.important

    payments = [] if isinstance(data, GiftCardIn) else data.payments
    row.payments = [
        models.Payment(position=i, type=p.type, gift_card_number=p.gift_card_number, amount_cents=p.amount_cents)
        for i, p in enumerate(payments)
    ]

    if isinstance(data, TransactionIn):
        details = row.transaction or models.TransactionDetails()
        details.transaction_number = data.transaction_number
        details.date = data.date.isoformat()
        details.time = data.time
        details.store_number = data.store_number
        details.register_number = data.register_number
        row.transaction = details

    elif isinstance(data, GiftCardIn):
        details = row.gift_card or models.GiftCardDetails()
        details.gift_card_number = data.gift_card_number
        details.activation_transaction_number = data.activation.transaction_number
        details.activation_date = data.activation.date.isoformat()
        details.activation_time = data.activation.time
        details.activation_store_number = data.activation.store_number
        details.activation_amount_cents = data.activation.amount_cents
        row.gift_card = details
        row.history_entries = [
            models.GiftCardHistoryEntry(
                position=i,
                transaction_number=h.transaction_number,
                date=h.date.isoformat(),
                time=h.time,
                store_number=h.store_number,
                amount_cents=h.amount_cents,
            )
            for i, h in enumerate(data.history)
        ]

    elif isinstance(data, OnlineOrderIn):
        details = row.online_order or models.OnlineOrderDetails()
        details.order_number = data.order_number
        details.placed_date = data.placed_date.isoformat()
        details.placed_time = data.placed_time
        details.customer_city = data.customer_city
        details.customer_state = data.customer_state
        details.pickup_store_number = data.pickup_store_number
        row.online_order = details

    else:
        details = row.misc or models.MiscDetails()
        details.name = data.name
        details.date = data.date.isoformat()
        details.time = data.time
        details.transaction_number = data.transaction_number
        details.order_number = data.order_number
        row.misc = details


def insert_document(session: Session, investigation: models.Investigation, data: DocumentIn, now: str) -> models.Document:
    """Add a new document row without committing or checking its key. create_document and
    the CSV import (which checks keys within the file itself) both use it."""
    row = models.Document(investigation=investigation, type=data.type, created_at=now, updated_at=now)
    _apply_fields(row, data)
    session.add(row)
    return row


def create_document(session: Session, investigation_id: int, data: DocumentIn) -> AnyDocumentOut:
    investigation = require_investigation(session, investigation_id)
    _check_unique(session, investigation_id, data, exclude_id=None)

    now = now_iso()
    row = insert_document(session, investigation, data, now)
    investigation.updated_at = now
    session.commit()
    return get_document(session, investigation_id, str(row.id))


def update_document(session: Session, investigation_id: int, doc_id: str, data: DocumentIn) -> AnyDocumentOut:
    """PUT replaces the whole document (api.md 2.3). The type can't change."""
    row = _saved_row(session, investigation_id, doc_id)
    if data.type != row.type:
        raise AppError(422, "type_change_not_allowed", "A document's type can't be changed.")
    _check_unique(session, investigation_id, data, exclude_id=row.id)

    now = now_iso()
    _apply_fields(row, data)
    row.updated_at = now
    row.investigation.updated_at = now
    session.commit()
    return get_document(session, investigation_id, doc_id)


def delete_document(session: Session, investigation_id: int, doc_id: str) -> None:
    """References to it re-resolve on the next read (api.md 2.4): to another match, a
    placeholder, or an ambiguous set."""
    row = _saved_row(session, investigation_id, doc_id)
    row.investigation.updated_at = now_iso()
    session.delete(row)
    session.commit()
