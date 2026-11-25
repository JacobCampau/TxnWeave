import {
    addError,
    checkDate,
    checkDigits,
    checkState,
    checkText,
    checkTime,
    fromTime24,
    optional,
    toDisplayDate,
    toIsoDate,
    toTime24,
    type Errors,
} from "../../documents/fieldRules";
import type { OnlineOrderDoc, OnlineOrderPlaceholder } from "../../types/document";
import FormShell from "./FormShell";
import PaymentRows, { emptyPayment, paymentToDraft, validatePayments, type PaymentDraft } from "./PaymentRows";
import TextField from "./TextField";
import { useDocumentForm, type DocumentFormProps, type ValidationResult } from "./useDocumentForm";

interface OnlineOrderDraft {
    order_number: string;
    placed_date: string; // MM-DD-YYYY as typed
    placed_time: string;
    customer_city: string;
    customer_state: string;
    pickup_store_number: string;
    payments: PaymentDraft[];
    notes: string;
}

function emptyDraft(): OnlineOrderDraft {
    return {
        order_number: "",
        placed_date: "",
        placed_time: "",
        customer_city: "",
        customer_state: "",
        pickup_store_number: "",
        payments: [emptyPayment()], // at least one payment is required
        notes: "",
    };
}

// A saved Online Order back as typed text, for editing.
function toDraft(doc: OnlineOrderDoc): OnlineOrderDraft {
    return {
        order_number: doc.order_number,
        placed_date: toDisplayDate(doc.placed_date),
        placed_time: fromTime24(doc.placed_time),
        customer_city: doc.customer_city ?? "",
        customer_state: doc.customer_state ?? "",
        pickup_store_number: doc.pickup_store_number ?? "",
        payments: doc.payments.map(paymentToDraft),
        notes: doc.notes ?? "",
    };
}

// An incomplete Online Order: only its number is known (relationship-resolution 3.7).
function prefillToDraft(placeholder: OnlineOrderPlaceholder): OnlineOrderDraft {
    return { ...emptyDraft(), order_number: placeholder.order_number };
}

function validate(draft: OnlineOrderDraft): ValidationResult {
    const errors: Errors = {};
    addError(errors, "order-number", checkDigits(draft.order_number, 8, true));
    addError(errors, "order-date", checkDate(draft.placed_date, true));
    addError(errors, "order-time", checkTime(draft.placed_time, true));
    addError(errors, "order-city", checkText(draft.customer_city, false));
    addError(errors, "order-state", checkState(draft.customer_state));
    addError(errors, "order-pickup-store", checkDigits(draft.pickup_store_number, 3, false));
    const payments = validatePayments(draft.payments, errors, true);
    addError(errors, "notes", checkText(draft.notes, false, 10_000));

    if (Object.keys(errors).length > 0) {
        return { errors, doc: null };
    }
    return {
        errors,
        doc: {
            type: "online_order",
            order_number: draft.order_number.trim(),
            placed_date: toIsoDate(draft.placed_date),
            placed_time: toTime24(draft.placed_time),
            customer_city: optional(draft.customer_city),
            customer_state: optional(draft.customer_state),
            pickup_store_number: optional(draft.pickup_store_number),
            payments,
            notes: optional(draft.notes),
        },
    };
}

export default function OnlineOrderForm({
    initial,
    prefill,
    onSave,
    onCancel,
    onDelete,
    onDirtyChange,
}: DocumentFormProps<OnlineOrderDoc, OnlineOrderPlaceholder>) {
    const { draft, setField, errors, shell } = useDocumentForm({
        initialDraft: () => (initial ? toDraft(initial) : prefill ? prefillToDraft(prefill) : emptyDraft()),
        validate,
        onSave,
        onDirtyChange,
        isPlaceholder: prefill !== undefined,
    });

    return (
        <FormShell {...shell} onCancel={onCancel} onDelete={onDelete}>
            <TextField
                id="order-number"
                label="Online order number"
                required
                numeric
                maxLength={8}
                autoFocus
                value={draft.order_number}
                onChange={(value) => setField("order_number", value)}
                error={errors["order-number"]}
            />
            <TextField
                id="order-date"
                label="Placed date"
                required
                placeholder="MM-DD-YYYY"
                maxLength={10}
                value={draft.placed_date}
                onChange={(value) => setField("placed_date", value)}
                error={errors["order-date"]}
            />
            <TextField
                id="order-time"
                label="Placed time"
                required
                placeholder="HHMM"
                numeric
                maxLength={4}
                value={draft.placed_time}
                onChange={(value) => setField("placed_time", value)}
                error={errors["order-time"]}
            />
            <TextField
                id="order-city"
                label="Customer city"
                maxLength={200}
                value={draft.customer_city}
                onChange={(value) => setField("customer_city", value)}
                error={errors["order-city"]}
            />
            <TextField
                id="order-state"
                label="Customer state"
                maxLength={2}
                value={draft.customer_state}
                onChange={(value) => setField("customer_state", value.toUpperCase())}
                error={errors["order-state"]}
            />
            <TextField
                id="order-pickup-store"
                label="Store number for pickup"
                numeric
                maxLength={3}
                value={draft.pickup_store_number}
                onChange={(value) => setField("pickup_store_number", value)}
                error={errors["order-pickup-store"]}
            />
            <PaymentRows
                rows={draft.payments}
                onChange={(rows) => setField("payments", rows)}
                errors={errors}
                required
            />
            <TextField
                id="notes"
                label="Notes"
                multiline
                value={draft.notes}
                onChange={(value) => setField("notes", value)}
                error={errors["notes"]}
            />
        </FormShell>
    );
}
