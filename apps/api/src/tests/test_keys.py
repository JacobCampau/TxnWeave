from datetime import date

from txnweave_api.services.keys import TxnRef, known_count, matches, transaction_key
from txnweave_api.schemas.documents import TransactionOut

D = date(2026, 3, 14)


def test_transaction_key_blank_register_is_empty_string():
    doc = TransactionOut(
        id="1", investigation_id=1, status="complete", title="t", type="transaction",
        transaction_number="00482913", date=D, time="18:05", store_number="042", register_number=None,
    )
    assert transaction_key(doc) == ("00482913", "2026-03-14", "042", "")


def test_unknown_parts_of_a_reference_are_wildcards():
    candidate = TxnRef("00482913", D, "042")
    assert matches(TxnRef("00482913", None, None), candidate)
    assert matches(TxnRef("00482913", D, None), candidate)
    assert matches(TxnRef("00482913", D, "042"), candidate)


def test_known_parts_must_be_equal():
    candidate = TxnRef("00482913", D, "042")
    assert not matches(TxnRef("00482914", D, "042"), candidate)
    assert not matches(TxnRef("00482913", date(2026, 3, 15), "042"), candidate)
    assert not matches(TxnRef("00482913", D, "051"), candidate)


def test_a_candidates_unknown_part_never_matches_a_known_one():
    placeholder = TxnRef("00482913", D, None)
    assert not matches(TxnRef("00482913", D, "042"), placeholder)
    assert matches(TxnRef("00482913", None, None), placeholder)


def test_known_count():
    assert known_count(TxnRef("1", None, None)) == 1
    assert known_count(TxnRef("1", D, "042")) == 3
