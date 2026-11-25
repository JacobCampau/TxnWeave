// Backend timestamps (ISO, UTC) shown in the agent's local time.

function pad(value: number): string {
    return String(value).padStart(2, "0");
}

// "18:05" (24-hour, like the forms)
export function localTime(iso: string): string {
    const when = new Date(iso);
    return `${pad(when.getHours())}:${pad(when.getMinutes())}`;
}

// "03-14-2026" (the forms' date format)
export function localDate(iso: string): string {
    const when = new Date(iso);
    return `${pad(when.getMonth() + 1)}-${pad(when.getDate())}-${when.getFullYear()}`;
}
