interface ApiErrorBannerProps {
    message: string;
    onRetry: () => void;
}

// Shown under the top bar when the app can't load from the backend (app-shell's ApiErrorBanner).
// Crimson with white text, and an ink Retry button (color-system).
export default function ApiErrorBanner({ message, onRetry }: ApiErrorBannerProps) {
    return (
        <div className="api-error-banner" role="alert">
            <span>{message}</span>
            <button type="button" className="button api-error-banner__retry" onClick={onRetry}>
                Retry
            </button>
        </div>
    );
}
