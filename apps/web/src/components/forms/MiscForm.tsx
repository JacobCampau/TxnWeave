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
import type { MiscDoc } from "../../types/document";
import FormShell from "./FormShell";
import PaymentRows, { paymentToDraft, validatePayments, type PaymentDraft } from "./PaymentRows";
import TextField from "./TextField";
import { useDocumentForm, type DocumentFormProps, type ValidationResult } from "./useDocumentForm";

interface MiscDraft {
    name: string;
    date: string; // MM-DD-YYYY as typed
    time: string;
    transaction_number: string;
    order_number: string;
    payments: PaymentDraft[];
    notes: string;
}

function emptyDraft(): MiscDraft {
    return {
        name: "",
        date: "",
        time: "",
        transaction_number: "",
        order_number: "",
        payments: [], // payments are optional on Misc
        notes: "",
    };
}

// A saved Misc document back as typed text, for editing.
function toDraft(doc: MiscDoc): MiscDraft {
    return {
        name: doc.name,
        date: toDisplayDate(doc.date),
        time: fromTime24(doc.time),
        transaction_number: doc.transaction_number ?? "",
        order_number: doc.order_number ?? "",
        payments: doc.payments.map(paymentToDraft),
        notes: doc.notes ?? "",
    };
}

function validate(draft: MiscDraft): ValidationResult {
    const errors: Errors = {};
    addError(errors, "misc-name", checkText(draft.name, true));
    addError(errors, "misc-date", checkDate(draft.date, true));
    addError(errors, "misc-time", checkTime(draft.time, true));
    addError(errors, "misc-txn-number", checkDigits(draft.transaction_number, 8, false));
    addError(errors, "misc-order-number", checkDigits(draft.order_number, 8, false));
    const payments = validatePayments(draft.payments, errors, false);
    addError(errors, "notes", checkText(draft.notes, false, 10_000));

    if (Object.keys(errors).length > 0) {
        return { errors, doc: null };
    }
    return {
        errors,
        doc: {
            type: "misc",
            name: draft.name.trim(),
            date: toIsoDate(draft.date),
            time: toTime24(draft.time),
            transaction_number: optional(draft.transaction_number),
            order_number: optional(draft.order_number),
            payments,
            notes: optional(draft.notes),
        },
    };
}

export default function MiscForm({
    initial,
    onSave,
    onCancel,
    onDelete,
    onDirtyChange,
}: DocumentFormProps<MiscDoc>) {
    // Misc documents are never referenced, so there are no incomplete Misc nodes to prefill.
    const { draft, setField, errors, shell } = useDocumentForm({
        initialDraft: () => (initial ? toDraft(initial) : emptyDraft()),
        validate,
        onSave,
        onDirtyChange,
        isPlaceholder: false,
    });

    return (
        <FormShell {...shell} onCancel={onCancel} onDelete={onDelete}>
            <TextField
                id="misc-name"
                label="Node name"
                required
                maxLength={200}
                autoFocus
                value={draft.name}
                onChange={(value) => setField("name", value)}
                error={errors["misc-name"]}
            />
            <TextField
                id="misc-date"
                label="Date"
                required
                placeholder="MM-DD-YYYY"
                maxLength={10}
                value={draft.date}
                onChange={(value) => setField("date", value)}
                error={errors["misc-date"]}
            />
            <TextField
                id="misc-time"
                label="Time"
                required
                placeholder="HHMM"
                numeric
                maxLength={4}
                value={draft.time}
                onChange={(value) => setField("time", value)}
                error={errors["misc-time"]}
            />
            <TextField
                id="misc-txn-number"
                label="Transaction number"
                numeric
                maxLength={8}
                value={draft.transaction_number}
                onChange={(value) => setField("transaction_number", value)}
                error={errors["misc-txn-number"]}
            />
            <TextField
                id="misc-order-number"
                label="Online order number"
                numeric
                maxLength={8}
                value={draft.order_number}
                onChange={(value) => setField("order_number", value)}
                error={errors["misc-order-number"]}
            />
            <PaymentRows
                rows={draft.payments}
                onChange={(rows) => setField("payments", rows)}
                errors={errors}
                required={false}
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
