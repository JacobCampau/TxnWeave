"""Transaction keys and reference matching (data-model B14/BD1, relationship-resolution 3.3).

Small and pure, with its own tests.
"""

from dataclasses import dataclass
from datetime import date
from typing import Protocol


class HasTransactionKey(Protocol):
    transaction_number: str | None
    date: date | None
    store_number: str | None
    register_number: str | None


def transaction_key(doc: HasTransactionKey) -> tuple[str, str, str, str]:
    """A saved Transaction's identity, used for uniqueness. A blank register counts as "" (BD1)."""
    assert doc.transaction_number is not None and doc.date is not None and doc.store_number is not None
    return (doc.transaction_number, doc.date.isoformat(), doc.store_number, doc.register_number or "")


@dataclass(frozen=True)
class TxnRef:
    """The parts of a Transaction a reference knows. None means "not known": a wildcard (BD2).

    No reference ever knows a register number, so the register never affects matching.
    """

    number: str
    date: date | None
    store: str | None


def txn_ref_of(doc: HasTransactionKey) -> TxnRef:
    assert doc.transaction_number is not None
    return TxnRef(doc.transaction_number, doc.date, doc.store_number)


def matches(ref: TxnRef, candidate: TxnRef) -> bool:
    """True when, for every part the reference knows, the candidate has that part and it is
    equal. A candidate's unknown (None) part never matches a part the reference knows."""
    return (
        ref.number == candidate.number
        and (ref.date is None or ref.date == candidate.date)
        and (ref.store is None or ref.store == candidate.store)
    )


def known_count(ref: TxnRef) -> int:
    """How many parts the reference knows: the number always, plus date and store."""
    return 1 + (ref.date is not None) + (ref.store is not None)
