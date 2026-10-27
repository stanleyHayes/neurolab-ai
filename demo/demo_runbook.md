# Demo operator runbook

1. **Current implementation is replay-only.** Do not present it as Meta inference. For a genuine Meta demo, first configure a real provider adapter and credentials, and pass a real smoke call; until then do not record the Meta-dependent submission demo.
2. Verify service health at `/health`; it must explicitly report `model_inference_live: false` for the current replay-only build.
3. Open the dashboard at `/`; show Ghana provenance, DOI and source hash.
4. Start a fresh deterministic replay run; keep the “no model call” label visible.
5. Show the evidence-linked decisions, uncertainty interval, warnings and report; verify the persisted run can be reopened from the API.
6. If an analysis tool fails, disclose `partial` completion and identify the failed analysis; profile recovery is not a substitute for the missing result.
7. Record no more than 180 seconds only if this replay-only product is useful as a clearly disclosed prototype. It cannot be submitted as proof of the live Meta-powered experience.
8. Before any actual submission, cross-check public repository, live product, and video links in a private browser window.
