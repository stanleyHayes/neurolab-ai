"use client";

import Link from "next/link";
import Image from "next/image";
import { useRouter, useSearchParams } from "next/navigation";
import { Suspense, useEffect, useRef, useState } from "react";
import type { ReactNode, SyntheticEvent } from "react";
import { authRequest, ensureCsrfCookie } from "./auth-client";
import { EyeIcon, KeyIcon, LockIcon, MailIcon, UserIcon } from "./auth-icons";
import { AuthField } from "./auth/AuthField";

type AuthResponse = {
  access_token: string;
  user: { user_id: string; email: string; display_name: string; role: string };
};

function safeDestination(value: string | null): string {
  return value && value.startsWith("/") && !value.startsWith("//")
    ? value
    : "/";
}

function AuthForm({ mode }: Readonly<{ mode: "sign-in" | "register" }>) {
  const router = useRouter();
  const search = useSearchParams();
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const [csrfReady, setCsrfReady] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmation, setShowConfirmation] = useState(false);
  const [leaving, setLeaving] = useState(false);
  const navigationTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const registering = mode === "register";

  useEffect(() => {
    void ensureCsrfCookie()
      .then(() => setCsrfReady(true))
      .catch((cause: unknown) => {
        setError(
          cause instanceof Error
            ? cause.message
            : "Unable to initialize secure sign-in.",
        );
      });
    return () => {
      if (navigationTimer.current) clearTimeout(navigationTimer.current);
    };
  }, []);

  function navigateWithExit(destination: string) {
    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
      router.push(destination);
      return;
    }
    setLeaving(true);
    navigationTimer.current = setTimeout(() => router.push(destination), 260);
  }

  async function submit(event: SyntheticEvent<HTMLFormElement, SubmitEvent>) {
    event.preventDefault();
    setError("");
    setBusy(true);
    const form = new FormData(event.currentTarget);
    const data: Record<string, string> = {
      email: formText(form, "email").trim(),
      password: formText(form, "password"),
    };
    if (registering) {
      data.display_name = formText(form, "display_name").trim();
      data.invite_code = formText(form, "invite_code").trim();
      const confirmation = formText(form, "confirm_password");
      if (data.password !== confirmation) {
        setError("The passwords do not match.");
        setBusy(false);
        return;
      }
    }
    try {
      await authRequest<AuthResponse>(registering ? "register" : "login", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify(data),
      });
      const destination = safeDestination(search.get("next"));
      if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
        router.replace(destination);
        router.refresh();
      } else {
        setLeaving(true);
        navigationTimer.current = setTimeout(() => {
          router.replace(destination);
          router.refresh();
        }, 260);
      }
    } catch (cause) {
      setError(
        cause instanceof Error
          ? cause.message
          : "Authentication failed. Try again.",
      );
      setBusy(false);
    }
  }

  const field = (
    label: string,
    name: string,
    type: string,
    autocomplete: string,
    placeholder: string,
    icon: ReactNode,
    options: {
      minLength?: number;
      maxLength?: number;
      suffix?: ReactNode;
    } = {},
  ) => (
    <AuthField
      label={label}
      name={name}
      type={type}
      autocomplete={autocomplete}
      placeholder={placeholder}
      icon={icon}
      registering={registering}
      minLength={options.minLength}
      maxLength={options.maxLength}
      suffix={options.suffix}
    />
  );

  const renderedChoice1 = (() => {
    if (busy) {
      return "Please wait…";
    }
    if (!csrfReady) {
      return "Securing form…";
    }
    if (registering) {
      return "Create account";
    }
    return "Sign in";
  })();
  return (
    <main className={`auth-shell${leaving ? " auth-leaving" : ""}`}>
      <section className="auth-split" aria-label="NeuroLab account access">
        <aside className="auth-story" aria-label="About NeuroLab AI">
          <Link
            className="auth-brand"
            href="/"
            aria-label="NeuroLab AI — Discover. Experiment. Impact."
          >
            <Image
              src="/brand/04_full_horizontal.svg"
              alt="NeuroLab AI — Discover. Experiment. Impact."
              width={1800}
              height={550}
              priority
              unoptimized
            />
          </Link>
          <div className="auth-story-copy">
            <p className="auth-story-kicker">
              <span /> EVIDENCE, IN ITS ELEMENT
            </p>
            <h2>
              Better questions.
              <br />
              <em>Grounded</em> in the field.
            </h2>
            <p className="auth-story-description">
              A quieter place to explore real trial data, trace every result,
              and think carefully about what the evidence can—and can’t—tell us.
            </p>
            <div className="auth-botanical" aria-hidden="true">
              <svg viewBox="0 0 520 370" fill="none">
                <path
                  className="auth-plant-stem"
                  d="M260 370c-8-74 3-139 3-201 0-54-12-99-37-137M263 253c-46-26-88-37-129-36-37 1-69 13-97 37M261 198c41-34 81-53 122-61 38-8 74-3 108 14M262 302c39-7 74-3 105 12 31 14 56 38 76 69M256 154c-31-37-62-60-96-70-31-10-62-8-94 5"
                />
                <path
                  className="auth-plant-leaf"
                  d="M168 218c-4-42-35-71-92-83 7 42 37 70 92 83Zm183-75c18-39 53-58 106-57-21 39-56 58-106 57ZM220 87c-28-34-34-70-18-109 31 31 38 67 18 109Zm146 240c10-37 35-59 77-68-10 38-35 61-77 68Zm-202-107c-35-12-69-5-103 21 39 15 73 8 103-21Z"
                />
                <path
                  className="auth-plant-vein"
                  d="M168 218c-26-32-54-58-92-83m275 8c31-21 65-41 106-57M220 87c-6-32-12-65-18-109m112 324c31-17 65-37 106-68M164 220c-29-3-62 1-103 21"
                />
                <circle className="auth-plant-node" cx="263" cy="169" r="4" />
                <circle className="auth-plant-node" cx="260" cy="258" r="4" />
                <circle className="auth-plant-node" cx="131" cy="217" r="3" />
                <circle className="auth-plant-node" cx="383" cy="137" r="3" />
              </svg>
              <span className="auth-figure-label">
                FIELD NOTES <i>·</i> GHANA MAIZE TRIALS
              </span>
            </div>
          </div>
          <footer className="auth-story-footer">
            <span>REAL DATA. CLEAR LINEAGE.</span>
            <span>BUILT FOR CAREFUL INQUIRY</span>
          </footer>
        </aside>

        <div className="auth-form-panel">
          <section className="auth-card" aria-labelledby="auth-title">
            <p className="eyebrow">
              RESEARCH WORKSPACE <span>·</span> PRIVATE ACCESS
            </p>
            <h1 id="auth-title">
              {registering ? "Create your account" : "Welcome back"}
            </h1>
            <p className="auth-description">
              {registering
                ? "Create a secure researcher account for your private research runs. Registration requires an operator-issued invite code."
                : "Sign in to continue to your private research workspace."}
            </p>
            <form className="auth-form" onSubmit={submit}>
              {registering &&
                field(
                  "Display name",
                  "display_name",
                  "text",
                  "name",
                  "e.g. Ada Mensah",
                  <UserIcon />,
                  { maxLength: 80 },
                )}
              {field(
                "Email address",
                "email",
                "email",
                "email",
                "you@institution.org",
                <MailIcon />,
                { maxLength: 254 },
              )}
              {field(
                "Password",
                "password",
                showPassword ? "text" : "password",
                registering ? "new-password" : "current-password",
                "Enter your password",
                <LockIcon />,
                {
                  minLength: registering ? 12 : 1,
                  maxLength: 1024,
                  suffix: (
                    <button
                      className="auth-password-toggle"
                      type="button"
                      onClick={() => setShowPassword((visible) => !visible)}
                      aria-label={
                        showPassword ? "Hide password" : "Show password"
                      }
                      aria-pressed={showPassword}
                    >
                      <EyeIcon visible={showPassword} />
                    </button>
                  ),
                },
              )}
              {registering && (
                <>
                  {field(
                    "Confirm password",
                    "confirm_password",
                    showConfirmation ? "text" : "password",
                    "new-password",
                    "Re-enter your password",
                    <LockIcon />,
                    {
                      minLength: 12,
                      maxLength: 1024,
                      suffix: (
                        <button
                          className="auth-password-toggle"
                          type="button"
                          onClick={() =>
                            setShowConfirmation((visible) => !visible)
                          }
                          aria-label={
                            showConfirmation
                              ? "Hide confirmation"
                              : "Show confirmation"
                          }
                          aria-pressed={showConfirmation}
                        >
                          <EyeIcon visible={showConfirmation} />
                        </button>
                      ),
                    },
                  )}
                  {field(
                    "Invitation code",
                    "invite_code",
                    "text",
                    "off",
                    "Enter your invite code",
                    <KeyIcon />,
                    { maxLength: 256 },
                  )}
                </>
              )}
              {error && (
                <p className="auth-error" role="alert">
                  {error}
                </p>
              )}
              <button
                className="primary-button auth-submit"
                type="submit"
                disabled={busy || !csrfReady || leaving}
                aria-busy={busy || !csrfReady}
              >
                <span>{renderedChoice1}</span>
                <svg aria-hidden="true" viewBox="0 0 20 20" fill="none">
                  <path d="M3.5 10h12m-5-5 5 5-5 5" />
                </svg>
              </button>
            </form>
            <p className="auth-switch">
              {registering ? "Already registered?" : "New to NeuroLab?"}{" "}
              <Link
                href={registering ? "/sign-in" : "/register"}
                onClick={(event) => {
                  if (
                    event.metaKey ||
                    event.ctrlKey ||
                    event.shiftKey ||
                    event.altKey ||
                    event.button !== 0
                  )
                    return;
                  event.preventDefault();
                  navigateWithExit(registering ? "/sign-in" : "/register");
                }}
              >
                {registering ? "Sign in" : "Create an account"}
                <span aria-hidden="true"> ↗</span>
              </Link>
            </p>
            <p className="auth-security">
              <LockIcon />{" "}
              <span>
                Your access token stays in memory. Refresh credentials use
                HttpOnly cookies.
              </span>
            </p>
          </section>
          <p className="auth-panel-foot">
            NEUROLAB AI <span>·</span> RESEARCH PROTOTYPE
          </p>
        </div>
      </section>
    </main>
  );
}

export function AuthPage({ mode }: Readonly<{ mode: "sign-in" | "register" }>) {
  return (
    <Suspense
      fallback={
        <main className="auth-shell">
          <p className="auth-loading">Loading secure sign-in…</p>
        </main>
      }
    >
      <AuthForm mode={mode} />
    </Suspense>
  );
}

function formText(form: FormData, name: string): string {
  const value = form.get(name);
  return typeof value === "string" ? value : "";
}
