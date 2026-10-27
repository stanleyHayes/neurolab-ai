import { useState } from "react";
import {
  act,
  fireEvent,
  render,
  screen,
  waitFor,
} from "@testing-library/react";
import { beforeEach, expect, it, vi } from "vitest";
import { ExperimentSetup } from "../../app/workspace/ExperimentSetup";
import { defaultConfiguration } from "../../app/workspace/research-editor-types";
import type {
  DraftResponse,
  ResearchPlan,
} from "../../app/workspace/research-editor-types";
import { setAccessToken } from "../../app/auth-client";

const run = vi.fn(async () => undefined);
const cancel = vi.fn(async () => undefined);
function EditorHarness() {
  const [objective, setObjective] = useState("Initial objective");
  return (
    <ExperimentSetup
      objective={objective}
      setObjective={setObjective}
      mode="replay"
      setMode={vi.fn()}
      busy={false}
      canceling={false}
      runId=""
      runStatus=""
      runAnalysis={run}
      cancelRun={cancel}
    />
  );
}
const proposal: ResearchPlan = {
  objective_sha256: "a".repeat(64),
  planning_mode: "meta",
  title: "Proposed title",
  refined_objective: "Proposed clearer objective",
  important_constraints: ["No causal inference"],
  ambiguities: ["Calendar years are not documented"],
  research_questions: ["How do observed yields differ?"],
  hypotheses: ["Proposed yield contrast hypothesis"],
  dataset_suggestions: [
    {
      dataset_id: "ghana_combined",
      rationale: "Enabled real trial",
      enabled_for_analysis: true,
    },
  ],
  analysis_approaches: [
    { method_id: "dataset_profile", rationale: "Inspect source first" },
  ],
  desired_outputs: ["research_report"],
  tasks: [
    {
      task_id: "t1",
      title: "Profile source",
      description: "Read the immutable source",
      tool_name: "dataset_profile",
      status: "pending",
      evidence_ids: [],
    },
  ],
  unsupported_requirements: ["Confirmatory agronomic recommendation"],
};
let stored: DraftResponse;
beforeEach(() => {
  run.mockClear();
  setAccessToken("editor-test-fixture");
  stored = {
    revision: 0,
    draft: { ...defaultConfiguration(), objective: "", accepted_plan: null },
    updated_at: null,
  };
  vi.stubGlobal(
    "fetch",
    vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
      if (String(input).endsWith("/research-capabilities"))
        return Response.json({
          model_inference_enabled: true,
          inference_message: "Fixture model available",
        });
      if (String(input).endsWith("/refine")) {
        const request = JSON.parse(String(init?.body));
        return Response.json({
          original_objective: request.objective,
          plan: proposal,
        });
      }
      if (init?.method === "PUT") {
        const request = JSON.parse(String(init.body));
        if (request.expected_revision !== stored.revision)
          return Response.json(
            {
              detail: "Draft changed in another session. Reload before saving.",
            },
            { status: 409 },
          );
        stored = {
          revision: stored.revision + 1,
          draft: request.draft,
          updated_at: "2026-10-27T00:00:00Z",
        };
      }
      return Response.json(stored);
    }),
  );
});

it.each([40, 5000, 20000])(
  "saves and restores %i characters without trimming Markdown or paragraphs",
  async (size) => {
    const view = render(<EditorHarness />);
    await waitFor(() =>
      expect(
        screen
          .getByRole("button", { name: "Load saved draft" })
          .getAttribute("aria-busy"),
      ).toBe("false"),
    );
    const base = "# Study\n\nPreserve **Markdown**, λ and paragraphs.\n";
    const original = base.repeat(Math.ceil(size / base.length)).slice(0, size);
    fireEvent.change(screen.getByLabelText("Research question"), {
      target: { value: original },
    });
    fireEvent.click(screen.getByRole("button", { name: "Save draft" }));
    await screen.findByText(
      "Draft saved to your account. You can resume after a refresh.",
    );
    expect(stored.draft.objective).toBe(original);
    view.unmount();
    render(<EditorHarness />);
    await screen.findByText(
      "Saved draft restored from your account. Original formatting is preserved.",
    );
    expect(
      (screen.getByLabelText("Research question") as HTMLTextAreaElement).value,
    ).toBe(original);
    fireEvent.click(
      screen.getByRole("button", { name: /Generate experiment plan/ }),
    );
    expect(run).toHaveBeenCalledWith(defaultConfiguration(), null);
  },
);

