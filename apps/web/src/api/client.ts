// Shared fetch helper for the backend. All paths are relative ("/api/..."); the Vite dev server
// proxies them to the API (vite.config.ts).

// An error response from the API. `code` is the app error code (for example "duplicate_key")
// when the backend sent one (api.md error body).
export class ApiError extends Error {
    constructor(
        readonly status: number,
        readonly code: string | null,
        message: string,
    ) {
        super(message);
    }
}

// The raw response, after turning an error status into an ApiError. A FormData body (a file
// upload) is sent as multipart, so it must not get the JSON Content-Type.
export async function requestResponse(path: string, init: RequestInit = {}): Promise<Response> {
    const headers = init.body instanceof FormData ? init.headers : { "Content-Type": "application/json", ...init.headers };
    const response = await fetch(`/api${path}`, { ...init, headers });

    if (!response.ok) {
        let code: string | null = null;
        let message = `The server answered ${response.status}.`;
        try {
            const body = await response.json();
            // App errors: {"detail": {"code", "message"}}. Validation errors are a list instead.
            if (body?.detail && typeof body.detail === "object" && !Array.isArray(body.detail)) {
                code = body.detail.code ?? null;
                message = body.detail.message ?? message;
            }
        } catch {
            // Not JSON: keep the generic message.
        }
        throw new ApiError(response.status, code, message);
    }
    return response;
}

export async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
    const response = await requestResponse(path, init);
    if (response.status === 204) {
        return undefined as T;
    }
    return (await response.json()) as T;
}

// A message for the user, starting "Error:" (color-system).
export function errorMessage(error: unknown): string {
    if (error instanceof ApiError) {
        return `Error: ${error.message}`;
    }
    return "Error: Couldn't reach the server. Check that the API is running and try again.";
}
