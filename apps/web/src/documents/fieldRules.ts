// Field checks and conversions for the document forms (documents-page.md, data-model.md).
// Each check returns an error message starting with "Error:" (color-system), or null if valid.
// Values are trimmed before they are checked, and an empty optional field is valid.

export type FieldError = string | null;

// Errors for one form, keyed by the input's element id, in the order the fields appear.
export type Errors = Record<string, string>;

const REQUIRED = "Error: This field is required.";
const MAX_CENTS = 9_999_999; // $99,999.99

export function addError(errors: Errors, id: string, error: FieldError) {
    if (error) {
        errors[id] = error;
    }
}

// Digits-only ID and number fields, at most maxLength digits (D18, D25).
export function checkDigits(value: string, maxLength: number, required: boolean): FieldError {
    const v = value.trim();
    if (v === "") return required ? REQUIRED : null;
    if (!/^[0-9]+$/.test(v)) return "Error: Use digits only.";
    if (v.length > maxLength) return `Error: Use at most ${maxLength} digits.`;
    return null;
}

export function checkText(value: string, required: boolean, maxLength = 200): FieldError {
    const v = value.trim();
    if (v === "") return required ? REQUIRED : null;
    if (v.length > maxLength) return `Error: Use at most ${maxLength} characters.`;
    return null;
}

// MM-DD-YYYY, and it must be a real calendar date (D17, D18).
export function checkDate(value: string, required: boolean): FieldError {
    const v = value.trim();
    if (v === "") return required ? REQUIRED : null;
    const match = /^(\d{2})-(\d{2})-(\d{4})$/.exec(v);
    if (!match) return "Error: Use the format MM-DD-YYYY.";

    const month = Number(match[1]);
    const day = Number(match[2]);
    const year = Number(match[3]);
    // Date.UTC rolls an impossible date over (02-30 becomes 03-02), so compare the parts back.
    const date = new Date(Date.UTC(year, month - 1, day));
    const isReal =
        date.getUTCFullYear() === year &&
        date.getUTCMonth() === month - 1 &&
        date.getUTCDate() === day;
    return isReal ? null : "Error: This is not a real date.";
}

// Military time typed as HHMM with no colon, 0000 to 2359.
export function checkTime(value: string, required: boolean): FieldError {
    const v = value.trim();
    if (v === "") return required ? REQUIRED : null;
    return /^([01][0-9]|2[0-3])[0-5][0-9]$/.test(v) ? null : "Error: Use military time HHMM, for example 1805.";
}

// "1805" -> "18:05", the format the backend stores (data-model Time24). Call only after
// checkTime passed.
export function toTime24(value: string): string {
    const v = value.trim();
    return `${v.slice(0, 2)}:${v.slice(2)}`;
}

// Two-letter state code. The form uppercases it as the user types.
export function checkState(value: string): FieldError {
    const v = value.trim();
    if (v === "") return null;
    return /^[A-Za-z]{2}$/.test(v) ? null : "Error: Use a 2-letter state code.";
}

// "25", "25.5", "$1,234.56" and "-25.00" are all accepted.
const MONEY_PATTERN = /^(-)?\$?(\d{1,3}(?:,\d{3})+|\d+)(?:\.(\d{1,2}))?$/;

// Converts typed money text to integer cents, or null if it isn't a money value.
export function parseMoney(value: string): number | null {
    const match = MONEY_PATTERN.exec(value.trim());
    if (!match) return null;
    const [, minus, whole, fraction = ""] = match;
    const cents = Number(whole.replaceAll(",", "")) * 100 + Number(fraction.padEnd(2, "0"));
    return minus ? -cents : cents;
}

export function checkMoney(value: string, required: boolean, allowNegative: boolean): FieldError {
    const v = value.trim();
    if (v === "") return required ? REQUIRED : null;
    const cents = parseMoney(v);
    if (cents === null) {
        return allowNegative
            ? "Error: Enter an amount like 25.00 or -25.00."
            : "Error: Enter an amount like 25.00.";
    }
    if (!allowNegative && cents < 0) return "Error: The amount can't be negative.";
    if (Math.abs(cents) > MAX_CENTS) return "Error: The amount must be at most $99,999.99.";
    return null;
}

// Shows cents as "$1,234.50" or "-$25.00".
export function formatMoney(cents: number): string {
    const text = (Math.abs(cents) / 100).toLocaleString("en-US", {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2,
    });
    return cents < 0 ? `-$${text}` : `$${text}`;
}

// Trimmed text, or null when empty (data-model "General rules").
export function optional(value: string): string | null {
    const v = value.trim();
    return v === "" ? null : v;
}

// Optional money: null when empty, otherwise cents. Call only after checkMoney passed.
export function optionalCents(value: string): number | null {
    return value.trim() === "" ? null : parseMoney(value);
}

// The reverse conversions below fill a form from a saved document.

// "18:05" -> "1805"
export function fromTime24(time: string): string {
    return time.replace(":", "");
}

// -2500 -> "-25.00", and null -> "". No "$" or commas, so parseMoney reads it back.
export function centsToText(cents: number | null): string {
    if (cents === null) return "";
    const sign = cents < 0 ? "-" : "";
    return sign + (Math.abs(cents) / 100).toFixed(2);
}

// "03-14-2026" -> "2026-03-14". Call only after checkDate passed.
export function toIsoDate(display: string): string {
    const [month, day, year] = display.trim().split("-");
    return `${year}-${month}-${day}`;
}

// "2026-03-14" -> "03-14-2026"
export function toDisplayDate(iso: string): string {
    const [year, month, day] = iso.split("-");
    return `${month}-${day}-${year}`;
}
