"""Shared value types (data-model.md "Shared value types" and "General rules").

Strings are trimmed before they are checked. On optional fields an empty string becomes None
(stored and returned as null). Amounts are strict integers in cents: floats and strings are
rejected (B7).
"""

from typing import Annotated, Any, Literal

from pydantic import BeforeValidator, Field, StringConstraints


def blank_to_none(value: Any) -> Any:
    if isinstance(value, str) and value.strip() == "":
        return None
    return value


def to_upper(value: Any) -> Any:
    return value.strip().upper() if isinstance(value, str) else value


def _digits(max_length: int) -> Any:
    return StringConstraints(strip_whitespace=True, pattern=rf"^[0-9]{{1,{max_length}}}$")


TxnNumber = Annotated[str, _digits(8)]
OrderNumber = Annotated[str, _digits(8)]
GiftCardNumber = Annotated[str, _digits(24)]  # BD5: 1 to 24 digits
StoreNumber = Annotated[str, _digits(3)]
RegisterNumber = Annotated[str, _digits(3)]
Time24 = Annotated[str, StringConstraints(strip_whitespace=True, pattern=r"^([01][0-9]|2[0-3]):[0-5][0-9]$")]
ShortText = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=200)]
StateCode = Annotated[str, BeforeValidator(to_upper), StringConstraints(pattern=r"^[A-Z]{2}$")]

AmountCents = Annotated[int, Field(ge=-9_999_999, le=9_999_999, strict=True)]  # signed, BD25
ActivationAmountCents = Annotated[int, Field(ge=0, le=9_999_999, strict=True)]  # never negative

# Optional versions: "" (or only spaces) becomes None.
OptionalTxnNumber = Annotated[TxnNumber | None, BeforeValidator(blank_to_none)]
OptionalOrderNumber = Annotated[OrderNumber | None, BeforeValidator(blank_to_none)]
OptionalGiftCardNumber = Annotated[GiftCardNumber | None, BeforeValidator(blank_to_none)]
OptionalStoreNumber = Annotated[StoreNumber | None, BeforeValidator(blank_to_none)]
OptionalRegisterNumber = Annotated[RegisterNumber | None, BeforeValidator(blank_to_none)]
OptionalShortText = Annotated[ShortText | None, BeforeValidator(blank_to_none)]
OptionalStateCode = Annotated[StateCode | None, BeforeValidator(blank_to_none)]
Notes = Annotated[
    Annotated[str, StringConstraints(strip_whitespace=True, max_length=10_000)] | None,
    BeforeValidator(blank_to_none),
]

PaymentType = Literal["credit_card", "gift_card", "cash", "other"]
DocumentType = Literal["transaction", "gift_card", "online_order", "misc"]
DocumentStatus = Literal["complete", "incomplete"]  # "incomplete" only for placeholders
MatchQuality = Literal["exact", "ambiguous"]
