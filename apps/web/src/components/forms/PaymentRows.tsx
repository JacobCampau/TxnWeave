import {
    addError,
    centsToText,
    checkDigits,
    checkMoney,
    formatMoney,
    parseMoney,
    type Errors,
} from "../../documents/fieldRules";
import {
    PAYMENT_TYPES,
    PAYMENT_TYPE_LABELS,
    type Payment,
    type PaymentType,
    type PrefillPayment,
} from "../../types/document";
import TextField from "./TextField";

// A payment row as typed. `key` identifies the row for React and for its input ids,
// so removing a row doesn't shift another row's errors onto it.
export interface PaymentDraft {
    key: number;
    type: PaymentType;
    gift_card_number: string;
    amount: string;
}

let nextRowKey = 1;

// Unique keys for repeatable rows (payments and gift card history).
export function newRowKey(): number {
    return nextRowKey++;
}

export function emptyPayment(): PaymentDraft {
    return { key: newRowKey(), type: "credit_card", gift_card_number: "", amount: "" };
}

// A saved (or prefilled) payment back as a row of typed text, for editing.
// A prefilled row's amount can be null, which shows as an empty amount.
export function paymentToDraft(payment: Payment | PrefillPayment): PaymentDraft {
    return {
        key: newRowKey(),
        type: payment.type,
        gift_card_number: payment.gift_card_number ?? "",
        amount: centsToText(payment.amount_cents),
    };
}

const ADD_BUTTON_ID = "payments-add";

interface PaymentRowsProps {
    rows: PaymentDraft[];
    onChange: (rows: PaymentDraft[]) => void;
    errors: Errors;
    required: boolean; // at least one row needed (Transaction, Online Order)
}

// Repeatable payment rows (D16, UI-16): type, card number (Gift Card only), amount,
// Remove, "Add payment", and a running total.
export default function PaymentRows({ rows, onChange, errors, required }: PaymentRowsProps) {
    function updateRow(key: number, changes: Partial<PaymentDraft>) {
        onChange(rows.map((row) => (row.key === key ? { ...row, ...changes } : row)));
    }

    function changeType(key: number, type: PaymentType) {
        // Leaving Gift Card clears the card number (UI-16).
        updateRow(key, type === "gift_card" ? { type } : { type, gift_card_number: "" });
    }

    // Rows whose amount isn't valid yet count as 0 in the total.
    const total = rows.reduce((sum, row) => sum + (parseMoney(row.amount) ?? 0), 0);
    const noRowsError = errors[ADD_BUTTON_ID];

    return (
        <fieldset className="repeat-section">
            <legend>
                Payments
                {required && <span aria-hidden="true"> *</span>}
            </legend>

            {rows.map((row, index) => {
                const typeId = `payment-${row.key}-type`;
                return (
                    <div key={row.key} className="repeat-row">
                        <div className="form-field">
                            <label htmlFor={typeId}>Payment {index + 1} type</label>
                            <select
                                id={typeId}
                                className="form-field__input"
                                value={row.type}
                                onChange={(event) => changeType(row.key, event.target.value as PaymentType)}
                            >
                                {PAYMENT_TYPES.map((type) => (
                                    <option key={type} value={type}>
                                        {PAYMENT_TYPE_LABELS[type]}
                                    </option>
                                ))}
                            </select>
                        </div>

                        {row.type === "gift_card" && (
                            <TextField
                                id={`payment-${row.key}-card`}
                                label="Gift card number"
                                required
                                numeric
                                maxLength={24}
                                value={row.gift_card_number}
                                onChange={(value) => updateRow(row.key, { gift_card_number: value })}
                                error={errors[`payment-${row.key}-card`]}
                            />
                        )}

                        <TextField
                            id={`payment-${row.key}-amount`}
                            label="Amount"
                            required
                            placeholder="$0.00"
                            hint="Negative = returned to this tender"
                            value={row.amount}
                            onChange={(value) => updateRow(row.key, { amount: value })}
                            error={errors[`payment-${row.key}-amount`]}
                        />

                        <button
                            type="button"
                            className="button button--secondary repeat-row__remove"
                            aria-label={`Remove payment ${index + 1}`}
                            onClick={() => onChange(rows.filter((r) => r.key !== row.key))}
                        >
                            ×
                        </button>
                    </div>
                );
            })}

            <div className="repeat-section__footer">
                <button
                    id={ADD_BUTTON_ID}
                    type="button"
                    className="button button--secondary"
                    aria-describedby={noRowsError ? `${ADD_BUTTON_ID}-error` : undefined}
                    onClick={() => onChange([...rows, emptyPayment()])}
                >
                    Add payment
                </button>
                <span className="repeat-section__total">Total {formatMoney(total)}</span>
            </div>
            {noRowsError && (
                <p id={`${ADD_BUTTON_ID}-error`} className="form-field__error">
                    {noRowsError}
                </p>
            )}
        </fieldset>
    );
}

// Checks every payment row, adding errors in row order, and returns the rows as Payments.
// The returned rows are only meaningful when no errors were added.
export function validatePayments(rows: PaymentDraft[], errors: Errors, required: boolean): Payment[] {
    if (required && rows.length === 0) {
        addError(errors, ADD_BUTTON_ID, "Error: Add at least one payment.");
    }

    return rows.map((row) => {
        const isGiftCard = row.type === "gift_card";
        if (isGiftCard) {
            addError(errors, `payment-${row.key}-card`, checkDigits(row.gift_card_number, 24, true));
        }
        addError(errors, `payment-${row.key}-amount`, checkMoney(row.amount, true, true));

        return {
            type: row.type,
            gift_card_number: isGiftCard ? row.gift_card_number.trim() : null,
            amount_cents: parseMoney(row.amount) ?? 0,
        };
    });
}
