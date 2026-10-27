"use client";

import { useState } from "react";
import { authenticatedFetch } from "../auth-client";
import { ResultIcon } from "./ResultIcon";

export function EvidenceBundleButton({
  runId,
  downloadFile,
}: Readonly<{
  runId: string;
  downloadFile: (name: string, value: unknown, mime: string) => void;
}>) {
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  async function exportBundle() {
    setBusy(true);
    setError("");
    try {
      const response = await authenticatedFetch(
        `/api/research-runs/${encodeURIComponent(runId)}/bundle`,
      );
      if (!response.ok) throw new Error("Export unavailable");
      downloadFile(
        `neurolab-${runId}-evidence.json`,
        await response.json(),
        "application/json",
      );
    } catch {
      setError(
        "Could not export this run. Your saved evidence is kept. Try again.",
      );
    } finally {
      setBusy(false);
    }
  }
  return (
    <div>
      <button
        className="secondary-button"
        type="button"
        disabled={busy}
        onClick={() => void exportBundle()}
      >
        <ResultIcon name="download" />
        {busy ? "Preparing evidence…" : "Export evidence & figures data"}
      </button>
      {error && <p role="alert">{error}</p>}
    </div>
  );
}
