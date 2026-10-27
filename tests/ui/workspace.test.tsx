import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import fixture from "../fixtures/ghana-ui.json";
import { navigation } from "./navigation";
import { ResearchWorkspace } from "../../app/research-workspace";
import { SECTION_COPY } from "../../app/workspace/workspace-config";
import type { WorkspaceSection } from "../../app/workspace/workspace-types";
import { setAccessToken } from "../../app/auth-client";

const runId = fixture.report.run_id;
const eventStream = fixture.events
  .map(
    (event) =>
      `id: ${event.sequence}\nevent: ${event.event_type}\ndata: ${JSON.stringify(event)}\n\n`,
  )
  .join("");
const reply = (value: unknown, status = 200) =>
  Response.json(value, { status });

function seedSavedRun(section: WorkspaceSection) {
  navigation.pathname = section === "overview" ? "/" : `/${section}`;
  sessionStorage.setItem(
    "neurolab-research-state:fixture-user",
    JSON.stringify({
      objective: fixture.report.objective,
      runId,
      runStatus: "COMPLETE",
      mode: "replay",
    }),
  );
}

beforeEach(() => {
  setAccessToken("test-fixture-access-token");
  vi.stubGlobal(
    "fetch",
    vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
      const url = String(input);
      if (url === "/api/research-draft")
        return reply({ revision: 0, draft: {}, updated_at: null });
      if (url === "/api/auth/me")
        return reply({
          user_id: "fixture-user",
          email: "fixture@example.test",
          display_name: "Fixture Researcher",
        });
      if (url.endsWith("/profile")) return reply(fixture.profile);
      if (url.endsWith("/artifacts")) return reply(fixture.artifacts);
      if (url.includes("/events?"))
        return new Response(eventStream, {
          headers: { "content-type": "text/event-stream" },
        });
      if (url.includes("?limit="))
        return reply([
          {
            run_id: runId,
            objective: fixture.report.objective,
            status: "COMPLETE",
            created_at: fixture.events[0].timestamp,
            source_sha256: fixture.report.source_sha256,
          },
        ]);
      if (url === "/api/research-runs" && init?.method === "POST")
        return reply({ run_id: runId, status: "QUEUED", report: null }, 202);
      if (url.endsWith("/cancel"))
        return reply({ run_id: runId, status: "cancel_requested" });
      if (url === `/api/research-runs/${runId}`)
        return reply({ status: "COMPLETE", report: fixture.report });
      return reply({ detail: "Unexpected test route: " + url }, 404);
    }),
  );
});

describe("authenticated real-data replay workspace", () => {
  it.each<WorkspaceSection>([
    "overview",
    "research-results",
    "genotype-explorer",
    "trait-analytics",
    "environments",
    "data-library",
    "ai-insights",
    "reports",
    "settings",
    "next-experiments",
  ])("restores %s from authorized persisted outputs", async (section) => {
    seedSavedRun(section);
    render(<ResearchWorkspace section={section} />);
    await screen.findByRole("link", {
      name: /Account settings for Fixture Researcher/,
    });
    await waitFor(() =>
      expect(fetch).toHaveBeenCalledWith(
        expect.stringContaining(`/api/research-runs/${runId}/events`),
        expect.objectContaining({ headers: expect.any(Headers) }),
      ),
    );
    if (section === "data-library") {
      expect(
        await screen.findByText(fixture.report.source_sha256),
      ).toBeTruthy();
      expect(
        await screen.findByText("Selected run matches this source"),
      ).toBeTruthy();
    } else if (section === "overview")
      expect(await screen.findByText("864")).toBeTruthy();
    else
      expect(
        screen.getByRole("heading", {
          name: SECTION_COPY[section].title,
          level: 1,
        }),
      ).toBeTruthy();
  });

  it("submits the exact objective and displays backend completion after a queued run", async () => {
    navigation.pathname = "/experiment-studio";
    render(<ResearchWorkspace section="experiment-studio" />);
    await screen.findByRole("link", {
      name: /Account settings for Fixture Researcher/,
    });
    const objective =
      "Observe Ghana patterns\nKeep every constraint unchanged.";
    fireEvent.change(screen.getByLabelText("Research question"), {
      target: { value: objective },
    });
    fireEvent.click(
      screen.getByRole("button", { name: /Generate experiment plan/ }),
    );
    await waitFor(() => expect(screen.getByText(/Run complete/)).toBeTruthy());
    const call = vi
      .mocked(fetch)
      .mock.calls.find(
        ([url, init]) =>
          url === "/api/research-runs" && init?.method === "POST",
      );
    expect(JSON.parse(String(call?.[1]?.body)).objective).toBe(objective);
    expect(
      screen.queryByRole("button", { name: "Request cancellation" }),
    ).toBeNull();
  });

  it("replays saved terminal events without inventing extra measurements", async () => {
    seedSavedRun("live-experiment");
    render(<ResearchWorkspace section="live-experiment" />);
    await screen.findByRole("button", {
      name: new RegExp(fixture.report.objective),
    });
    fireEvent.click(
      screen.getByRole("button", {
        name: new RegExp(fixture.report.objective),
      }),
    );
    await screen.findByText("Run complete");
    await waitFor(() =>
      expect(document.querySelectorAll(".event-list .event")).toHaveLength(
        fixture.events.length,
      ),
    );
    expect(document.querySelector(".event-list")?.textContent).toContain(
      fixture.artifacts[0].artifact_id,
    );
    fireEvent.click(screen.getByRole("button", { name: /Refresh/ }));
    await waitFor(() =>
      expect(
        screen
          .getByRole("button", { name: /Refresh/ })
          .getAttribute("aria-busy"),
      ).toBe("false"),
    );
  });

  it("opens a mobile native dialog, closes with Escape, and restores focus", async () => {
    vi.mocked(window.matchMedia).mockImplementation(
      (query) =>
        ({
          matches: true,
          media: query,
          addEventListener: vi.fn(),
          removeEventListener: vi.fn(),
        }) as unknown as MediaQueryList,
    );
    navigation.pathname = "/experiment-studio";
    render(<ResearchWorkspace section="experiment-studio" />);
    await screen.findByRole("link", {
      name: /Account settings for Fixture Researcher/,
    });
    const trigger = screen.getByRole("button", {
      name: "Open navigation menu",
    });
    fireEvent.click(trigger);
    expect(
      screen.getByRole("dialog", { name: "Primary navigation" }),
    ).toBeTruthy();
    expect(document.body.style.overflow).toBe("hidden");
    fireEvent.keyDown(document, { key: "Escape" });
    expect(
      screen.queryByRole("dialog", { name: "Primary navigation" }),
    ).toBeNull();
    expect(document.activeElement).toBe(trigger);
    expect(document.body.style.overflow).toBe("");
  });

  it("shows a recoverable dataset error without displaying fabricated profile values", async () => {
    const original = fetch;
    vi.stubGlobal(
      "fetch",
      vi.fn((input, init) =>
        String(input).endsWith("/profile")
          ? Promise.resolve(reply({ detail: "Fixture API unavailable" }, 503))
          : original(input, init),
      ),
    );
    navigation.pathname = "/data-library";
    render(<ResearchWorkspace section="data-library" />);
    expect(await screen.findByRole("alert")).toBeTruthy();
    expect(screen.getByText("Fixture API unavailable")).toBeTruthy();
    expect(screen.queryByText("864")).toBeNull();
    expect(
      screen.getByRole("button", { name: /Try again|Retry|Reload/ }),
    ).toBeTruthy();
  });
});
