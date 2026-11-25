"""Relationship resolution, checked against relationship-resolution.md (3.3 table and the
acceptance criteria). Pure: no database."""

from datetime import date

import pytest

from txnweave_api.schemas.documents import (
    GiftCardActivationOut,
    GiftCardHistoryEntryOut,
    GiftCardOut,
    MiscOut,
    OnlineOrderOut,
    PaymentOut,
    TransactionOut,
)
from txnweave_api.services.relationship_service import resolve
from txnweave_api.services.titles import gift_card_title, transaction_title

IID = 1
CARD = "6006491234567890123"


class Docs:
    """Builds saved documents with increasing IDs."""

    def __init__(self):
        self.next_id = 1

    def _id(self) -> str:
        doc_id = str(self.next_id)
        self.next_id += 1
        return doc_id

    def txn(self, number, on, store, register=None, payments=None):
        return TransactionOut(
            id=self._id(), investigation_id=IID, status="complete", type="transaction",
            title=transaction_title(number, on, store, register),
            transaction_number=number, date=on, time="10:00", store_number=store, register_number=register,
            payments=payments or [PaymentOut(type="cash", amount_cents=100)],
        )

    def card(self, number, act_number, act_date, act_store=None, history=()):
        return GiftCardOut(
            id=self._id(), investigation_id=IID, status="complete", type="gift_card",
            title=gift_card_title(number), gift_card_number=number,
            activation=GiftCardActivationOut(
                transaction_number=act_number, date=act_date, time="08:00", store_number=act_store
            ),
            history=list(history),
        )

    def misc(self, txn_number=None, order_number=None, payments=()):
        name = f"Misc {self.next_id}"
        return MiscOut(
            id=self._id(), investigation_id=IID, status="complete", type="misc", title=name, name=name,
            date=date(2026, 1, 1), time="09:00", transaction_number=txn_number, order_number=order_number,
            payments=list(payments),
        )

    def order(self, number, payments):
        return OnlineOrderOut(
            id=self._id(), investigation_id=IID, status="complete", type="online_order",
            title=f"Online Order {number}", order_number=number,
            placed_date=date(2026, 1, 1), placed_time="10:00", payments=payments,
        )


def history(number, on, store=None, amount=None):
    return GiftCardHistoryEntryOut(transaction_number=number, date=on, time="12:00", store_number=store, amount_cents=amount)


def card_payment(amount, number=CARD):
    return PaymentOut(type="gift_card", gift_card_number=number, amount_cents=amount)


def refs(resolution, target_id):
    return {(ref.id, ref.match) for ref in resolution.referenced_by.get(target_id, [])}


MAR14 = date(2026, 3, 14)
APR02 = date(2026, 4, 2)
MAY01 = date(2026, 5, 1)


# ---- 3.3 matching table ----


@pytest.fixture
def table():
    d = Docs()
    saved = {
        "A": d.txn("00482913", MAR14, "042", "003"),
        "B": d.txn("00482913", MAR14, "042", "007"),
        "C": d.txn("00482913", MAR14, "051"),
        "D": d.txn("00482913", APR02, "042"),
    }
    return d, saved


def test_activation_with_number_date_store_links_exactly(table):
    d, s = table
    card = d.card("111", "00482913", APR02, "042")
    r = resolve(IID, [*s.values(), card])
    assert refs(r, s["D"].id) == {(card.id, "exact")}


def test_history_with_store_051_links_exactly_to_c(table):
    d, s = table
    card = d.card("222", "9", MAR14, history=[history("00482913", MAR14, "051")])
    r = resolve(IID, [*s.values(), card])
    assert (card.id, "exact") in refs(r, s["C"].id)


def test_store_042_is_ambiguous_between_a_and_b(table):
    d, s = table
    card = d.card("333", "00482913", MAR14, "042")
    r = resolve(IID, [*s.values(), card])
    assert refs(r, s["A"].id) == refs(r, s["B"].id) == {(card.id, "ambiguous")}
    assert refs(r, s["C"].id) == set()


def test_no_store_is_ambiguous_between_a_b_and_c(table):
    d, s = table
    card = d.card("444", "00482913", MAR14)
    r = resolve(IID, [*s.values(), card])
    for key in "ABC":
        assert refs(r, s[key].id) == {(card.id, "ambiguous")}


def test_misc_number_only_is_ambiguous_with_all_four(table):
    d, s = table
    misc = d.misc("00482913")
    r = resolve(IID, [*s.values(), misc])
    for key in "ABCD":
        assert refs(r, s[key].id) == {(misc.id, "ambiguous")}


def test_unmatched_references_make_placeholders(table):
    d, s = table
    card = d.card("555", "00482913", MAY01, "042")
    misc = d.misc("11112222")
    r = resolve(IID, [*s.values(), card, misc])
    titles = sorted(p.title for p in r.placeholders)
    assert titles == ["Transaction 00482913 · 05-01-2026 · Store 042", "Transaction 11112222"]


# ---- Placeholders, promotion ----


