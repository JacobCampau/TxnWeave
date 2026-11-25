import {
    addError,
    checkDate,
    checkDigits,
    checkMoney,
    checkText,
    checkTime,
    centsToText,
    fromTime24,
    optional,
    optionalCents,
    toDisplayDate,
    toIsoDate,
    toTime24,
    type Errors,
} from "../../documents/fieldRules";
import type { GiftCardDoc, GiftCardHistoryEntry, GiftCardPlaceholder } from "../../types/document";
import FormShell from "./FormShell";
import { newRowKey } from "./PaymentRows";
import TextField from "./TextField";
import { useDocumentForm, type DocumentFormProps, type ValidationResult } from "./useDocumentForm";

// A history row as typed. `key` works like PaymentDraft.key.
interface HistoryDraft {
    key: number;
    transaction_number: string;
    date: string;
    time: string;
    store_number: string;
    amount: string;
}

// The activation fields are kept flat in the draft and nested only when the document is built.
interface GiftCardDraft {
    gift_card_number: string;
    activation_transaction_number: string;
    activation_date: string; // MM-DD-YYYY as typed
    activation_time: string;
    activation_store_number: string;
    activation_amount: string;
    history: HistoryDraft[];
    notes: string;
}

function emptyDraft(): GiftCardDraft {
    return {
        gift_card_number: "",
        activation_transaction_number: "",
        activation_date: "",
        activation_time: "",
        activation_store_number: "",
        activation_amount: "",
        history: [], // 0 or more rows
        notes: "",
    };
}

function emptyHistoryRow(): HistoryDraft {
    return { key: newRowKey(), transaction_number: "", date: "", time: "", store_number: "", amount: "" };
}

// A saved Gift Card back as typed text, for editing.
function toDraft(doc: GiftCardDoc): GiftCardDraft {
    return {
        gift_card_number: doc.gift_card_number,
        activation_transaction_number: doc.activation.transaction_number,
        activation_date: toDisplayDate(doc.activation.date),
        activation_time: fromTime24(doc.activation.time),
        activation_store_number: doc.activation.store_number ?? "",
        activation_amount: centsToText(doc.activation.amount_cents),
        history: doc.history.map(historyToDraft),
        notes: doc.notes ?? "",
    };
}

// An incomplete Gift Card: the number and one history row per Transaction that paid with it,
// already in card view (relationship-resolution 3.7). Activation is never prefilled.
function prefillToDraft(placeholder: GiftCardPlaceholder): GiftCardDraft {
    return {
        ...emptyDraft(),
        gift_card_number: placeholder.gift_card_number,
        history: placeholder.history.map(historyToDraft),
    };
}

function historyToDraft(entry: GiftCardHistoryEntry): HistoryDraft {
    return {
        key: newRowKey(),
        transaction_number: entry.transaction_number,
        date: toDisplayDate(entry.date),
        time: fromTime24(entry.time),
        store_number: entry.store_number ?? "",
        amount: centsToText(entry.amount_cents),
    };
}

function validate(draft: GiftCardDraft): ValidationResult {
    const errors: Errors = {};
    addError(errors, "gc-number", checkDigits(draft.gift_card_number, 24, true));
    addError(errors, "gc-act-txn", checkDigits(draft.activation_transaction_number, 8, true));
    addError(errors, "gc-act-date", checkDate(draft.activation_date, true));
    addError(errors, "gc-act-time", checkTime(draft.activation_time, true));
    addError(errors, "gc-act-store", checkDigits(draft.activation_store_number, 3, false));
    // Activation amounts can't be negative (card view, BD25).
    addError(errors, "gc-act-amount", checkMoney(draft.activation_amount, false, false));

    const history: GiftCardHistoryEntry[] = draft.history.map((row) => {
        const id = `history-${row.key}`;
        addError(errors, `${id}-txn`, checkDigits(row.transaction_number, 8, true));
        addError(errors, `${id}-date`, checkDate(row.date, true));
        addError(errors, `${id}-time`, checkTime(row.time, true));
        addError(errors, `${id}-store`, checkDigits(row.store_number, 3, false));
        addError(errors, `${id}-amount`, checkMoney(row.amount, false, true));
        // Only used when there are no errors, so toIsoDate gets a valid date.
        return {
            transaction_number: row.transaction_number.trim(),
            date: row.date.trim() === "" ? "" : toIsoDate(row.date),
            time: toTime24(row.time),
            store_number: optional(row.store_number),
            amount_cents: optionalCents(row.amount),
        };
    });

    addError(errors, "notes", checkText(draft.notes, false, 10_000));

    if (Object.keys(errors).length > 0) {
        return { errors, doc: null };
    }
    return {
        errors,
        doc: {
            type: "gift_card",
            gift_card_number: draft.gift_card_number.trim(),
            activation: {
                transaction_number: draft.activation_transaction_number.trim(),
                date: toIsoDate(draft.activation_date),
                time: toTime24(draft.activation_time),
                store_number: optional(draft.activation_store_number),
                amount_cents: optionalCents(draft.activation_amount),
            },
            history,
            notes: optional(draft.notes),
        },
    };
}

