export function Skeleton({ className = "" }: Readonly<{ className?: string }>) {
  return <span className={`skeleton ${className}`} aria-hidden="true" />;
}
