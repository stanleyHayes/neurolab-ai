"use client";

import Link from "next/link";
import { ResearchWorkspace } from "../../research-workspace";
import { UserIcon, LockIcon, EyeIcon } from "../../auth-icons";
import { ResultIcon } from "../../workspace/ResultIcon";
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

  const initials =
    user?.display_name
      .trim()
      .split(/\s+/)
      .map((part) => part[0])
      .slice(0, 2)
      .join("")
      .toUpperCase() || "NL";
  const joined = user ? new Date(user.created_at) : null;
  const joinedLabel =
    joined && Number.isFinite(joined.getTime())
      ? joined.toLocaleDateString("en-GB", {
          month: "long",
          year: "numeric",
          timeZone: "Africa/Accra",
        })
      : null;

  return (
    <ResearchWorkspace
      section="settings"
      pageTitle="Account settings"
      accountDisplayName={user?.display_name}
    >
      <section
        className="account-redesign account-in-workspace"
        aria-label="Account settings"
      >
        <section className="account-content" aria-labelledby="account-title">
          <div className="account-page-heading">
            <p className="eyebrow">YOUR RESEARCH WORKSPACE</p>
            <h1 id="account-title">Account settings</h1>
            <p>
              Manage your researcher identity, password and signed-in sessions.
            </p>
          </div>
          {error && (
            <p className="auth-error" role="alert">
              {error}
            </p>
          )}
          {notice && <output className="account-notice">{notice}</output>}
          <div className="account-layout">
            <aside
              className="account-identity"
              aria-label="Researcher identity"
              aria-busy={!user && !error}
            >
              <span className="account-identity-avatar" aria-hidden="true">
                {initials}
              </span>
              <h2>{user?.display_name ?? "Loading profile…"}</h2>
              <p className="account-identity-email">
                {user?.email ?? "Your account details will appear here."}
              </p>
              {user && <span className="account-role">{user.role}</span>}
              {joinedLabel && (
                <p className="account-joined">Member since {joinedLabel}</p>
              )}
              <Link
                className="account-workspace-return"
                href="/"
                aria-label="Back to workspace"
              >
                <ResultIcon name="arrow" /> Back to workspace
              </Link>
              <nav
                className="account-section-nav"
                aria-label="Account sections"
              >
                <a href="#researcher-profile">
                  <UserIcon /> Researcher profile <span>↗</span>
                </a>
                <a href="#account-password">
                  <LockIcon /> Password <span>↗</span>
                </a>
                <a href="#account-sessions">
                  <ResultIcon name="retention" /> Sessions <span>↗</span>
                </a>
              </nav>
              <Link className="account-evidence-link" href="/reports">
                <ResultIcon name="record" />
                <span>Return to your research reports</span>
              </Link>
            </aside>
            <div className="account-panels">
              <article
                className="account-panel"
                id="researcher-profile"
                aria-labelledby="profile-heading"
              >
                <div className="account-panel-heading">
                  <span className="account-section-icon" aria-hidden="true">
                    <UserIcon />
                  </span>
                  <div>
                    <h2 id="profile-heading">Researcher profile</h2>
                    <p>Choose the name shown in your workspace.</p>
                  </div>
                </div>
                <form
                  className="auth-form account-profile-form"
                  onSubmit={updateProfile}
                >
                  <label>
                    <span>Display name</span>
                    <span className="auth-input-wrap">
                      <span className="auth-field-icon" aria-hidden="true">
                        <UserIcon />
                      </span>
                      <input
                        name="display_name"
                        placeholder="Enter your researcher name"
                        autoComplete="name"
                        required
                        minLength={1}
                        maxLength={80}
                        defaultValue={user?.display_name ?? ""}
                        key={user?.display_name ?? "loading"}
                        disabled={!user || busy}
                      />
                    </span>
                  </label>
                  <div className="account-form-footer">
                    <span>Keep your name recognizable.</span>
                    <button
                      className="primary-button"
                      type="submit"
                      disabled={busy || !user}
                    >
                      <ResultIcon name="save" /> Save profile
                    </button>
                  </div>
                </form>
              </article>
              <article
                className="account-panel"
                id="account-password"
                aria-labelledby="password-heading"
              >
                <div className="account-panel-heading">
                  <span className="account-section-icon" aria-hidden="true">
                    <LockIcon />
                  </span>
                  <div>
                    <h2 id="password-heading">Change password</h2>
                    <p>
                      Use a unique password to protect access to your research.
                    </p>
                  </div>
                </div>
                <form
                  className="auth-form account-password-form"
                  onSubmit={changePassword}
                >
                  <AccountPasswordField
                    name="current_password"
                    label="Current password"
                    placeholder="Enter your current password"
                    disabled={!user || busy}
                    current
                  />
                  <AccountPasswordField
                    name="new_password"
                    label="New password"
                    placeholder="Create a new password"
                    disabled={!user || busy}
                  />
                  <AccountPasswordField
                    name="confirm_password"
                    label="Confirm new password"
                    placeholder="Re-enter your new password"
                    disabled={!user || busy}
                  />
                  <div className="account-form-footer">
                    <span>
                      Changing your password signs out other sessions.
                    </span>
                    <button
                      className="secondary-button"
                      type="submit"
                      disabled={busy || !user}
                    >
                      <LockIcon /> Change password
                    </button>
                  </div>
                </form>
              </article>
              <article
                className="account-panel"
                id="account-sessions"
                aria-labelledby="sessions-heading"
              >
                <div className="account-panel-heading">
                  <span className="account-section-icon" aria-hidden="true">
                    <ResultIcon name="retention" />
                  </span>
                  <div>
                    <h2 id="sessions-heading">Sessions</h2>
                    <p>End this session or sign out on every device.</p>
                  </div>
                </div>
                <div className="account-session-row">
                  <div>
                    <h3>This session</h3>
                    <p>Sign out of the account in this browser.</p>
                  </div>
                  <button
                    className="secondary-button"
                    type="button"
                    onClick={() => void signOut(false)}
                    disabled={busy || !user}
                  >
                    Sign out <ResultIcon name="arrow" />
                  </button>
                </div>
                <div className="account-session-row">
                  <div>
                    <h3>All sessions</h3>
                    <p>
                      You will need to sign in again on each device, including
                      this one.
                    </p>
                  </div>
                  <button
                    className="quiet-button"
                    type="button"
                    onClick={() => void signOut(true)}
                    disabled={busy || !user}
                  >
                    Sign out all sessions <ResultIcon name="arrow" />
                  </button>
                </div>
              </article>
              <div className="account-recovery-note">
                <ResultIcon name="caution" />
                <p>
                  <strong>Need help recovering your account?</strong>
                  <span>
                    Password recovery requires a verified operator-assisted
                    reset. No email reset channel is configured.
                  </span>
                </p>
              </div>
            </div>
          </div>
        </section>
      </section>
    </ResearchWorkspace>
  );
}

