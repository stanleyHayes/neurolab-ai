import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, expect, it, vi } from "vitest";
import SignInPage from "../../app/sign-in/page";
import RegisterPage from "../../app/register/page";
import AccountSettingsPage from "../../app/settings/account/page";
import UnauthorizedPage from "../../app/unauthorized/page";
import { navigation } from "./navigation";
import {
  authRequest,
  authenticatedFetch,
  clearAccessToken,
  configureAuthRedirect,
  getAccessToken,
  setAccessToken,
} from "../../app/auth-client";

const user = {
  user_id: "fixture-owner",
  email: "fixture@example.test",
  display_name: "Fixture Researcher",
  role: "researcher",
  created_at: "2026-10-27T00:00:00Z",
};
const payload = { access_token: "fixture-access", expires_in: 720, user };
beforeEach(() => {
  clearAccessToken();
  navigation.router.replace.mockClear();
  vi.stubGlobal(
    "fetch",
    vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
      const url = String(input);
      if (url.endsWith("/csrf")) {
        document.cookie = "neurolab_csrf=fixture-csrf; path=/";
        return Response.json({ csrf_ready: true });
      }
      if (url.endsWith("/me"))
        return Response.json(
          init?.method === "PATCH"
            ? { ...user, display_name: "Updated Researcher" }
            : user,
        );
      if (url.endsWith("/change-password") || url.includes("/logout"))
        return new Response(null, { status: 204 });
      return Response.json(payload);
    }),
  );
});

it("signs in with CSRF and retains access credentials only in memory", async () => {
  render(<SignInPage />);
  const submit = await screen.findByRole("button", { name: "Sign in" });
  fireEvent.change(screen.getByLabelText("Email address"), {
    target: { value: user.email },
  });
  fireEvent.change(screen.getByLabelText("Password"), {
    target: { value: "fixture-password-long" },
  });
  fireEvent.click(screen.getByRole("button", { name: "Show password" }));
  expect((screen.getByLabelText("Password") as HTMLInputElement).type).toBe(
    "text",
  );
  fireEvent.click(submit);
  await waitFor(() =>
    expect(navigation.router.replace).toHaveBeenCalledWith("/"),
  );
  expect(getAccessToken()).toBe(payload.access_token);
  expect(localStorage.getItem("access_token")).toBeNull();
  expect(sessionStorage.getItem("access_token")).toBeNull();
});

it("validates matching registration passwords before calling the server", async () => {
  render(<RegisterPage />);
  await screen.findByRole("button", { name: "Create account" });
  fireEvent.change(screen.getByLabelText("Password"), {
    target: { value: "fixture-password-one" },
  });
  fireEvent.change(screen.getByLabelText("Confirm password"), {
    target: { value: "fixture-password-two" },
  });
  fireEvent.submit(
    screen.getByRole("button", { name: "Create account" }).closest("form")!,
  );
  expect(await screen.findByRole("alert")).toHaveProperty(
    "textContent",
    "The passwords do not match.",
  );
  expect(
    vi
      .mocked(fetch)
      .mock.calls.some(([url]) => String(url).endsWith("/register")),
  ).toBe(false);
  fireEvent.change(screen.getByLabelText("Confirm password"), {
    target: { value: "fixture-password-one" },
  });
  fireEvent.click(screen.getByRole("button", { name: "Show confirmation" }));
  fireEvent.submit(
    screen.getByRole("button", { name: "Create account" }).closest("form")!,
  );
  await waitFor(() =>
    expect(navigation.router.replace).toHaveBeenCalledWith("/"),
  );
});

it("updates profile and changes password with current-password confirmation", async () => {
  render(<AccountSettingsPage />);
  await screen.findByText(user.email);
  fireEvent.change(screen.getByLabelText("Display name"), {
    target: { value: "Updated Researcher" },
  });
  fireEvent.submit(screen.getByLabelText("Display name").closest("form")!);
  expect(await screen.findByRole("status")).toHaveProperty(
    "textContent",
    "Profile updated.",
  );
  fireEvent.change(screen.getByLabelText("Current password"), {
    target: { value: "fixture-password-current" },
  });
  fireEvent.change(screen.getByLabelText("New password"), {
    target: { value: "fixture-password-new" },
  });
  fireEvent.change(screen.getByLabelText("Confirm new password"), {
    target: { value: "mismatch" },
  });
  fireEvent.submit(screen.getByLabelText("Current password").closest("form")!);
  expect(await screen.findByRole("alert")).toHaveProperty(
    "textContent",
    "The new passwords do not match.",
  );
  fireEvent.change(screen.getByLabelText("Confirm new password"), {
    target: { value: "fixture-password-new" },
  });
  fireEvent.submit(screen.getByLabelText("Current password").closest("form")!);
  expect(
    await screen.findByText(
      "Password changed. Other sessions have been signed out.",
    ),
  ).toBeTruthy();
  fireEvent.click(screen.getByRole("button", { name: "Sign out" }));
  await waitFor(() =>
    expect(navigation.router.replace).toHaveBeenCalledWith("/sign-in"),
  );
  expect(getAccessToken()).toBe("");
});

it("coalesces concurrent refreshes and retries with the rotated access credential", async () => {
  document.cookie = "neurolab_csrf=fixture-csrf; path=/";
  setAccessToken("expired-fixture");
  vi.stubGlobal(
    "fetch",
    vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
      if (String(input).endsWith("/refresh")) return Response.json(payload);
      return new Response("{}", {
        status:
          new Headers(init?.headers).get("authorization") ===
          "Bearer fixture-access"
            ? 200
            : 401,
      });
    }),
  );
  const responses = await Promise.all([
    authenticatedFetch("/api/private"),
    authenticatedFetch("/api/private"),
  ]);
  expect(responses.every((response) => response.ok)).toBe(true);
  expect(
    vi
      .mocked(fetch)
      .mock.calls.filter(([url]) => String(url).endsWith("/refresh")),
  ).toHaveLength(1);
});

it("clears a rejected refresh and redirects without leaking provider errors", async () => {
  document.cookie = "neurolab_csrf=fixture-csrf; path=/";
  const redirect = vi.fn();
  configureAuthRedirect(redirect);
  vi.stubGlobal(
    "fetch",
    vi.fn(async () => new Response("{}", { status: 401 })),
  );
  const response = await authenticatedFetch("/api/private");
  expect(response.status).toBe(401);
  expect(getAccessToken()).toBe("");
  expect(redirect).toHaveBeenCalledWith(
    expect.stringContaining("/sign-in?next="),
  );
  await expect(authRequest("login", { method: "POST" })).rejects.toThrow();
});

it("explains owner-only access on the restricted page", () => {
  render(<UnauthorizedPage />);
  expect(
    screen.getByRole("heading", { name: "You don’t have access" }),
  ).toBeTruthy();
  expect(
    screen
      .getByRole("link", { name: /Return to sign in/ })
      .getAttribute("href"),
  ).toBe("/sign-in");
});