it("keeps oversized Unicode text and blocks execution instead of silently cutting it", async () => {
  render(<EditorHarness />);
  const original = "🌽".repeat(20001);
  fireEvent.change(screen.getByLabelText("Research question"), {
    target: { value: original },
  });
  expect(
    (screen.getByLabelText("Research question") as HTMLTextAreaElement).value,
  ).toBe(original);
  expect(screen.getByText("20,001 / 20,000 characters")).toBeTruthy();
  expect(
    (
      screen.getByRole("button", {
        name: /Generate experiment plan/,
      }) as HTMLButtonElement
    ).disabled,
  ).toBe(true);
  fireEvent.change(screen.getByLabelText("Research question"), {
    target: { value: "🌽".repeat(20000) },
  });
  expect(
    (
      screen.getByRole("button", {
        name: /Generate experiment plan/,
      }) as HTMLButtonElement
    ).disabled,
  ).toBe(false);
});

it("expands writing, preserves text and restores the trigger focus", async () => {
  render(<EditorHarness />);
  const trigger = screen.getByRole("button", {
    name: "Expand writing space ↗",
  });
  fireEvent.click(trigger);
  expect(
    screen.getByRole("dialog", {
      name: "Keep the full investigation in view.",
    }),
  ).toBeTruthy();
  fireEvent.change(
    screen.getByLabelText("Complete original research objective"),
    { target: { value: "Expanded\n\nwriting" } },
  );
  fireEvent.click(screen.getByRole("button", { name: "Close writing space" }));
  expect(
    (screen.getByLabelText("Research question") as HTMLTextAreaElement).value,
  ).toBe("Expanded\n\nwriting");
  expect(document.activeElement).toBe(trigger);
});

it("reviews and edits Meta proposals without overwriting the original objective", async () => {
  render(<EditorHarness />);
  const original = "Original\n<script data-fixture>unsafe()</script>";
  fireEvent.change(screen.getByLabelText("Research question"), {
    target: { value: original },
  });
  await waitFor(() =>
    expect(
      (
        screen.getByRole("button", {
          name: "Refine Research Objective",
        }) as HTMLButtonElement
      ).disabled,
    ).toBe(false),
  );
  fireEvent.click(
    screen.getByRole("button", { name: "Refine Research Objective" }),
  );
  await screen.findByRole("heading", { name: "Review the research plan" });
  expect(document.querySelector("script[data-fixture]")).toBeNull();
  expect(
    (screen.getByLabelText("Research question") as HTMLTextAreaElement).value,
  ).toBe(original);
  fireEvent.change(
    screen.getByLabelText("Proposed refined objective · editable"),
    { target: { value: "Edited refinement" } },
  );
  fireEvent.click(screen.getByRole("button", { name: "Accept research plan" }));
  await screen.findByText(
    "Research plan accepted. The original objective was not changed. Save the draft to retain this plan.",
  );
  expect(
    (screen.getByLabelText("Research question") as HTMLTextAreaElement).value,
  ).toBe(original);
  fireEvent.click(
    screen.getByRole("button", { name: /Generate experiment plan/ }),
  );
  expect(run).toHaveBeenCalledWith(
    expect.objectContaining({ title: "Proposed title" }),
    expect.objectContaining({ refined_objective: "Edited refinement" }),
  );
});

