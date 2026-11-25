import { useEffect } from "react";
import { formatMoney, toDisplayDate } from "../documents/fieldRules";
import {
    DOCUMENT_TYPE_LABELS,
    PAYMENT_TYPE_LABELS,
    type ListedDocument,
    type PrefillPayment,
} from "../types/document";

export interface ConnectedNode {
    id: string;
    title: string;
}

interface PropertyPanelProps {
    doc: ListedDocument;
    connected: ConnectedNode[];
    onSelect: (id: string) => void; // a connected node was clicked
    onEdit: (id: string) => void; // "Edit in Documents"
    onClose: () => void;
}

const UNKNOWN = "Unknown";

function date(value: string | null | undefined): string {
    return value ? toDisplayDate(value) : UNKNOWN;
}

function text(value: string | null | undefined): string {
    return value || UNKNOWN;
}

function money(cents: number | null | undefined): string {
    return cents === null || cents === undefined ? UNKNOWN : formatMoney(cents);
}

// [label, value] rows for every field of the document (UI-6). The full card number is shown
// here on purpose: this panel and the form are the only places it appears (B13, D10).
function fieldRows(doc: ListedDocument): [string, string][] {
    switch (doc.type) {
        case "transaction":
            return [
                ["Transaction number", doc.transaction_number],
                ["Date", date(doc.date)],
                ["Time", text(doc.time)],
                ["Store", text(doc.store_number)],
                ["Register", doc.status === "complete" ? doc.register_number ?? "—" : UNKNOWN],
            ];
        case "gift_card":
            if (doc.status === "incomplete") return [["Gift card number", doc.gift_card_number]];
            return [
                ["Gift card number", doc.gift_card_number],
                ["Activation transaction", doc.activation.transaction_number],
                ["Activation date", date(doc.activation.date)],
                ["Activation time", doc.activation.time],
                ["Activation store", doc.activation.store_number ?? "—"],
                ["Activation amount", doc.activation.amount_cents === null ? "—" : formatMoney(doc.activation.amount_cents)],
            ];
        case "online_order":
            if (doc.status === "incomplete") return [["Order number", doc.order_number]];
            return [
                ["Order number", doc.order_number],
                ["Placed", `${date(doc.placed_date)} ${doc.placed_time}`],
                ["Customer city", doc.customer_city ?? "—"],
                ["Customer state", doc.customer_state ?? "—"],
                ["Pickup store", doc.pickup_store_number ?? "—"],
            ];
        case "misc":
            return [
                ["Name", doc.name],
                ["Date", date(doc.date)],
                ["Time", doc.time],
                ["Transaction number", doc.transaction_number ?? "—"],
                ["Order number", doc.order_number ?? "—"],
            ];
    }
}

function paymentText(payment: PrefillPayment): string {
    const card = payment.gift_card_number ? ` ${payment.gift_card_number}` : "";
    return `${PAYMENT_TYPE_LABELS[payment.type]}${card}: ${money(payment.amount_cents)}`;
}

// Read-only details of the clicked node (UI-6, D7), in a slate drawer on the right.
export default function PropertyPanel({ doc, connected, onSelect, onEdit, onClose }: PropertyPanelProps) {
    // Esc closes the panel (UI-6, UI-19).
    useEffect(() => {
        function onKey(event: KeyboardEvent) {
            if (event.key === "Escape") onClose();
        }
        window.addEventListener("keydown", onKey);
        return () => window.removeEventListener("keydown", onKey);
    }, [onClose]);

    const payments: PrefillPayment[] = "payments" in doc ? doc.payments : [];
    const history = doc.type === "gift_card" ? doc.history : [];
    const notes = doc.status === "complete" ? doc.notes : null;

    return (
        <aside className="property-panel" aria-label="Node details">
            <div className="property-panel__header">
                <h2>{doc.title}</h2>
                <button type="button" className="button button--secondary-on-dark" aria-label="Close details" onClick={onClose}>
                    ×
                </button>
            </div>
            <p>
                {DOCUMENT_TYPE_LABELS[doc.type]}
                {doc.status === "incomplete" && <span className="badge badge--incomplete">Incomplete</span>}
            </p>

            <dl className="property-panel__fields">
                {fieldRows(doc).map(([label, value]) => (
                    <div key={label}>
                        <dt>{label}</dt>
                        <dd>{value}</dd>
                    </div>
                ))}
            </dl>

            {payments.length > 0 && (
                <>
                    <h3>Payments</h3>
                    <ul>
                        {payments.map((payment, index) => (
                            <li key={index}>{paymentText(payment)}</li>
                        ))}
                    </ul>
                </>
            )}

            {history.length > 0 && (
                <>
                    <h3>History</h3>
                    <ul>
                        {history.map((entry, index) => (
                            <li key={index}>
                                {date(entry.date)} {entry.time} · Transaction {entry.transaction_number}
                                {entry.store_number && ` · Store ${entry.store_number}`}: {money(entry.amount_cents)}
                            </li>
                        ))}
                    </ul>
                </>
            )}

            <h3>Notes</h3>
            <p className="property-panel__notes">{notes || "None"}</p>

            <h3>Connected nodes</h3>
            {connected.length === 0 ? (
                <p>None</p>
            ) : (
                <ul className="property-panel__connected">
                    {connected.map((node) => (
                        <li key={node.id}>
                            <button type="button" className="property-panel__link" onClick={() => onSelect(node.id)}>
                                {node.title}
                            </button>
                        </li>
                    ))}
                </ul>
            )}

            <button type="button" className="button button--primary" onClick={() => onEdit(doc.id)}>
                Edit in Documents
            </button>
        </aside>
    );
}
