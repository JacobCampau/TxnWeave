"""ORM classes, one per table (persistence.md "Tables", B10).

A shared `documents` table, one detail table per document type keyed by `document_id`, and
the child tables `payments` and `gift_card_history_entries`. Dates are ISO text
("YYYY-MM-DD"), times "HH:MM", timestamps ISO 8601 UTC text, amounts integer cents.
Blank optional values are NULL. Placeholders (incomplete nodes) are never stored (B4).
"""

from sqlalchemy import CheckConstraint, ForeignKey, Index, Text, text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

AMOUNT_RANGE = "BETWEEN -9999999 AND 9999999"


class Base(DeclarativeBase):
    pass


class Investigation(Base):
    __tablename__ = "investigations"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[str] = mapped_column(Text)
    updated_at: Mapped[str] = mapped_column(Text)
    last_exported_at: Mapped[str | None] = mapped_column(Text)

    documents: Mapped[list["Document"]] = relationship(
        back_populates="investigation", cascade="all, delete-orphan", passive_deletes=True
    )


class Document(Base):
    __tablename__ = "documents"
    __table_args__ = (
        CheckConstraint("type IN ('transaction','gift_card','online_order','misc')", name="ck_documents_type"),
        CheckConstraint("important IN (0,1)", name="ck_documents_important"),
        Index("ix_documents_investigation_type", "investigation_id", "type"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    investigation_id: Mapped[int] = mapped_column(ForeignKey("investigations.id", ondelete="CASCADE"))
    type: Mapped[str] = mapped_column(Text)
    notes: Mapped[str | None] = mapped_column(Text)
    # Added now so the table never changes later; set through the UI in Wave 2 (BD27).
    important: Mapped[bool] = mapped_column(default=False, server_default=text("0"))
    created_at: Mapped[str] = mapped_column(Text)
    updated_at: Mapped[str] = mapped_column(Text)

    investigation: Mapped[Investigation] = relationship(back_populates="documents")

    # Exactly one of these four is set, matching `type`.
    transaction: Mapped["TransactionDetails | None"] = relationship(cascade="all, delete-orphan", passive_deletes=True)
    gift_card: Mapped["GiftCardDetails | None"] = relationship(cascade="all, delete-orphan", passive_deletes=True)
    online_order: Mapped["OnlineOrderDetails | None"] = relationship(cascade="all, delete-orphan", passive_deletes=True)
    misc: Mapped["MiscDetails | None"] = relationship(cascade="all, delete-orphan", passive_deletes=True)

    # Child rows keep the order the user entered them in.
    payments: Mapped[list["Payment"]] = relationship(
        order_by="Payment.position", cascade="all, delete-orphan", passive_deletes=True
    )
    history_entries: Mapped[list["GiftCardHistoryEntry"]] = relationship(
        order_by="GiftCardHistoryEntry.position", cascade="all, delete-orphan", passive_deletes=True
    )


class TransactionDetails(Base):
    __tablename__ = "transactions"
    __table_args__ = (Index("ix_transactions_number_date", "transaction_number", "date"),)

    document_id: Mapped[int] = mapped_column(ForeignKey("documents.id", ondelete="CASCADE"), primary_key=True)
    transaction_number: Mapped[str] = mapped_column(Text)
    date: Mapped[str] = mapped_column(Text)
    time: Mapped[str] = mapped_column(Text)
    store_number: Mapped[str] = mapped_column(Text)  # required on Transactions (BD26)
    register_number: Mapped[str | None] = mapped_column(Text)


class GiftCardDetails(Base):
    __tablename__ = "gift_cards"
    __table_args__ = (
        CheckConstraint("activation_amount_cents BETWEEN 0 AND 9999999", name="ck_gift_cards_activation_amount"),
        Index("ix_gift_cards_number", "gift_card_number"),
        Index("ix_gift_cards_activation_txn", "activation_transaction_number"),
    )

    document_id: Mapped[int] = mapped_column(ForeignKey("documents.id", ondelete="CASCADE"), primary_key=True)
    gift_card_number: Mapped[str] = mapped_column(Text)
    activation_transaction_number: Mapped[str] = mapped_column(Text)
    activation_date: Mapped[str] = mapped_column(Text)
    activation_time: Mapped[str] = mapped_column(Text)
    activation_store_number: Mapped[str | None] = mapped_column(Text)
    activation_amount_cents: Mapped[int | None]


class GiftCardHistoryEntry(Base):
    __tablename__ = "gift_card_history_entries"
    __table_args__ = (
        CheckConstraint(f"amount_cents {AMOUNT_RANGE}", name="ck_history_amount"),
        Index("ix_history_transaction_number", "transaction_number"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    gift_card_document_id: Mapped[int] = mapped_column(ForeignKey("documents.id", ondelete="CASCADE"))
    position: Mapped[int]
    transaction_number: Mapped[str] = mapped_column(Text)
    date: Mapped[str] = mapped_column(Text)
    time: Mapped[str] = mapped_column(Text)
    store_number: Mapped[str | None] = mapped_column(Text)
    amount_cents: Mapped[int | None]  # card view (BD25)


class OnlineOrderDetails(Base):
    __tablename__ = "online_orders"
    __table_args__ = (Index("ix_online_orders_number", "order_number"),)

    document_id: Mapped[int] = mapped_column(ForeignKey("documents.id", ondelete="CASCADE"), primary_key=True)
    order_number: Mapped[str] = mapped_column(Text)
    placed_date: Mapped[str] = mapped_column(Text)
    placed_time: Mapped[str] = mapped_column(Text)
    customer_city: Mapped[str | None] = mapped_column(Text)
    customer_state: Mapped[str | None] = mapped_column(Text)
    pickup_store_number: Mapped[str | None] = mapped_column(Text)


class MiscDetails(Base):
    __tablename__ = "misc_nodes"
    __table_args__ = (
        Index("ix_misc_transaction_number", "transaction_number"),
        Index("ix_misc_order_number", "order_number"),
    )

    document_id: Mapped[int] = mapped_column(ForeignKey("documents.id", ondelete="CASCADE"), primary_key=True)
    name: Mapped[str] = mapped_column(Text)
    date: Mapped[str] = mapped_column(Text)
    time: Mapped[str] = mapped_column(Text)
    transaction_number: Mapped[str | None] = mapped_column(Text)
    order_number: Mapped[str | None] = mapped_column(Text)


class Payment(Base):
    __tablename__ = "payments"
    __table_args__ = (
        CheckConstraint("type IN ('credit_card','gift_card','cash','other')", name="ck_payments_type"),
        CheckConstraint(f"amount_cents {AMOUNT_RANGE}", name="ck_payments_amount"),
        # A card number exactly when the type is Gift Card.
        CheckConstraint("(type = 'gift_card') = (gift_card_number IS NOT NULL)", name="ck_payments_card_number"),
        Index("ix_payments_gift_card_number", "gift_card_number"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    document_id: Mapped[int] = mapped_column(ForeignKey("documents.id", ondelete="CASCADE"))
    position: Mapped[int]
    type: Mapped[str] = mapped_column(Text)
    gift_card_number: Mapped[str | None] = mapped_column(Text)
    amount_cents: Mapped[int]  # transaction view (BD25)


NODE_COLORS = "('ink','slate','mist','rose','crimson')"
NODE_SHAPES = "('ellipse','rectangle','round-rectangle','triangle','diamond','hexagon','octagon','star')"


class InvestigationSettings(Base):
    """One row per investigation, only after the first settings save. No row means the
    defaults, and Reset deletes the row (BD30). Colors are palette token names (BD29)."""

    __tablename__ = "investigation_settings"
    __table_args__ = (
        *(
            CheckConstraint(f"{doc_type}_color IN {NODE_COLORS}", name=f"ck_settings_{doc_type}_color")
            for doc_type in ("transaction", "gift_card", "online_order", "misc")
        ),
        *(
            CheckConstraint(f"{doc_type}_shape IN {NODE_SHAPES}", name=f"ck_settings_{doc_type}_shape")
            for doc_type in ("transaction", "gift_card", "online_order", "misc")
        ),
        CheckConstraint("important_edge_color IN ('ink','slate','crimson')", name="ck_settings_edge_color"),
    )

    investigation_id: Mapped[int] = mapped_column(
        ForeignKey("investigations.id", ondelete="CASCADE"), primary_key=True
    )
    transaction_color: Mapped[str] = mapped_column(Text)
    transaction_shape: Mapped[str] = mapped_column(Text)
    gift_card_color: Mapped[str] = mapped_column(Text)
    gift_card_shape: Mapped[str] = mapped_column(Text)
    online_order_color: Mapped[str] = mapped_column(Text)
    online_order_shape: Mapped[str] = mapped_column(Text)
    misc_color: Mapped[str] = mapped_column(Text)
    misc_shape: Mapped[str] = mapped_column(Text)
    important_edge_color: Mapped[str] = mapped_column(Text)
    updated_at: Mapped[str] = mapped_column(Text)
