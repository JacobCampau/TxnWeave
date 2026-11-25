import { createContext, useCallback, useContext, useEffect, useRef, useState, type ReactNode } from "react";

// Toasts (app-shell's Toast, UI-18): short messages in the bottom-right corner that go away by
// themselves. Success is slate and error is crimson, both with white text (color-system).

type ToastKind = "success" | "error";

interface ToastMessage {
    id: number;
    kind: ToastKind;
    text: string;
}

type ShowToast = (text: string, kind?: ToastKind) => void;

const ToastContext = createContext<ShowToast>(() => {});

const VISIBLE_MS = 5000;

// Any component under the provider can call useToast()(message, kind).
export function useToast(): ShowToast {
    return useContext(ToastContext);
}

export function ToastProvider({ children }: { children: ReactNode }) {
    const [toasts, setToasts] = useState<ToastMessage[]>([]);
    const nextId = useRef(1);

    const dismiss = useCallback((id: number) => setToasts((all) => all.filter((toast) => toast.id !== id)), []);

    const show = useCallback<ShowToast>((text, kind = "success") => {
        const id = nextId.current++;
        setToasts((all) => [...all, { id, kind, text }]);
    }, []);

    return (
        <ToastContext.Provider value={show}>
            {children}
            {/* Screen readers announce new toasts; errors interrupt (role="alert"). */}
            <div className="toast-region" aria-live="polite">
                {toasts.map((toast) => (
                    <ToastItem key={toast.id} toast={toast} onDismiss={dismiss} />
                ))}
            </div>
        </ToastContext.Provider>
    );
}

function ToastItem({ toast, onDismiss }: { toast: ToastMessage; onDismiss: (id: number) => void }) {
    useEffect(() => {
        const timer = window.setTimeout(() => onDismiss(toast.id), VISIBLE_MS);
        return () => window.clearTimeout(timer);
    }, [toast.id, onDismiss]);

    return (
        <div className={`toast toast--${toast.kind}`} role={toast.kind === "error" ? "alert" : "status"}>
            <span>{toast.text}</span>
            <button type="button" className="toast__close" aria-label="Dismiss" onClick={() => onDismiss(toast.id)}>
                ×
            </button>
        </div>
    );
}