function AccountPasswordField({
  name,
  label,
  placeholder,
  disabled,
  current = false,
}: Readonly<{
  name: string;
  label: string;
  placeholder: string;
  disabled: boolean;
  current?: boolean;
}>) {
  const [visible, setVisible] = useState(false);
  const labelId = `account-${name}-label`;
  return (
    <label className={current ? "account-current-password" : undefined}>
      <span id={labelId}>{label}</span>
      <span className="auth-input-wrap">
        <span className="auth-field-icon" aria-hidden="true">
          <LockIcon />
        </span>
        <input
          name={name}
          aria-labelledby={labelId}
          aria-describedby={
            name === "new_password" ? "account-password-help" : undefined
          }
          type={visible ? "text" : "password"}
          autoComplete={current ? "current-password" : "new-password"}
          required
          minLength={current ? undefined : 12}
          maxLength={1024}
          placeholder={placeholder}
          disabled={disabled}
        />
        <button
          className="auth-password-toggle"
          type="button"
          aria-label={`${visible ? "Hide" : "Show"} ${label.toLowerCase()}`}
          aria-pressed={visible}
          onClick={() => setVisible((value) => !value)}
          disabled={disabled}
        >
          <EyeIcon visible={visible} />
        </button>
      </span>
      {name === "new_password" && (
        <small id="account-password-help">Use at least 12 characters.</small>
      )}
    </label>
  );
}

function formText(form: FormData, name: string): string {
  const value = form.get(name);
  return typeof value === "string" ? value : "";
}
