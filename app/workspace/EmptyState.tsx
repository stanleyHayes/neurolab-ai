import type { ReactNode } from "react";

type EmptyStateProps = {
  icon: "evidence" | "events" | "archive" | "report" | "insight";
  title: string;
  description: string;
  action?: ReactNode;
  compact?: boolean;
};

const ICON_PATHS: Record<EmptyStateProps["icon"], string> = {
  evidence:
    "M11 33V23l7-6 6 4 8-10 6 3v19H11Z M15 29h4v4h-4z M23 25h4v8h-4z M31 21h4v12h-4z",
  events: "M14 13h20 M14 24h20 M14 35h20 M9 13h.1 M9 24h.1 M9 35h.1",
  archive: "M9 15h30v7H9z M12 22v15h24V22 M19 28h10",
  report: "M14 9h14l7 7v23H14z M28 9v8h7 M19 24h11 M19 30h11 M19 36h7",
  insight:
    "M24 8v8 M24 32v8 M8 24h8 M32 24h8 M12.7 12.7l5.7 5.7 M29.6 29.6l5.7 5.7 M35.3 12.7l-5.7 5.7 M18.4 29.6l-5.7 5.7 M24 19a5 5 0 1 0 0 10 5 5 0 0 0 0-10Z",
};

export function EmptyState({
  icon,
  title,
  description,
  action,
  compact = false,
}: Readonly<EmptyStateProps>) {
  return (
    <div className={`empty-state${compact ? " empty-state-compact" : ""}`}>
      <svg
        className="empty-state-icon"
        viewBox="0 0 48 48"
        aria-hidden="true"
        focusable="false"
      >
        <circle className="empty-state-orbit" cx="24" cy="24" r="19" />
        <path className="empty-state-mark" d={ICON_PATHS[icon]} />
        <circle className="empty-state-pulse" cx="38" cy="16" r="2.5" />
      </svg>
      <h3>{title}</h3>
      <p>{description}</p>
      {action && <div className="empty-state-actions">{action}</div>}
    </div>
  );
}
