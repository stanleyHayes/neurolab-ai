export function MailIcon() {
  return (
    <svg viewBox="0 0 20 20" fill="none">
      <rect x="2.5" y="4" width="15" height="12" rx="2" />
      <path d="m3.5 5 6.5 5 6.5-5" />
    </svg>
  );
}

export function UserIcon() {
  return (
    <svg viewBox="0 0 20 20" fill="none">
      <circle cx="10" cy="6.2" r="3.1" />
      <path d="M3.8 17c.5-3 2.7-4.7 6.2-4.7s5.7 1.7 6.2 4.7" />
    </svg>
  );
}

export function LockIcon() {
  return (
    <svg viewBox="0 0 20 20" fill="none">
      <rect x="3.5" y="8.5" width="13" height="9" rx="2" />
      <path d="M6.5 8.5V6a3.5 3.5 0 0 1 7 0v2.5M10 12v2" />
    </svg>
  );
}

export function KeyIcon() {
  return (
    <svg viewBox="0 0 20 20" fill="none">
      <circle cx="7" cy="10" r="3.5" />
      <path d="m9.6 12.5 6 5m-2-3 2-2m-4 0 2-2" />
    </svg>
  );
}

export function EyeIcon({ visible }: Readonly<{ visible: boolean }>) {
  return visible ? (
    <svg viewBox="0 0 20 20" fill="none">
      <path d="M2 10s2.8-5 8-5 8 5 8 5-2.8 5-8 5-8-5-8-5Z" />
      <circle cx="10" cy="10" r="2.2" />
    </svg>
  ) : (
    <svg viewBox="0 0 20 20" fill="none">
      <path d="M2 10s2.8-5 8-5 8 5 8 5-2.8 5-8 5-8-5-8-5Z" />
      <circle cx="10" cy="10" r="2.2" />
      <path d="m4 16 12-12" />
    </svg>
  );
}
