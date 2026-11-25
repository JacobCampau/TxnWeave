"""The amount sign convention (BD25, relationship-resolution 3.14).

Payment rows are in "transaction view": positive = paid with this tender, negative = returned
to this tender. Gift Card activation and history amounts are in "card view": positive = value
put onto the card, negative = value spent from the card. Whenever the two are related, the
sign flips: card amount = -(payment amount).

These two functions are the ONLY place an amount is negated. Never compare a card-view amount
with a transaction-view amount directly; convert one first.

The CSV money cells (csv-save-load 5.5, 5.6) live here too. They never change a sign.
"""

import re
from decimal import Decimal

MAX_CENTS = 9_999_999  # $99,999.99 either way (B7)


def card_view(payment_amount_cents: int) -> int:
    """A payment amount as the card sees it: a $25.00 return to the card (-2500) is +2500."""
    return 0 - payment_amount_cents  # "0 -" keeps 0 as 0


def transaction_view(card_amount_cents: int) -> int:
    """A card amount as the transaction sees it: $40.00 spent from the card (-4000) is +4000."""
    return 0 - card_amount_cents


# ---- CSV money cells (BD11, 5.5, 5.6) ----


class MoneyCellError(ValueError):
    """A money cell that can't be read. `code` is the ImportReport problem code."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


# An optional sign and an optional "$" in either order, then digits (plain, or grouped in
# threes with commas), then at most one "." with the decimals.
_MONEY_CELL = re.compile(r"^([-+]?)\$?([-+]?)(\d{1,3}(?:,\d{3})+|\d+)(?:\.(\d*))?$")


def parse_money_cell(text: str) -> int:
    """`-25.50`, `-$25.50`, `$-25.50`, `25.5`, `25`, `1,250.00` and Excel's `(25.50)` become
    integer cents. Parsed with Decimal, never float."""
    cell = text.strip()
    negative = False
    if cell.startswith("(") and cell.endswith(")"):  # accounting format for a negative
        cell = cell[1:-1].strip()
        negative = True

    match = _MONEY_CELL.match(cell)
    if match is None:
        raise MoneyCellError("invalid_format", "Must be an amount like 25.50 or -25.50")
    sign_before, sign_after, whole, decimals = match.groups()
    signs = sign_before + sign_after
    if len(signs) > 1 or (negative and signs):
        raise MoneyCellError("invalid_format", "Must be an amount like 25.50 or -25.50")
    if decimals is not None and len(decimals) > 2:
        raise MoneyCellError("invalid_format", "At most 2 decimal places")

    value = Decimal(f"{whole.replace(',', '')}.{decimals or '0'}")
    cents = int(value * 100)
    if negative or signs == "-":
        cents = 0 - cents
    if abs(cents) > MAX_CENTS:
        raise MoneyCellError("out_of_range", "Must be between -99,999.99 and 99,999.99")
    return cents


def format_money_cell(cents: int) -> str:
    """Plain signed decimal with exactly 2 decimals: -2550 is "-25.50", 0 is "0.00"."""
    sign = "-" if cents < 0 else ""
    whole, part = divmod(abs(cents), 100)
    return f"{sign}{whole}.{part:02d}"
