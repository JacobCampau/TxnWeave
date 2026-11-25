import pytest

from txnweave_api.services.money import (
    MoneyCellError,
    card_view,
    format_money_cell,
    parse_money_cell,
    transaction_view,
)


def test_card_view_flips_the_sign():
    assert card_view(-2500) == 2500
    assert card_view(4000) == -4000
    assert card_view(0) == 0


def test_transaction_view_flips_back():
    assert transaction_view(-4000) == 4000
    assert transaction_view(card_view(1234)) == 1234


# ---- CSV money cells (csv-save-load 5.6 acceptance criteria) ----

@pytest.mark.parametrize(
    "text, cents",
    [
        ("-25.50", -2550), ("-$25.50", -2550), ("$-25.50", -2550), ("(25.50)", -2550),
        ("1,250.00", 125000), ("25.5", 2550), ("25", 2500), ("$0.10", 10), ("99999.99", 9_999_999),
        (" 12.00 ", 1200), ("+3", 300),
    ],
)
def test_parse_money_cell(text, cents):
    assert parse_money_cell(text) == cents


@pytest.mark.parametrize(
    "text, code",
    [
        ("25.505", "invalid_format"), ("1e3", "invalid_format"), ("abc", "invalid_format"), ("", "invalid_format"),
        ("--5", "invalid_format"), ("(-5)", "invalid_format"), ("1,25.00", "invalid_format"),
        ("100000.00", "out_of_range"), ("-100000", "out_of_range"),
    ],
)
def test_parse_money_cell_rejects(text, code):
    with pytest.raises(MoneyCellError) as error:
        parse_money_cell(text)
    assert error.value.code == code


def test_format_money_cell():
    assert format_money_cell(-1250) == "-12.50"
    assert format_money_cell(0) == "0.00"
    assert format_money_cell(125000) == "1250.00"
    assert format_money_cell(5) == "0.05"


def test_round_trip_never_changes_a_sign():
    for cents in (-9_999_999, -1, 0, 1, 2550, 9_999_999):
        assert parse_money_cell(format_money_cell(cents)) == cents
