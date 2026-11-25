"""Relationship resolution (relationship-resolution.md, section 3).

A pure function (B11) over every saved document of one investigation. It finds every
reference (rules R1-R6), matches each against the saved documents, turns the references that
match nothing into placeholders (incomplete nodes) with prefilled fields, and works out which
documents reference each document (`referenced_by`). Nothing here touches the database, and
nothing is stored: this runs on every read (B4).
"""

import hashlib
from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import Literal

from txnweave_api.schemas.documents import (
    AnyDocumentOut,
    DocumentRef,
    GiftCardHistoryEntryOut,
    GiftCardOut,
    OnlineOrderOut,
    PaymentOut,
    TransactionOut,
)
from txnweave_api.services.keys import TxnRef, known_count, matches, txn_ref_of
from txnweave_api.services.money import card_view, transaction_view
from txnweave_api.services.titles import gift_card_title, online_order_title, transaction_title

Match = Literal["exact", "ambiguous"]
Kind = Literal["activated", "used_in", "related"]  # table 3.2, BD6
Ref = Literal["gift_card_activation", "gift_card_history", "payment", "misc_reference"]


@dataclass(frozen=True)
class Link:
    """`source_id` references `target_id`. The graph step (build-plan step 7) turns these into
    edges, using `kind` for the edge direction in table 3.2."""

    source_id: str
    target_id: str
    kind: Kind
    ref: Ref
    match: Match


@dataclass
class Resolution:
    placeholders: list[AnyDocumentOut]
    links: list[Link]
    referenced_by: dict[str, list[DocumentRef]]  # keyed by document or placeholder id


@dataclass
class _TransactionReference:
    """A reference to a Transaction (R1 activation, R2a history entry, R5 Misc).
    `time` and `payment` are what it can prefill on a Transaction placeholder (3.7)."""

    key: TxnRef
    source: AnyDocumentOut
    row: int  # position of the row it came from, for a stable prefill order
    kind: Kind
    ref: Ref
    time: str | None = None
    payment: PaymentOut | None = None


@dataclass
class _NumberReference:
    """A reference by number to a Gift Card (R2b, R3, R4) or an Online Order (R6).
    `history` is what it can prefill on a Gift Card placeholder (3.7)."""

    number: str
    source: AnyDocumentOut
    row: int
    kind: Kind
    ref: Ref
    history: GiftCardHistoryEntryOut | None = None


@dataclass
class _TransactionPlaceholderBuild:
    key: TxnRef
    attached: list[tuple[_TransactionReference, Match]] = field(default_factory=list)


def _id_order(doc: AnyDocumentOut) -> int:
    return int(doc.id)  # saved ids are integers as text


def _source_then_row(ref: _TransactionReference | _NumberReference) -> tuple[int, int]:
    return (_id_order(ref.source), ref.row)


# ---- 3.2: find every reference ----


