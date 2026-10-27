# Implementation plans

| # | Plan | Severity | Status |
| --- | --- | --- | --- |
| 001 | [Add Coordinated Workspace Motion](001-coordinated-workspace-motion.md) | MEDIUM | IN PROGRESS |

| 002 | [Finish the authoritative research prototype](002-project-completion.md) | P0 | ACTIVE GOAL |

## Recommended execution order

1. Complete the backend, science, safety and evidence gates in **002** before optional motion polish.
2. Execute **001 — Add Coordinated Workspace Motion**. It is a single cohesive pass over the shared sidebar and route workspace and covers the prerequisites (motion tokens and reduced-motion behavior) alongside group, layout, route, and content transitions.

## Dependencies

- Plan 001 has no plan dependencies. Its implementation depends on the existing grouped sidebar and 12-route workspace structure remaining in place.
- Browser/keyboard acceptance is a completion gate. If Playwright/Puppeteer are unavailable, perform and record manual checks; do not state automated browser acceptance passed.