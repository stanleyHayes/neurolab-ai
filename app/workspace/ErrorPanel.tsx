import { LoadingDots } from "./LoadingDots";

type ErrorPanelProps = {
  title: string;
  description: string;
  details: string;
  actionLabel: string;
  onRetry: () => void;
  busy: boolean;
};

export function ErrorPanel({
  title,
  description,
  details,
  actionLabel,
  onRetry,
  busy,
}: Readonly<ErrorPanelProps>) {
  const headingId = `error-${title.replace(/[^a-z0-9]+/gi, "-").toLowerCase()}`;

  return (
    <section
      className="workspace-error"
      role="alert"
      aria-labelledby={headingId}
    >
      <span className="workspace-error-icon" aria-hidden="true">
        !
      </span>
      <div className="workspace-error-copy">
        <h2 id={headingId}>{title}</h2>
        <p>{description}</p>
        <details>
          <summary>Technical details</summary>
          <code>{details}</code>
        </details>
      </div>
      <button
        className="quiet-button workspace-error-action"
        type="button"
        onClick={onRetry}
        disabled={busy}
        aria-busy={busy}
      >
        {actionLabel}
        {busy && <LoadingDots />}
      </button>
    </section>
  );
}