export default function GiftCardForm({
    initial,
    prefill,
    onSave,
    onCancel,
    onDelete,
    onDirtyChange,
}: DocumentFormProps<GiftCardDoc, GiftCardPlaceholder>) {
    const { draft, setField, errors, shell } = useDocumentForm({
        initialDraft: () => (initial ? toDraft(initial) : prefill ? prefillToDraft(prefill) : emptyDraft()),
        validate,
        onSave,
        onDirtyChange,
        isPlaceholder: prefill !== undefined,
    });

    function updateHistoryRow(key: number, changes: Partial<HistoryDraft>) {
        setField(
            "history",
            draft.history.map((row) => (row.key === key ? { ...row, ...changes } : row)),
        );
    }

    return (
        <FormShell {...shell} onCancel={onCancel} onDelete={onDelete}>
            <TextField
                id="gc-number"
                label="Gift card number"
                required
                numeric
                maxLength={24}
                autoFocus
                value={draft.gift_card_number}
                onChange={(value) => setField("gift_card_number", value)}
                error={errors["gc-number"]}
            />

            <fieldset className="repeat-section">
                <legend>Activation</legend>
                <TextField
                    id="gc-act-txn"
                    label="Transaction number"
                    required
                    numeric
                    maxLength={8}
                    value={draft.activation_transaction_number}
                    onChange={(value) => setField("activation_transaction_number", value)}
                    error={errors["gc-act-txn"]}
                />
                <TextField
                    id="gc-act-date"
                    label="Date"
                    required
                    placeholder="MM-DD-YYYY"
                    maxLength={10}
                    value={draft.activation_date}
                    onChange={(value) => setField("activation_date", value)}
                    error={errors["gc-act-date"]}
                />
                <TextField
                    id="gc-act-time"
                    label="Time"
                    required
                    placeholder="HHMM"
                    numeric
                    maxLength={4}
                    value={draft.activation_time}
                    onChange={(value) => setField("activation_time", value)}
                    error={errors["gc-act-time"]}
                />
                <TextField
                    id="gc-act-store"
                    label="Store number"
                    numeric
                    maxLength={3}
                    value={draft.activation_store_number}
                    onChange={(value) => setField("activation_store_number", value)}
                    error={errors["gc-act-store"]}
                />
                <TextField
                    id="gc-act-amount"
                    label="Amount"
                    placeholder="$0.00"
                    value={draft.activation_amount}
                    onChange={(value) => setField("activation_amount", value)}
                    error={errors["gc-act-amount"]}
                />
            </fieldset>

            <fieldset className="repeat-section">
                <legend>History</legend>
                {draft.history.map((row, index) => {
                    const id = `history-${row.key}`;
                    return (
                        <div key={row.key} className="repeat-row">
                            <TextField
                                id={`${id}-txn`}
                                label={`Entry ${index + 1} transaction number`}
                                required
                                numeric
                                maxLength={8}
                                value={row.transaction_number}
                                onChange={(value) => updateHistoryRow(row.key, { transaction_number: value })}
                                error={errors[`${id}-txn`]}
                            />
                            <TextField
                                id={`${id}-date`}
                                label="Date"
                                required
                                placeholder="MM-DD-YYYY"
                                maxLength={10}
                                value={row.date}
                                onChange={(value) => updateHistoryRow(row.key, { date: value })}
                                error={errors[`${id}-date`]}
                            />
                            <TextField
                                id={`${id}-time`}
                                label="Time"
                                required
                                placeholder="HHMM"
                                numeric
                                maxLength={4}
                                value={row.time}
                                onChange={(value) => updateHistoryRow(row.key, { time: value })}
                                error={errors[`${id}-time`]}
                            />
                            <TextField
                                id={`${id}-store`}
                                label="Store number"
                                numeric
                                maxLength={3}
                                value={row.store_number}
                                onChange={(value) => updateHistoryRow(row.key, { store_number: value })}
                                error={errors[`${id}-store`]}
                            />
                            <TextField
                                id={`${id}-amount`}
                                label="Amount"
                                placeholder="$0.00"
                                hint="+ added to card, − spent from card"
                                value={row.amount}
                                onChange={(value) => updateHistoryRow(row.key, { amount: value })}
                                error={errors[`${id}-amount`]}
                            />
                            <button
                                type="button"
                                className="button button--secondary repeat-row__remove"
                                aria-label={`Remove history entry ${index + 1}`}
                                onClick={() =>
                                    setField(
                                        "history",
                                        draft.history.filter((r) => r.key !== row.key),
                                    )
                                }
                            >
                                ×
                            </button>
                        </div>
                    );
                })}
                <div className="repeat-section__footer">
                    <button
                        type="button"
                        className="button button--secondary"
                        onClick={() => setField("history", [...draft.history, emptyHistoryRow()])}
                    >
                        Add history entry
                    </button>
                </div>
            </fieldset>

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