it("rejects stale writes and leaves the local objective untouched", async () => {
  render(<EditorHarness />);
  await waitFor(() =>
    expect(
      screen
        .getByRole("button", { name: "Load saved draft" })
        .getAttribute("aria-busy"),
    ).toBe("false"),
  );
  stored = {
    ...stored,
    revision: 1,
    draft: { ...stored.draft, objective: "Other session" },
  };
  fireEvent.change(screen.getByLabelText("Research question"), {
    target: { value: "My unsaved writing" },
  });
  fireEvent.click(screen.getByRole("button", { name: "Save draft" }));
  expect((await screen.findByRole("alert")).textContent).toContain(
    "Draft changed in another session. Reload before saving.",
  );
  expect(
    (screen.getByLabelText("Research question") as HTMLTextAreaElement).value,
  ).toBe("My unsaved writing");
  expect(stored.draft.objective).toBe("Other session");
});

it("does not mark edits made during an in-flight save as saved", async () => {
  const originalFetch = fetch;
  let release: ((response: Response) => void) | undefined;
  vi.stubGlobal(
    "fetch",
    vi.fn((input: RequestInfo | URL, init?: RequestInit) => {
      if (init?.method === "PUT")
        return new Promise<Response>((resolve) => {
          release = resolve;
        });
      return originalFetch(input, init);
    }),
  );
  render(<EditorHarness />);
  await waitFor(() =>
    expect(
      screen
        .getByRole("button", { name: "Load saved draft" })
        .getAttribute("aria-busy"),
    ).toBe("false"),
  );
  fireEvent.click(screen.getByRole("button", { name: "Save draft" }));
  fireEvent.change(screen.getByLabelText("Research question"), {
    target: { value: "Newer writing" },
  });
  await act(async () =>
    release?.(
      Response.json({ revision: 1, draft: stored.draft, updated_at: null }),
    ),
  );
  expect(
    await screen.findByText(
      "Earlier draft saved. Your newer writing is kept and still has unsaved changes.",
    ),
  ).toBeTruthy();
  expect(
    (screen.getByLabelText("Research question") as HTMLTextAreaElement).value,
  ).toBe("Newer writing");
});

it("keeps optional configuration editable without losing newlines and sends bounded preferences", async () => {
  render(<EditorHarness />);
  fireEvent.click(screen.getByText(/Optional research configuration/));
  fireEvent.change(screen.getByLabelText("Research title"), {
    target: { value: "My trial investigation" },
  });
  const questions = screen.getByLabelText(
    "Research questions · one per line, up to 20",
  ) as HTMLTextAreaElement;
  fireEvent.change(questions, { target: { value: "Question one\n" } });
  expect(questions.value).toBe("Question one\n");
  fireEvent.change(questions, {
    target: { value: "Question one\nQuestion two" },
  });
  fireEvent.change(
    screen.getByLabelText("Proposed hypotheses · one per line, not results"),
    { target: { value: "Hypothesis one\nHypothesis two" } },
  );
  fireEvent.click(screen.getByRole("button", { name: /Dataset profile/ }));
  fireEvent.click(screen.getByRole("button", { name: "research report" }));
  fireEvent.change(screen.getByLabelText(/Analysis steps/), {
    target: { value: "0" },
  });
  expect(
    screen.getByText("Analysis steps must be an integer from 1 to 6."),
  ).toBeTruthy();
  fireEvent.change(screen.getByLabelText(/Analysis steps/), {
    target: { value: "6" },
  });
  fireEvent.change(screen.getByLabelText(/Tool calls/), {
    target: { value: "6" },
  });
  fireEvent.change(screen.getByLabelText(/Seconds/), {
    target: { value: "180" },
  });
  fireEvent.click(
    screen.getByRole("button", { name: /Execute supported analyses/ }),
  );
  fireEvent.click(
    screen.getByRole("button", {
      name: /Stop when a requested operation is unsupported/,
    }),
  );
  fireEvent.click(
    screen.getByRole("button", { name: /Generate experiment plan/ }),
  );
  expect(run).toHaveBeenCalledWith(
    expect.objectContaining({
      title: "My trial investigation",
      research_questions: ["Question one", "Question two"],
      hypotheses: ["Hypothesis one", "Hypothesis two"],
      preferred_methods: ["dataset_profile"],
      desired_outputs: ["research_report"],
      constraints: { max_steps: 6, max_tool_calls: 6, max_seconds: 180 },
      autonomy_preferences: {
        auto_plan_with_meta: true,
        execute_supported_tasks: false,
        stop_if_unsupported: true,
      },
    }),
    null,
  );
});

