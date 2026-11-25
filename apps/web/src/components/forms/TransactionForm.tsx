import {
    addError,
    checkDate,
    checkDigits,
    checkText,
    checkTime,
    fromTime24,
    optional,
    toDisplayDate,
    toIsoDate,
    toTime24,
    type Errors,
} from "../../documents/fieldRules";
import type { TransactionDoc, TransactionPlaceholder } from "../../types/document";
import FormShell from "./FormShell";
import PaymentRows, { emptyPayment, paymentToDraft, validatePayments, type PaymentDraft } from "./PaymentRows";
import TextField from "./TextField";
import { useDocumentForm, type DocumentFormProps, type ValidationResult } from "./useDocumentForm";

interface TransactionDraft {
    transaction_number: string;
    date: string; // MM-DD-YYYY as typed
    time: string;
    register_number: string;
    store_number: string;
    payments: PaymentDraft[];
    notes: string;
}

function emptyDraft(): TransactionDraft {
    return {
        transaction_number: "",
        date: "",
        time: "",
        register_number: "",
        store_number: "",
        payments: [emptyPayment()], // at least one payment is required
        notes: "",
    };
}

// A saved Transaction back as typed text, for editing.
function toDraft(doc: TransactionDoc): TransactionDraft {
    return {
        transaction_number: doc.transaction_number,
        date: toDisplayDate(doc.date),
        time: fromTime24(doc.time),
        register_number: doc.register_number ?? "",
        store_number: doc.store_number,
        payments: doc.payments.map(paymentToDraft),
        notes: doc.notes ?? "",
    };
}

// An incomplete Transaction as typed text: the known parts and the prefilled payment rows
// (relationship-resolution 3.7). Unknown parts stay empty so they show as missing.
function prefillToDraft(placeholder: TransactionPlaceholder): TransactionDraft {
    return {
        transaction_number: placeholder.transaction_number,
        date: placeholder.date ? toDisplayDate(placeholder.date) : "",
        time: placeholder.time ? fromTime24(placeholder.time) : "",
        register_number: "",
        store_number: placeholder.store_number ?? "",
        payments:
            placeholder.payments.length > 0 ? placeholder.payments.map(paymentToDraft) : [emptyPayment()],
        notes: "",
    };
}

// Errors are added in the order the fields appear, so focus goes to the first one.
function validate(draft: TransactionDraft): ValidationResult {
    const errors: Errors = {};
    addError(errors, "txn-number", checkDigits(draft.transaction_number, 8, true));
    addError(errors, "txn-date", checkDate(draft.date, true));
    addError(errors, "txn-time", checkTime(draft.time, true));
    addError(errors, "txn-register", checkDigits(draft.register_number, 3, false));
    addError(errors, "txn-store", checkDigits(draft.store_number, 3, true));
    const payments = validatePayments(draft.payments, errors, true);
    addError(errors, "notes", checkText(draft.notes, false, 10_000));

    if (Object.keys(errors).length > 0) {
        return { errors, doc: null };
    }
    return {
        errors,
        doc: {
            type: "transaction",
            transaction_number: draft.transaction_number.trim(),
            date: toIsoDate(draft.date),
            time: toTime24(draft.time),
            register_number: optional(draft.register_number),
            store_number: draft.store_number.trim(),
            payments,
            notes: optional(draft.notes),
        },
    };
}

export default function TransactionForm({
    initial,
    prefill,
    onSave,
    onCancel,
    onDelete,
    onDirtyChange,
}: DocumentFormProps<TransactionDoc, TransactionPlaceholder>) {
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
                id="txn-number"
                label="Transaction number"
                required
                numeric
                maxLength={8}
                autoFocus
                value={draft.transaction_number}
                onChange={(value) => setField("transaction_number", value)}
                error={errors["txn-number"]}
            />
            <TextField
                id="txn-date"
                label="Date"
                required
                placeholder="MM-DD-YYYY"
                maxLength={10}
                value={draft.date}
                onChange={(value) => setField("date", value)}
                error={errors["txn-date"]}
            />
            <TextField
                id="txn-time"
                label="Time"
                required
                placeholder="HHMM"
                numeric
                maxLength={4}
                value={draft.time}
                onChange={(value) => setField("time", value)}
                error={errors["txn-time"]}
            />
            <TextField
                id="txn-register"
                label="Register number"
                numeric
                maxLength={3}
                value={draft.register_number}
                onChange={(value) => setField("register_number", value)}
                error={errors["txn-register"]}
            />
            <TextField
                id="txn-store"
                label="Store number"
                required
                numeric
                maxLength={3}
                value={draft.store_number}
                onChange={(value) => setField("store_number", value)}
                error={errors["txn-store"]}
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