def _collect_references(
    docs: Sequence[AnyDocumentOut],
) -> tuple[list[_TransactionReference], list[_NumberReference], list[_NumberReference]]:
    transaction_refs: list[_TransactionReference] = []
    card_refs: list[_NumberReference] = []
    order_refs: list[_NumberReference] = []

    def add_payment_card_refs(doc: AnyDocumentOut, payments: list[PaymentOut]) -> None:
        # R2b, R3, R4: a gift card payment row references that card. Only a Transaction's
        # payment can prefill card history (BD17: history entries reference transactions only).
        for row, payment in enumerate(payments):
            if payment.type != "gift_card" or not payment.gift_card_number:
                continue
            history = None
            if isinstance(doc, TransactionOut) and payment.amount_cents is not None:
                history = GiftCardHistoryEntryOut(
                    transaction_number=doc.transaction_number,
                    date=doc.date,
                    time=doc.time,
                    store_number=doc.store_number,
                    amount_cents=card_view(payment.amount_cents),  # BD25 flip
                )
            card_refs.append(_NumberReference(payment.gift_card_number, doc, row, "used_in", "payment", history))

    for doc in docs:
        if isinstance(doc, TransactionOut):
            add_payment_card_refs(doc, doc.payments)

        elif isinstance(doc, GiftCardOut):
            activation = doc.activation
            if activation is not None and activation.transaction_number:
                # R1: the activation transaction. It prefills the time only: that's where the
                # card was bought, not a tender, so no payment row (3.7).
                transaction_refs.append(
                    _TransactionReference(
                        key=TxnRef(activation.transaction_number, activation.date, activation.store_number),
                        source=doc,
                        row=-1,  # before the history rows
                        kind="activated",
                        ref="gift_card_activation",
                        time=activation.time,
                    )
                )
            for row, entry in enumerate(doc.history):
                # R2a: each history entry prefills a gift card payment row, sign flipped.
                transaction_refs.append(
                    _TransactionReference(
                        key=TxnRef(entry.transaction_number, entry.date, entry.store_number),
                        source=doc,
                        row=row,
                        kind="used_in",
                        ref="gift_card_history",
                        time=entry.time,
                        payment=PaymentOut(
                            type="gift_card",
                            gift_card_number=doc.gift_card_number,
                            amount_cents=None if entry.amount_cents is None else transaction_view(entry.amount_cents),
                        ),
                    )
                )

        elif isinstance(doc, OnlineOrderOut):
            add_payment_card_refs(doc, doc.payments)

        else:  # Misc
            add_payment_card_refs(doc, doc.payments)
            if doc.transaction_number:
                # R5: a number-only transaction reference.
                transaction_refs.append(
                    _TransactionReference(
                        key=TxnRef(doc.transaction_number, None, None),
                        source=doc,
                        row=0,
                        kind="related",
                        ref="misc_reference",
                    )
                )
            if doc.order_number:
                # R6
                order_refs.append(_NumberReference(doc.order_number, doc, 0, "related", "misc_reference"))

    return transaction_refs, card_refs, order_refs


# ---- 3.6: placeholder IDs ----


def _placeholder_id(doc_type: str, text: str) -> str:
    """Stable while the placeholder's key stays the same, and never contains a card number."""
    return f"ph-{doc_type}-{hashlib.sha256(text.encode()).hexdigest()[:12]}"


# ---- 3.5 and 3.7: Transaction placeholders ----


def _placeholder_order(ref: _TransactionReference) -> tuple:
    """Most specific references first, so a number-only Misc reference joins an existing
    (number, date, store) placeholder instead of creating a second one (3.5)."""
    key = ref.key
    return (
        -known_count(key),
        key.number,
        key.date.isoformat() if key.date else "",
        key.store or "",
        *_source_then_row(ref),
    )


def _build_transaction_placeholders(unmatched: list[_TransactionReference]) -> list[_TransactionPlaceholderBuild]:
    builds: list[_TransactionPlaceholderBuild] = []
    for ref in sorted(unmatched, key=_placeholder_order):
        found = [build for build in builds if matches(ref.key, build.key)]
        if not found:
            # The new placeholder knows exactly what this reference knows.
            builds.append(_TransactionPlaceholderBuild(key=ref.key, attached=[(ref, "exact")]))
        else:
            match: Match = "exact" if len(found) == 1 else "ambiguous"
            for build in found:
                build.attached.append((ref, match))
    return builds


def _to_transaction_placeholder(investigation_id: int, build: _TransactionPlaceholderBuild) -> TransactionOut:
    key = build.key
    refs = sorted((ref for ref, _ in build.attached), key=_source_then_row)

    # A single-value field is prefilled only when every reference that gives it agrees (BD14).
    times = {ref.time for ref in refs if ref.time is not None}
    time = next(iter(times)) if len(times) == 1 else None

    date_text = key.date.isoformat() if key.date else "?"
    return TransactionOut(
        id=_placeholder_id(
            "transaction", f"{investigation_id}:transaction:{key.number}|{date_text}|{key.store or '?'}|?"
        ),
        investigation_id=investigation_id,
        status="incomplete",
        type="transaction",
        title=transaction_title(key.number, key.date, key.store, None),
        transaction_number=key.number,
        date=key.date,
        time=time,
        store_number=key.store,  # None when no reference gave a store (BD26)
        payments=[ref.payment for ref in refs if ref.payment is not None],  # one row per history entry
    )


# ---- The whole resolution ----


