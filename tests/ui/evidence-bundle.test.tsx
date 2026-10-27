import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { expect, it, vi } from "vitest";
import { EvidenceBundleButton } from "../../app/workspace/EvidenceBundleButton";
import { authenticatedFetch } from "../../app/auth-client";
vi.mock("../../app/auth-client", () => ({ authenticatedFetch: vi.fn() }));

it("downloads the authenticated saved evidence without running new tools", async () => {
  const bundle = { bundle_version: "neurolab-evidence-v1", artifacts: [] };
  vi.mocked(authenticatedFetch).mockResolvedValueOnce(
    new Response(JSON.stringify(bundle)),
  );
  const download = vi.fn();
  render(<EvidenceBundleButton runId="saved-run" downloadFile={download} />);
  fireEvent.click(screen.getByRole("button"));
  await waitFor(() =>
    expect(download).toHaveBeenCalledWith(
      "neurolab-saved-run-evidence.json",
      bundle,
      "application/json",
    ),
  );
  expect(authenticatedFetch).toHaveBeenCalledWith(
    "/api/research-runs/saved-run/bundle",
  );
});

it("retains saved evidence and permits retry when export fails", async () => {
  vi.mocked(authenticatedFetch).mockRejectedValueOnce(new Error("offline"));
  const download = vi.fn();
  render(<EvidenceBundleButton runId="saved-run" downloadFile={download} />);
  fireEvent.click(screen.getByRole("button"));
  expect((await screen.findByRole("alert")).textContent).toContain(
    "Your saved evidence is kept",
  );
  expect(download).not.toHaveBeenCalled();
  expect(screen.getByRole("button").hasAttribute("disabled")).toBe(false);
});
