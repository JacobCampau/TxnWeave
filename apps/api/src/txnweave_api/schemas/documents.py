"""Document schemas (data-model.md "Pydantic schema split").

`*In` models are strict request bodies for POST and PUT. `*Out` models have the same fields,
all optional (a placeholder knows only some of them), plus id, status, title and
referenced_by. `DocumentIn` / `DocumentOut` are unions picked by the `type` field (B9).
"""

import datetime as dt  # imported as a module: some fields are themselves named `date`
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from txnweave_api.schemas.common import (
    ActivationAmountCents,
    AmountCents,
    DocumentStatus,
    DocumentType,
    GiftCardNumber,
    MatchQuality,
    Notes,
    OptionalGiftCardNumber,
    OptionalOrderNumber,
    OptionalRegisterNumber,
    OptionalShortText,
    OptionalStateCode,
    OptionalStoreNumber,
    OptionalTxnNumber,
    OrderNumber,
    PaymentType,
    ShortText,
    StoreNumber,
    Time24,
    TxnNumber,
)


class StrictIn(BaseModel):
    model_config = ConfigDict(extra="forbid")  # unknown fields are a 422


# ---- Request bodies ----


class PaymentIn(StrictIn):
    type: PaymentType
    gift_card_number: OptionalGiftCardNumber = None
    amount_cents: AmountCents  # transaction view (BD25)

    @model_validator(mode="after")
    def card_number_only_for_gift_cards(self) -> "PaymentIn":
        # The messages never include the number itself (B13).
        if self.type == "gift_card" and self.gift_card_number is None:
            raise ValueError("A gift card payment needs a gift card number")
        if self.type != "gift_card" and self.gift_card_number is not None:
            raise ValueError("Only gift card payments can have a gift card number")
        return self


class GiftCardActivationIn(StrictIn):
    transaction_number: TxnNumber
    date: dt.date
    time: Time24
    store_number: OptionalStoreNumber = None
    amount_cents: ActivationAmountCents | None = None  # card view, never negative


class GiftCardHistoryEntryIn(StrictIn):
    transaction_number: TxnNumber
    date: dt.date
    time: Time24
    store_number: OptionalStoreNumber = None
    amount_cents: AmountCents | None = None  # card view (BD25)


class TransactionIn(StrictIn):
    type: Literal["transaction"]
    transaction_number: TxnNumber
    date: dt.date
    time: Time24
    store_number: StoreNumber  # required (BD26)
    register_number: OptionalRegisterNumber = None
    payments: list[PaymentIn] = Field(min_length=1)
    notes: Notes = None
    important: bool = False


class GiftCardIn(StrictIn):
    type: Literal["gift_card"]
    gift_card_number: GiftCardNumber
    activation: GiftCardActivationIn
    history: list[GiftCardHistoryEntryIn] = []
    notes: Notes = None
    important: bool = False


class OnlineOrderIn(StrictIn):
    type: Literal["online_order"]
    order_number: OrderNumber
    placed_date: dt.date
    placed_time: Time24
    customer_city: OptionalShortText = None
    customer_state: OptionalStateCode = None
    pickup_store_number: OptionalStoreNumber = None
    payments: list[PaymentIn] = Field(min_length=1)
    notes: Notes = None
    important: bool = False


class MiscIn(StrictIn):
    type: Literal["misc"]
    name: ShortText  # not unique (BD16)
    date: dt.date
    time: Time24
    transaction_number: OptionalTxnNumber = None
    order_number: OptionalOrderNumber = None
    payments: list[PaymentIn] = []
    notes: Notes = None
    important: bool = False


DocumentIn = Annotated[TransactionIn | GiftCardIn | OnlineOrderIn | MiscIn, Field(discriminator="type")]


# ---- Responses ----


class DocumentRef(BaseModel):
    """A document that references another one. "ambiguous": the reference also matched others."""

    id: str
    type: DocumentType
    title: str
    match: MatchQuality


class PaymentOut(BaseModel):
    type: PaymentType
    gift_card_number: str | None = None
    amount_cents: int | None = None  # null only on a placeholder's prefilled row


class GiftCardActivationOut(BaseModel):
    transaction_number: str | None = None
    date: dt.date | None = None
    time: str | None = None
    store_number: str | None = None
    amount_cents: int | None = None


class GiftCardHistoryEntryOut(BaseModel):
    transaction_number: str
    date: dt.date
    time: str
    store_number: str | None = None
    amount_cents: int | None = None


class DocumentOutBase(BaseModel):
    id: str  # a saved document's integer ID as text, or "ph-<type>-<hash>" for a placeholder
    investigation_id: int
    status: DocumentStatus
    title: str
    important: bool = False  # always false on placeholders (BD27)
    notes: str | None = None
    referenced_by: list[DocumentRef] = []
    created_at: dt.datetime | None = None  # null for placeholders
    updated_at: dt.datetime | None = None


class TransactionOut(DocumentOutBase):
    type: Literal["transaction"]
    transaction_number: str | None = None
    date: dt.date | None = None
    time: str | None = None
    store_number: str | None = None
    register_number: str | None = None
    payments: list[PaymentOut] = []


class GiftCardOut(DocumentOutBase):
    type: Literal["gift_card"]
    gift_card_number: str | None = None
    activation: GiftCardActivationOut | None = None
    history: list[GiftCardHistoryEntryOut] = []


class OnlineOrderOut(DocumentOutBase):
    type: Literal["online_order"]
    order_number: str | None = None
    placed_date: dt.date | None = None
    placed_time: str | None = None
    customer_city: str | None = None
    customer_state: str | None = None
    pickup_store_number: str | None = None
    payments: list[PaymentOut] = []


class MiscOut(DocumentOutBase):
    type: Literal["misc"]
    name: str | None = None
    date: dt.date | None = None
    time: str | None = None
    transaction_number: str | None = None
    order_number: str | None = None
    payments: list[PaymentOut] = []


DocumentOut = Annotated[TransactionOut | GiftCardOut | OnlineOrderOut | MiscOut, Field(discriminator="type")]
# The same union without the discriminator wrapper, for type hints in the services.
AnyDocumentOut = TransactionOut | GiftCardOut | OnlineOrderOut | MiscOut
