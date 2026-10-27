import { createRef } from "react";
import { fireEvent, render, screen } from "@testing-library/react";
import { expect, it, vi } from "vitest";
import { WorkspaceHeader } from "../../app/workspace/WorkspaceHeader";

function props() {
  return {
    title: "Research results",
    providerLabel: "Deterministic replay · no model call",
    runId: "fixture-run",
    savedRuns: [
      {
        run_id: "fixture-run",
        objective: "Recorded Ghana objective",
        status: "COMPLETE",
        created_at: "2026-10-27",
        source_sha256: "fixture-source",
      },
    ],
    onSelectRun: vi.fn(),
    account: { display_name: "Fixture Researcher" },
    isOverview: false,
    sidebarCollapsed: false,
    setSidebarCollapsed: vi.fn(),
    mobileNavOpen: false,
    setMobileNavOpen: vi.fn(),
    mobileNavTriggerRef: createRef<HTMLButtonElement>(),
  };
}

it("dismisses the experiment picker with Escape and returns keyboard focus", () => {
  const { container } = render(<WorkspaceHeader {...props()} />);
  const picker = container.querySelector("details")!;
  const summary = picker.querySelector("summary")!;
  picker.open = true;
  screen.getByRole("button", { name: "Select experiment fixture-" }).focus();
  fireEvent.keyDown(document.activeElement!, { key: "ArrowDown" });
  expect(picker.open).toBe(true);
  fireEvent.keyDown(document.activeElement!, { key: "Escape" });
  expect(picker.open).toBe(false);
  expect(document.activeElement).toBe(summary);
});

it("dismisses on focus or pointer departure and selects an owned saved context", () => {
  const input = props();
  const { container } = render(<WorkspaceHeader {...input} />);
  const picker = container.querySelector("details")!;
  picker.open = true;
  fireEvent.click(
    screen.getByRole("button", { name: "Select experiment fixture-" }),
  );
  expect(input.onSelectRun).toHaveBeenCalledWith("fixture-run");
  expect(picker.open).toBe(false);
  picker.open = true;
  fireEvent.focusIn(screen.getByRole("link", { name: /Account settings/ }));
  expect(picker.open).toBe(false);
  picker.open = true;
  fireEvent.pointerDown(document.body);
  expect(picker.open).toBe(false);
});
