// Document types (data-model.md). Field names and value formats match the backend's
// DocumentIn / DocumentOut (apps/api schemas/documents.py).
// Dates are ISO "YYYY-MM-DD", times "HH:MM" (24h), amounts are integer cents.
// The backend also sends investigation_id, created_at and updated_at; the UI doesn't use them yet.

export type DocumentType = "transaction" | "gift_card" | "online_order" | "misc";
export type PaymentType = "credit_card" | "gift_card" | "cash" | "other";

export const DOCUMENT_TYPES: DocumentType[] = ["transaction", "gift_card", "online_order", "misc"];

export const DOCUMENT_TYPE_LABELS: Record<DocumentType, string> = {
    transaction: "Transaction",
    gift_card: "Gift Card",
    online_order: "Online Order",
    misc: "Misc",
};

export const PAYMENT_TYPES: PaymentType[] = ["credit_card", "gift_card", "cash", "other"];

export const PAYMENT_TYPE_LABELS: Record<PaymentType, string> = {
    credit_card: "Credit Card",
    gift_card: "Gift Card",
    cash: "Cash",
    other: "Other",
};

// One payment row. gift_card_number is set only when type is "gift_card".
// amount_cents is from the transaction's point of view (BD25): negative = returned to this tender.
export interface Payment {
    type: PaymentType;
    gift_card_number: string | null;
    amount_cents: number;
}

interface DocumentBase {
    id: string; // DocumentId: a saved document's integer ID as a string
    status: "complete"; // saved documents are always complete; placeholders are "incomplete"
    title: string; // display title, built by the backend (BD24)
    notes: string | null;
    important: boolean; // BD27; no UI for it yet (Wave 2)
    referenced_by: DocumentRef[];
}

export interface TransactionDoc extends DocumentBase {
    type: "transaction";
    transaction_number: string;
    date: string;
    time: string;
    store_number: string;
    register_number: string | null;
    payments: Payment[];
}

// Activation and history amounts are from the card's point of view (BD25).
export interface GiftCardActivation {
    transaction_number: string;
    date: string;
    time: string;
    store_number: string | null;
    amount_cents: number | null;
}

export interface GiftCardHistoryEntry {
    transaction_number: string;
    date: string;
    time: string;
    store_number: string | null;
    amount_cents: number | null;
}

export interface GiftCardDoc extends DocumentBase {
    type: "gift_card";
    gift_card_number: string;
    activation: GiftCardActivation;
    history: GiftCardHistoryEntry[];
}

export interface OnlineOrderDoc extends DocumentBase {
    type: "online_order";
    order_number: string;
    placed_date: string;
    placed_time: string;
    customer_city: string | null;
    customer_state: string | null;
    pickup_store_number: string | null;
    payments: Payment[];
}

export interface MiscDoc extends DocumentBase {
    type: "misc";
    name: string;
    date: string;
    time: string;
    transaction_number: string | null;
    order_number: string | null;
    payments: Payment[];
}

export type TxnDocument = TransactionDoc | GiftCardDoc | OnlineOrderDoc | MiscDoc;

// Omit applied to each member of a union separately (plain Omit would merge the union).
type DistributiveOmit<T, K extends PropertyKey> = T extends unknown ? Omit<T, K> : never;

// A document as a form produces it: the body of POST / PUT (the backend's DocumentIn).
// `important` is left out, so it defaults to false; the Wave 2 checkbox will send it.
export type NewDocument = DistributiveOmit<TxnDocument, "id" | "title" | "status" | "important" | "referenced_by">;

// ---- Incomplete nodes (placeholders) ----
// Something other documents reference but that has no document yet (B4). The backend works
// these out from the saved documents on every read (relationship_service.py) and returns
// them in the same list, with status "incomplete". Only the fields the references tell us are
// known; the rest are null (relationship-resolution 3.7).

// A prefilled payment row. The amount is null when the history entry it came from had none.
export interface PrefillPayment {
    type: PaymentType;
    gift_card_number: string | null;
    amount_cents: number | null;
}

interface PlaceholderBase {
    id: string; // "ph-<type>-<hash>", never contains a card number (B13)
    status: "incomplete";
    title: string;
    referenced_by: DocumentRef[];
}

export interface TransactionPlaceholder extends PlaceholderBase {
    type: "transaction";
    transaction_number: string;
    date: string | null;
    time: string | null;
    store_number: string | null;
    payments: PrefillPayment[];
}

export interface GiftCardPlaceholder extends PlaceholderBase {
    type: "gift_card";
    gift_card_number: string;
    history: GiftCardHistoryEntry[];
}

export interface OnlineOrderPlaceholder extends PlaceholderBase {
    type: "online_order";
    order_number: string;
}

export type Placeholder = TransactionPlaceholder | GiftCardPlaceholder | OnlineOrderPlaceholder;

// Everything the Documents list shows: saved documents and incomplete nodes.
export type ListedDocument = TxnDocument | Placeholder;

// One document that references another (data-model DocumentRef). "ambiguous" means the
// reference also matched other documents (BD3).
export interface DocumentRef {
    id: string;
    type: DocumentType;
    title: string;
    match: "exact" | "ambiguous";
}
