import Link from "next/link";

export default function UnauthorizedPage() {
  return (
    <main className="auth-shell">
      <section className="auth-card" aria-labelledby="unauthorized-title">
        <Link className="auth-brand" href="/">
          ◈ <span>NEUROLAB AI</span>
        </Link>
        <p className="eyebrow">ACCESS RESTRICTED</p>
        <h1 id="unauthorized-title">You don’t have access</h1>
        <p className="auth-description">
          This research resource is private to its owner or your session has
          expired.
        </p>
        <Link className="primary-link" href="/sign-in">
          Return to sign in <span aria-hidden="true">↗</span>
        </Link>
      </section>
    </main>
  );
}
