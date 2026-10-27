"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import type { SyntheticEvent } from "react";
import {
  authenticatedFetch,
  authRequest,
  clearAccessToken,
  configureAuthRedirect,
  ensureCsrfCookie,
} from "../../auth-client";

type User = {
  email: string;
  display_name: string;
  role: string;
  created_at: string;
};

export default function AccountSettingsPage() {
  const router = useRouter();
  const [user, setUser] = useState<User | null>(null);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    configureAuthRedirect((destination) => router.replace(destination));
  }, [router]);

  useEffect(() => {
    let active = true;
    void ensureCsrfCookie()
      .then(() => authenticatedFetch("/api/auth/me"))
      .then(async (response) => {
        if (!response.ok) throw new Error("Sign in to view account settings.");
        const data = (await response.json()) as User;
        if (active) setUser(data);
      })
      .catch((cause: unknown) => {
        if (active)
          setError(
            cause instanceof Error
              ? cause.message
              : "Could not load account settings.",
          );
      });
    return () => {
      active = false;
    };
  }, []);

  async function updateProfile(
    event: SyntheticEvent<HTMLFormElement, SubmitEvent>,
  ) {
    event.preventDefault();
    setError("");
    setNotice("");
    setBusy(true);
    const form = new FormData(event.currentTarget);
    try {
      const updated = await authRequest<User>("me", {
        method: "PATCH",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({
          display_name: formText(form, "display_name").trim(),
        }),
      });
      setUser(updated);
      setNotice("Profile updated.");
    } catch (cause) {
      setError(
        cause instanceof Error ? cause.message : "Could not update profile.",
      );
    } finally {
      setBusy(false);
    }
  }

  async function changePassword(
    event: SyntheticEvent<HTMLFormElement, SubmitEvent>,
  ) {
    event.preventDefault();
    const formElement = event.currentTarget;
    setError("");
    setNotice("");
    const form = new FormData(event.currentTarget);
    const currentPassword = formText(form, "current_password");
    const newPassword = formText(form, "new_password");
    if (newPassword !== formText(form, "confirm_password")) {
      setError("The new passwords do not match.");
      return;
    }
    setBusy(true);
    try {
      const response = await authenticatedFetch("/api/auth/change-password", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({
          current_password: currentPassword,
          new_password: newPassword,
        }),
      });
      if (!response.ok) {
        const payload = (await response.json().catch(() => ({}))) as {
          detail?: string;
        };
        throw new Error(payload.detail ?? "Could not change password.");
      }
      formElement.reset();
      setNotice("Password changed. Other sessions have been signed out.");
    } catch (cause) {
      setError(
        cause instanceof Error ? cause.message : "Could not change password.",
      );
    } finally {
      setBusy(false);
    }
  }

  async function signOut(all: boolean) {
    setError("");
    setBusy(true);
    try {
      await ensureCsrfCookie();
      const match = /(?:^|;\s*)neurolab_csrf=([^;]+)/.exec(document.cookie);
      const csrf = match ? decodeURIComponent(match[1]) : "";
      const response = await authenticatedFetch(
        `/api/auth/${all ? "logout-all" : "logout"}`,
        {
          method: "POST",
          headers: csrf ? { "x-csrf-token": csrf } : {},
        },
      );
      if (!response.ok)
        throw new Error("Could not end the session. Please retry.");
      clearAccessToken();
      document.cookie = "neurolab_csrf=; path=/; max-age=0; samesite=lax";
      router.replace("/sign-in");
      router.refresh();
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Could not sign out.");
      setBusy(false);
    }
  }

  return (
    <main className="account-shell">
      <header className="account-header">
        <Link className="auth-brand" href="/">
          ◈ <span>NEUROLAB AI</span>
        </Link>
        <Link className="text-link" href="/">
          Back to workspace
        </Link>
      </header>
      <section className="account-content" aria-labelledby="account-title">
        <p className="eyebrow">IDENTITY & SECURITY</p>
        <h1 id="account-title">Account settings</h1>
        <p className="auth-description">
          Manage your researcher profile and credentials.
        </p>
        {error && (
          <p className="auth-error" role="alert">
            {error}
          </p>
        )}
        {notice && <output className="account-notice">{notice}</output>}
        <article className="card account-card">
          <h2>Researcher profile</h2>
          <p className="auth-description">
            Signed in as <strong>{user?.email ?? "Loading…"}</strong>
          </p>
          <form className="auth-form" onSubmit={updateProfile}>
            <label>
              <span>Display name</span>
              <input
                name="display_name"
                autoComplete="name"
                required
                minLength={1}
                maxLength={80}
                defaultValue={user?.display_name ?? ""}
                key={user?.display_name ?? "loading"}
              />
            </label>
            <button
              className="primary-button"
              type="submit"
              disabled={busy || !user}
            >
              Save profile
            </button>
          </form>
        </article>
        <article className="card account-card">
          <h2>Change password</h2>
          <form className="auth-form" onSubmit={changePassword}>
            <label>
              <span>Current password</span>
              <input
                name="current_password"
                type="password"
                autoComplete="current-password"
                required
                maxLength={1024}
              />
            </label>
            <label>
              <span>New password</span>
              <input
                name="new_password"
                type="password"
                autoComplete="new-password"
                required
                minLength={12}
                maxLength={1024}
              />
              <small>Use at least 12 characters.</small>
            </label>
            <label>
              <span>Confirm new password</span>
              <input
                name="confirm_password"
                type="password"
                autoComplete="new-password"
                required
                minLength={12}
                maxLength={1024}
              />
            </label>
            <button className="primary-button" type="submit" disabled={busy}>
              Change password
            </button>
          </form>
        </article>
        <article className="card account-card signout-actions">
          <h2>Sessions</h2>
          <p>Sign out here, or revoke all your active sessions.</p>
          <button
            className="secondary-button"
            type="button"
            onClick={() => void signOut(false)}
            disabled={busy}
          >
            Sign out
          </button>
          <button
            className="quiet-button"
            type="button"
            onClick={() => void signOut(true)}
            disabled={busy}
          >
            Sign out all sessions
          </button>
        </article>
        <p className="auth-security">
          Password recovery requires a verified operator-assisted reset. No
          email reset channel is configured.
        </p>
      </section>
    </main>
  );
}

function formText(form: FormData, name: string): string {
  const value = form.get(name);
  return typeof value === "string" ? value : "";
}
