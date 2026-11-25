// One labelled text input (or textarea) with its hint and error message.
// Required fields show "*" (documents-page.md). An input in error gets the error style
// and is linked to its message with aria-describedby (color-system: "Input in error").
interface TextFieldProps {
    id: string;
    label: string;
    value: string;
    onChange: (value: string) => void;
    error?: string;
    hint?: string;
    required?: boolean;
    maxLength?: number;
    numeric?: boolean; // shows the number keypad on touch devices
    placeholder?: string;
    multiline?: boolean;
    autoFocus?: boolean;
}

export default function TextField({
    id,
    label,
    value,
    onChange,
    error,
    hint,
    required = false,
    maxLength,
    numeric = false,
    placeholder,
    multiline = false,
    autoFocus = false,
}: TextFieldProps) {
    const hintId = `${id}-hint`;
    const errorId = `${id}-error`;
    const describedBy = [hint ? hintId : null, error ? errorId : null].filter(Boolean).join(" ");

    const shared = {
        id,
        value,
        placeholder,
        maxLength,
        autoFocus,
        required,
        "aria-invalid": error ? true : undefined,
        "aria-describedby": describedBy || undefined,
        className: error ? "form-field__input form-field__input--error" : "form-field__input",
    };

    return (
        <div className="form-field">
            <label htmlFor={id}>
                {label}
                {required && <span aria-hidden="true"> *</span>}
            </label>

            {multiline ? (
                <textarea {...shared} rows={4} onChange={(event) => onChange(event.target.value)} />
            ) : (
                <input
                    {...shared}
                    type="text"
                    autoComplete="off"
                    inputMode={numeric ? "numeric" : undefined}
                    onChange={(event) => onChange(event.target.value)}
                />
            )}

            {hint && (
                <p id={hintId} className="form-field__hint">
                    {hint}
                </p>
            )}
            {error && (
                <p id={errorId} className="form-field__error">
                    {error}
                </p>
            )}
        </div>
    );
}
