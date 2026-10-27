"use client";

type AuthPayload = {
  access_token: string;
  expires_in: number;
  user: { user_id: string; email: string; display_name: string; role: string };
};

let redirectHandler: ((destination: string) => void) | null = null;

export function configureAuthRedirect(
  handler: (destination: string) => void,
): void {
  redirectHandler = handler;
}

let accessToken = "";
let refreshInFlight: Promise<string> | null = null;
let csrfToken = "";
let csrfBootstrap: Promise<void> | null = null;

if (typeof document !== "undefined") {
  const match = /(?:^|;\s*)neurolab_csrf=([^;]+)/.exec(document.cookie);
  if (match) csrfToken = decodeURIComponent(match[1]);
}

export function setAccessToken(token: string): void {
  accessToken = token;
}

export function getAccessToken(): string {
  return accessToken;
}

export function clearAccessToken(): void {
  accessToken = "";
  csrfToken = "";
}

function csrfCookie(): string {
  const match = /(?:^|;\s*)neurolab_csrf=([^;]+)/.exec(document.cookie);
  if (match) csrfToken = decodeURIComponent(match[1]);
  return csrfToken;
}

async function refreshAccessToken(): Promise<string> {
  if (refreshInFlight) return refreshInFlight;
  refreshInFlight = (async () => {
    const csrf = csrfCookie();
    const response = await fetch("/api/auth/refresh", {
      method: "POST",
      credentials: "same-origin",
      cache: "no-store",
      headers: csrf ? { "x-csrf-token": csrf } : {},
    });
    const payload = (await response
      .json()
      .catch(() => ({}))) as Partial<AuthPayload>;
    if (!response.ok || typeof payload.access_token !== "string") {
      clearAccessToken();
      throw new Error("Your session has expired. Please sign in again.");
    }
    accessToken = payload.access_token;
    csrfToken = csrfCookie();
    return accessToken;
  })().finally(() => {
    refreshInFlight = null;
  });
  return refreshInFlight;
}

export async function ensureCsrfCookie(): Promise<void> {
  if (csrfCookie()) return;
  csrfBootstrap ??= (async () => {
    const response = await fetch("/api/auth/csrf", {
      credentials: "same-origin",
      cache: "no-store",
    });
    if (!response.ok)
      throw new Error("Unable to initialize secure sign-in. Please retry.");
    csrfToken = csrfCookie();
    if (!csrfToken)
      throw new Error(
        "Secure sign-in cookie was not set. Check browser cookie settings.",
      );
  })().finally(() => {
    csrfBootstrap = null;
  });
  await csrfBootstrap;
}

export async function authenticatedFetch(
  url: string,
  init: RequestInit = {},
  options: { redirectOnFailure?: boolean } = {},
): Promise<Response> {
  const request = async (token: string) => {
    const headers = new Headers(init.headers);
    if (token) headers.set("authorization", `Bearer ${token}`);
    const method = (init.method ?? "GET").toUpperCase();
    if (["POST", "PUT", "PATCH", "DELETE"].includes(method)) {
      const csrf = csrfCookie();
      if (csrf) headers.set("x-csrf-token", csrf);
    }
    return fetch(url, {
      ...init,
      headers,
      credentials: "same-origin",
      cache: "no-store",
    });
  };

  let response = await request(accessToken);
  if (
    response.status !== 401 ||
    ["/api/auth/login", "/api/auth/register", "/api/auth/refresh"].includes(
      url.split("?")[0],
    )
  )
    return response;

  try {
    const token = await refreshAccessToken();
    response = await request(token);
  } catch {
    if (options.redirectOnFailure !== false && typeof window !== "undefined") {
      const next = `${window.location.pathname}${window.location.search}`;
      redirectHandler?.(`/sign-in?next=${encodeURIComponent(next)}`);
    }
    return response;
  }
  if (response.status === 401 && options.redirectOnFailure !== false) {
    accessToken = "";
    const next = `${window.location.pathname}${window.location.search}`;
    redirectHandler?.(`/sign-in?next=${encodeURIComponent(next)}`);
  }
  return response;
}

export async function authRequest<T>(
  path: string,
  init: RequestInit = {},
): Promise<T> {
  if (["register", "login"].includes(path)) await ensureCsrfCookie();
  const response = await authenticatedFetch(`/api/auth/${path}`, init, {
    redirectOnFailure: false,
  });
  const payload = (await response.json().catch(() => ({}))) as Record<
    string,
    unknown
  >;
  if (!response.ok) {
    const detail = payload.detail;
    throw new Error(
      typeof detail === "string"
        ? detail
        : `Request failed (${response.status})`,
    );
  }
  if (typeof payload.access_token === "string") {
    setAccessToken(payload.access_token);
    csrfToken = csrfCookie();
  }
  return payload as T;
}