def resolve(investigation_id: int, documents: Sequence[AnyDocumentOut]) -> Resolution:
    docs = sorted(documents, key=_id_order)  # the same input always gives the same output (3.12)
    transaction_refs, card_refs, order_refs = _collect_references(docs)
    placeholders: list[AnyDocumentOut] = []
    links: list[Link] = []

    def link(source: AnyDocumentOut, target_id: str, ref: _TransactionReference | _NumberReference, match: Match):
        links.append(Link(source.id, target_id, ref.kind, ref.ref, match))

    # Transactions: match against saved ones (3.3, 3.4); zero matches go to placeholders (3.5).
    saved_transactions = [doc for doc in docs if isinstance(doc, TransactionOut)]
    unmatched: list[_TransactionReference] = []
    for ref in transaction_refs:
        found = [txn for txn in saved_transactions if matches(ref.key, txn_ref_of(txn))]
        if not found:
            unmatched.append(ref)
            continue
        match: Match = "exact" if len(found) == 1 else "ambiguous"
        for txn in found:
            link(ref.source, txn.id, ref, match)

    for build in _build_transaction_placeholders(unmatched):
        placeholder = _to_transaction_placeholder(investigation_id, build)
        placeholders.append(placeholder)
        for ref, match in build.attached:
            link(ref.source, placeholder.id, ref, match)

    # Gift cards and online orders: a single-number lookup, never ambiguous (3.2). References
    # to the same missing number share one placeholder.
    saved_cards: dict[str, AnyDocumentOut] = {}
    saved_orders: dict[str, AnyDocumentOut] = {}
    for doc in docs:
        if isinstance(doc, GiftCardOut) and doc.gift_card_number:
            saved_cards.setdefault(doc.gift_card_number, doc)
        if isinstance(doc, OnlineOrderOut) and doc.order_number:
            saved_orders.setdefault(doc.order_number, doc)

    missing_cards: dict[str, list[_NumberReference]] = {}
    for ref in card_refs:
        if ref.number in saved_cards:
            link(ref.source, saved_cards[ref.number].id, ref, "exact")
        else:
            missing_cards.setdefault(ref.number, []).append(ref)
    for number, refs in missing_cards.items():
        card = GiftCardOut(
            id=_placeholder_id("gift_card", f"{investigation_id}:gift_card:{number}"),
            investigation_id=investigation_id,
            status="incomplete",
            type="gift_card",
            title=gift_card_title(number),
            gift_card_number=number,
            # One history row per paying Transaction row, already in card view (3.7).
            # Activation is never prefilled: no reference says how the card was activated.
            history=[ref.history for ref in sorted(refs, key=_source_then_row) if ref.history is not None],
        )
        placeholders.append(card)
        for ref in refs:
            link(ref.source, card.id, ref, "exact")

    missing_orders: dict[str, list[_NumberReference]] = {}
    for ref in order_refs:
        if ref.number in saved_orders:
            link(ref.source, saved_orders[ref.number].id, ref, "exact")
        else:
            missing_orders.setdefault(ref.number, []).append(ref)
    for number, refs in missing_orders.items():
        order = OnlineOrderOut(
            id=_placeholder_id("online_order", f"{investigation_id}:online_order:{number}"),
            investigation_id=investigation_id,
            status="incomplete",
            type="online_order",
            title=online_order_title(number),
            order_number=number,
        )
        placeholders.append(order)
        for ref in refs:
            link(ref.source, order.id, ref, "exact")

    by_id = {doc.id: doc for doc in docs}
    return Resolution(placeholders=placeholders, links=links, referenced_by=_referenced_by(links, by_id))


def _referenced_by(links: list[Link], by_id: dict[str, AnyDocumentOut]) -> dict[str, list[DocumentRef]]:
    """3.11: each target's distinct referencing documents, ordered by id, with `match` set as in
    3.9: "exact" if any reference between the two documents matched uniquely. That includes a
    reference the other way round: if card X's history is ambiguous between A and B but A's own
    payment uses X, then X and A are exactly related, and only B stays ambiguous."""
    exact_pairs = {frozenset((link.source_id, link.target_id)) for link in links if link.match == "exact"}

    sources_by_target: dict[str, dict[str, Match]] = {}
    for link in links:
        exact = frozenset((link.source_id, link.target_id)) in exact_pairs
        sources_by_target.setdefault(link.target_id, {})[link.source_id] = "exact" if exact else "ambiguous"

    result: dict[str, list[DocumentRef]] = {}
    for target_id, sources in sources_by_target.items():
        refs = []
        for source_id in sorted(sources, key=int):
            source = by_id[source_id]
            refs.append(DocumentRef(id=source.id, type=source.type, title=source.title, match=sources[source_id]))
        result[target_id] = refs
    return result