def test_activation_and_misc_share_one_placeholder():
    d = Docs()
    card = d.card(CARD, "11112222", MAY01, "042")
    misc = d.misc("11112222")
    r = resolve(IID, [card, misc])
    assert len(r.placeholders) == 1
    ph = r.placeholders[0]
    assert (ph.transaction_number, ph.date, ph.store_number, ph.time) == ("11112222", MAY01, "042", "08:00")
    assert refs(r, ph.id) == {(card.id, "exact"), (misc.id, "exact")}


def test_placeholder_ids_are_stable_and_hide_card_numbers():
    d = Docs()
    txn = d.txn("1", MAR14, "001", payments=[card_payment(-2500)])
    first = resolve(IID, [txn]).placeholders[0]
    second = resolve(IID, [txn]).placeholders[0]
    assert first.id == second.id
    assert first.id.startswith("ph-gift_card-") and CARD not in first.id
    assert first.title == "Gift Card …0123"


def test_saving_the_real_transaction_promotes_the_placeholder():
    d = Docs()
    card = d.card(CARD, "11112222", MAY01, "042")
    misc = d.misc("11112222")
    real = d.txn("11112222", MAY01, "042", "003")
    r = resolve(IID, [card, misc, real])
    assert r.placeholders == []
    assert refs(r, real.id) == {(card.id, "exact"), (misc.id, "exact")}


def test_a_different_date_does_not_promote():
    d = Docs()
    card = d.card(CARD, "11112222", MAY01, "042")
    misc = d.misc("11112222")
    other_day = d.txn("11112222", date(2026, 5, 2), "042")
    r = resolve(IID, [card, misc, other_day])
    assert len(r.placeholders) == 1  # the activation still points at 05-01


def test_history_without_store_gives_a_placeholder_with_no_store():
    d = Docs()
    card = d.card("999", "1", MAR14, "001", history=[history("777", MAY01, None, -4000)])
    r = resolve(IID, [card])
    ph = next(p for p in r.placeholders if p.transaction_number == "777")
    assert ph.store_number is None
    assert ph.title == "Transaction 777 · 05-01-2026"
    # Any store promotes it.
    r2 = resolve(IID, [card, d.txn("777", MAY01, "123")])
    assert not any(p.transaction_number == "777" for p in r2.placeholders)


# ---- Sign convention (BD25) ----


def test_transaction_payments_prefill_card_history_with_the_sign_flipped():
    d = Docs()
    txn = d.txn("00482913", MAR14, "042", payments=[card_payment(-2500), card_payment(4000)])
    r = resolve(IID, [txn])
    card = r.placeholders[0]
    assert [h.amount_cents for h in card.history] == [2500, -4000]
    first = card.history[0]
    assert (first.transaction_number, first.date, first.time, first.store_number) == ("00482913", MAR14, "10:00", "042")


def test_card_history_prefills_a_transaction_payment_with_the_sign_flipped():
    d = Docs()
    card = d.card(CARD, "1", MAR14, "001", history=[history("11112222", MAY01, "042", -4000)])
    ph = next(p for p in resolve(IID, [card]).placeholders if p.transaction_number == "11112222")
    assert [(p.type, p.gift_card_number, p.amount_cents) for p in ph.payments] == [("gift_card", CARD, 4000)]


def test_a_blank_history_amount_gives_a_blank_payment_amount():
    d = Docs()
    card = d.card("998", "1", MAR14, "001", history=[history("778", MAY01, "042", None)])
    ph = next(p for p in resolve(IID, [card]).placeholders if p.transaction_number == "778")
    assert ph.payments[0].amount_cents is None


def test_order_and_misc_card_payments_reference_but_add_no_history():
    d = Docs()
    txn = d.txn("1", MAR14, "001", payments=[card_payment(-2500)])
    order = d.order("5", [card_payment(100)])
    r = resolve(IID, [txn, order])
    card = r.placeholders[0]
    assert len(card.history) == 1
    assert refs(r, card.id) == {(txn.id, "exact"), (order.id, "exact")}


def test_misc_order_reference_makes_an_online_order_placeholder():
    d = Docs()
    r = resolve(IID, [d.misc(order_number="88")])
    assert [p.title for p in r.placeholders] == ["Online Order 88"]


# ---- Deleting ----


def test_deleting_brings_placeholders_back_or_removes_them():
    d = Docs()
    txn = d.txn("1", MAR14, "001")
    card = d.card("123", "1", MAR14)
    assert resolve(IID, [txn, card]).placeholders == []
    assert len(resolve(IID, [card]).placeholders) == 1  # the matched transaction was deleted
    assert resolve(IID, [txn]).placeholders == []  # the only referencer was deleted


def test_exact_beats_ambiguous_for_the_same_source():
    """3.9: a card's history is ambiguous between A and B, but A also paid with the card."""
    d = Docs()
    a = d.txn("5", MAR14, "042", "001", payments=[card_payment(100, "321")])
    b = d.txn("5", MAR14, "042", "002")
    card = d.card("321", "9", MAR14, history=[history("5", MAR14, "042")])
    r = resolve(IID, [a, b, card])
    assert refs(r, a.id) == {(card.id, "exact")}
    assert refs(r, b.id) == {(card.id, "ambiguous")}
    assert refs(r, card.id) == {(a.id, "exact")}