it("lets the researcher reject a proposal or invalidate it by changing the original", async () => {
  render(<EditorHarness />);
  await waitFor(() =>
    expect(
      (
        screen.getByRole("button", {
          name: "Refine Research Objective",
        }) as HTMLButtonElement
      ).disabled,
    ).toBe(false),
  );
  fireEvent.click(
    screen.getByRole("button", { name: "Refine Research Objective" }),
  );
  await screen.findByRole("heading", { name: "Review the research plan" });
  fireEvent.click(screen.getByRole("button", { name: "Reject proposal" }));
  expect(
    (screen.getByLabelText("Research question") as HTMLTextAreaElement).value,
  ).toBe("Initial objective");
  expect(
    screen.queryByRole("heading", { name: "Review the research plan" }),
  ).toBeNull();
  await waitFor(() =>
    expect(
      (
        screen.getByRole("button", {
          name: "Refine Research Objective",
        }) as HTMLButtonElement
      ).disabled,
    ).toBe(false),
  );
  fireEvent.click(
    screen.getByRole("button", { name: "Refine Research Objective" }),
  );
  await screen.findByRole("heading", { name: "Review the research plan" });
  fireEvent.change(screen.getByLabelText("Research question"), {
    target: { value: "Changed original" },
  });
  expect(
    (
      screen.getByRole("button", {
        name: "Accept research plan",
      }) as HTMLButtonElement
    ).disabled,
  ).toBe(true);
});

it("shows paused inference clearly, prevents Meta selection/refinement, and still permits deterministic analysis", async () => {
  const originalFetch = fetch;
  vi.stubGlobal(
    "fetch",
    vi.fn((input: RequestInfo | URL, init?: RequestInit) => {
      if (String(input).endsWith("/research-capabilities"))
        return Promise.resolve(
          Response.json({
            model_inference_enabled: false,
            inference_message: "Meta is paused. Saved replay uses no credits.",
          }),
        );
      return originalFetch(input, init);
    }),
  );
  render(<EditorHarness />);
  await screen.findByText("Meta is paused. Saved replay uses no credits.");
  expect(
    (
      screen.getByRole("button", {
        name: /Meta-assisted research/,
      }) as HTMLButtonElement
    ).disabled,
  ).toBe(true);
  expect(
    (
      screen.getByRole("button", {
        name: "Refine Research Objective",
      }) as HTMLButtonElement
    ).disabled,
  ).toBe(true);
  fireEvent.click(
    screen.getByRole("button", { name: "Generate experiment plan" }),
  );
  expect(run).toHaveBeenCalledOnce();
});

it("explains unavailable draft storage without replacing the original writing or claiming it is empty", async () => {
  const originalFetch = fetch;
  vi.stubGlobal(
    "fetch",
    vi.fn((input: RequestInfo | URL, init?: RequestInit) => {
      if (String(input).endsWith("/research-draft"))
        return Promise.resolve(
          Response.json({ detail: "Not Found" }, { status: 404 }),
        );
      return originalFetch(input, init);
    }),
  );
  render(<EditorHarness />);
  expect((await screen.findByRole("alert")).textContent).toContain(
    "Account draft storage is temporarily unavailable",
  );
  expect(
    (screen.getByLabelText("Research question") as HTMLTextAreaElement).value,
  ).toBe("Initial objective");
});
