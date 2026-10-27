# 001 — Add Coordinated Workspace Motion

- **Status**: IN PROGRESS — page-entry motion implemented; navigation/sidebar motion remains
- **Commit**: unavailable — `/Users/shayford/Desktop/Dev/Projects/neurodyne-ai` has no `.git` directory
- **Severity**: MEDIUM
- **Category**: Easing & duration; Accessibility; Missed opportunities
- **Estimated scope**: 2 source files plus `BUILD_LOG.md`; moderate CSS and small React markup changes

## Progress note (2026-10-26)

Implemented the route-keyed page-content entrance and coordinated stagger in `app/research-workspace.tsx` and `app/globals.css`. The content boundary remounts only when the route section changes; the 220ms opacity/8px reveal is limited to top-level page blocks and disabled by the existing reduced-motion rule. The spacing cleanup also normalizes shared page and section rhythm. Remaining items in this broader plan (animated nav-group expansion/collapse and sidebar layout easing) have not been implemented or browser-accepted; keep this plan IN PROGRESS until the remaining interaction work and acceptance checks are complete.

## Problem

The current UI uses CSS transitions, with no motion library or shared motion tokens. The sidebar width changes over `.22s ease`, which reflows the main column using a generic easing. Group children are hidden immediately using the `hidden` attribute and `display: none`, so the chevron rotates but the links do not animate. Route changes replace the shared `<main>` content without an entry transition, and the major content blocks have no coordinated reveal. Reduced motion currently disables every transition and animation, including non-spatial control feedback.

The app is a restrained, dark scientific dashboard; use concise, non-bouncy motion. Animation is presentation only. Do not suggest that a research run, evidence computation, or scientific discovery has occurred unless actual persisted application state says so.

Current implementation excerpts:

```css
/* /Users/shayford/Desktop/Dev/Projects/neurodyne-ai/app/globals.css:83 */
.sidebar { position: sticky; z-index: 9; top: 0; display: flex; width: 254px; height: 100vh; flex: 0 0 254px; flex-direction: column; overflow: hidden; padding: 18px 12px 14px; border-right: 1px solid #294147; background: linear-gradient(180deg, #07161b, #061116); transition: width .22s ease, flex-basis .22s ease; }
```

```css
/* /Users/shayford/Desktop/Dev/Projects/neurodyne-ai/app/globals.css:102-107 */
.nav-group-chevron { width: 15px; flex: 0 0 15px; color: #779693; font-size: 16px; text-align: center; transition: transform .16s ease; }
.nav-group-collapsed .nav-group-chevron { transform: rotate(-90deg); }
.nav-group-children { position: relative; display: grid; gap: 2px; margin: 3px 0 1px 20px; padding: 2px 0 3px 14px; border-left: 1px solid #31534f; }
.nav-group-children[hidden] { display: none; }
.app-shell .nav-group-collapsed > .nav-group-children { display: none; }
.nav-child-link { position: relative; display: flex; min-height: 34px; gap: 9px; align-items: center; padding: 5px 8px; border: 1px solid transparent; border-radius: 7px; color: #9ab1b0; font-size: 12px; text-decoration: none; transition: background-color .16s ease, border-color .16s ease, color .16s ease; }
```

```tsx
/* /Users/shayford/Desktop/Dev/Projects/neurodyne-ai/app/research-workspace.tsx:539-555 */
<section className={`nav-group${isActive ? " nav-group-active" : ""}${isCollapsed ? " nav-group-collapsed" : ""}`} key={group.id}>
  <button
    className="nav-group-toggle"
    type="button"
    aria-expanded={!isCollapsed}
    aria-controls={groupPanelId}
    aria-label={`${isCollapsed ? "Expand" : "Collapse"} ${group.label}`}
    title={group.label}
    onClick={() => toggleNavGroup(group.id)}
  >
    {/* group label and icon */}
  </button>
  <div className="nav-group-children" id={groupPanelId} hidden={isCollapsed}>
    {/* route links */}
  </div>
</section>
```

```tsx
/* /Users/shayford/Desktop/Dev/Projects/neurodyne-ai/app/research-workspace.tsx:587-590 */
<main id="main" className={`page-content${showOverview ? " overview-page" : " detail-page"}`}>
  {error && <div className="notice error-notice" role="alert">{/* ... */}</div>}
  {!showOverview && <section className="page-title-block">{/* ... */}</section>}
  {showOverview && <>{/* overview sections */}</>}
```

```css
/* /Users/shayford/Desktop/Dev/Projects/neurodyne-ai/app/globals.css:741-749 */
@media (prefers-reduced-motion: reduce) {
  *,
  *::before,
  *::after {
    scroll-behavior: auto !important;
    animation: none !important;
    transition: none !important;
  }
}
```

## Target

Implement all of the following in the two active source files named below, without adding an animation dependency:

1. **Shared tokens.** Add these exact CSS custom properties to the existing `:root` in `/Users/shayford/Desktop/Dev/Projects/neurodyne-ai/app/globals.css`:

   ```css
   --motion-ease-out: cubic-bezier(0.23, 1, 0.32, 1);
   --motion-ease-in-out: cubic-bezier(0.77, 0, 0.175, 1);
   --motion-duration-control: 160ms;
   --motion-duration-panel: 200ms;
   --motion-duration-layout: 260ms;
   --motion-duration-enter: 220ms;
   --motion-stagger: 40ms;
   ```

   The curves and duration budgets come from `/Users/shayford/.agents/skills/improve-animations/AUDIT.md`: use ease-out for entry, ease-in-out for spatial movement, and keep UI movement below 300 ms. Use only the tokens above for new motion timing; do not create near-duplicate curves or durations.

2. **Group expansion/collapse.** Replace the immediate `hidden`/`display:none` path for group children with an animatable panel wrapper and inner clipping wrapper in `/Users/shayford/Desktop/Dev/Projects/neurodyne-ai/app/research-workspace.tsx`. Animate the panel from zero to its natural content height with a CSS grid-row transition (closed `grid-template-rows: 0fr`, open `grid-template-rows: 1fr`) and opacity from 0 to 1 over `var(--motion-duration-panel)` using `var(--motion-ease-out)`; the inner wrapper must clip overflow during the transition. Keep the panel in the DOM while it closes so the transition can finish. Set `inert` and `aria-hidden` immediately when closed so invisible child links cannot receive focus or be exposed as available navigation; preserve the existing toggle `aria-expanded` and `aria-controls` contract. Do not use a fixed `max-height` cap, `scale(0)`, or a one-shot keyframe that restarts when users toggle rapidly. Animate the chevron with the panel state using `var(--motion-duration-control)` and `var(--motion-ease-in-out)`.

   Preserve all current desktop icon-rail and mobile horizontal-navigation behavior. In the collapsed mobile rule, the actual child-link row must remain horizontally laid out and scrollable; animate its containing panel without clipping the horizontal scrolling area or the existing focus/hover labels. Confirm the responsive selectors in the source before editing them.

3. **Sidebar/layout resize.** Replace the hard-coded `.22s ease` transition on `.sidebar` with `var(--motion-duration-layout) var(--motion-ease-in-out)` for the existing `width` and `flex-basis` properties. Keep width values and breakpoints unchanged. This deliberate geometric transition will reflow the content column; do not add transitions to every grid, margin, or padding property. Verify the 254px-to-74px desktop resize at 260 ms does not visibly lag or cause text/content to overlap, and confirm mobile rules still win over desktop width values.

4. **Route/page entry.** Give the route-specific content a stable keyed entry boundary using the existing `section` prop in `/Users/shayford/Desktop/Dev/Projects/neurodyne-ai/app/research-workspace.tsx`, so navigation between the 12 workspace routes reliably starts a new entry without animating unrelated run-state refreshes. On entry, animate opacity from 0 to 1 and `transform: translateY(8px)` to `transform: translateY(0)` over `var(--motion-duration-enter)` with `var(--motion-ease-out)`. Use CSS transitions/native `@starting-style` or an equivalent small CSS-only mounted-state technique compatible with the app's existing React structure; do not install Motion/Framer Motion. Avoid animating layout dimensions, blur, or a large vertical offset. Preserve the main landmark and its `id="main"`, heading, links, and keyboard focus behavior.

5. **Content entrances.** On route entry, reveal the page title and major, initially rendered overview sections, workspace cards, report strip, and grounded report with opacity plus a subtle `translateY(8px)` entrance. Add a `40ms` stagger per sibling, capped at five steps (maximum added delay 160ms); use CSS `:nth-child()` rules or another deterministic CSS-only approach. Make entrances one-shot for a route mount, not replayed on each fetch, event, run-status, replay-index, or form-value update. Conditional panels that first appear after a user action or persisted data arrives may use the same brief entrance, but do not animate data as if it were being computed: never create fake progress, fabricated events, or synthetic values. Keep chart bars proportional to actual tool-derived results; if their actual widths transition, use the real rendered width only and confirm reduced motion disables that movement. Use `@starting-style` for conditionally mounted panels where supported or a CSS fallback that does not introduce animation libraries or extra timers.

6. **Reduced motion.** Retain an explicit `@media (prefers-reduced-motion: reduce)` rule in `/Users/shayford/Desktop/Dev/Projects/neurodyne-ai/app/globals.css`. In this mode, remove all positional transforms, panel size movement, stagger delays, and entrance animations; keep route/group states immediate and preserve readable state changes and focus indicators. Follow the active product specification at `/Users/shayford/Desktop/Dev/Projects/neurodyne-ai/docs/09_Cinematic_Scientific_Visualization_and_Interaction_Design.md:9,49`, which calls for immediate state transitions in reduced-motion mode. Ensure no timer or JS animation continues in reduced motion. Do not simply remove focus/active/selected styles.

## Repo conventions to follow

- Keep the app dependency-free for motion: `/Users/shayford/Desktop/Dev/Projects/neurodyne-ai/package.json` contains Next.js, React, and TypeScript, but no animation library.
- Global styling, responsive breakpoints, existing CSS transitions, and the reduced-motion media query live in `/Users/shayford/Desktop/Dev/Projects/neurodyne-ai/app/globals.css`.
- Shared interactive navigation and the existing `usePrefersReducedMotion()` hook live in `/Users/shayford/Desktop/Dev/Projects/neurodyne-ai/app/research-workspace.tsx`. Prefer CSS for the transitions; do not add another JS animation loop or timing state.
- Existing accessible group disclosure pattern is `.nav-group-toggle` with `aria-expanded`, `aria-controls`, a labelled button, and child `<Link>` elements. Preserve it.
- The responsive navigation is defined in `/Users/shayford/Desktop/Dev/Projects/neurodyne-ai/app/globals.css:654-691`; collapsed mobile children specifically use a horizontal flex row. Do not regress that layout.
- Project rules in `/Users/shayford/Desktop/Dev/Projects/neurodyne-ai/AGENTS.md` require truthful, persisted-data-driven visuals, tests before marking done, and an appended `BUILD_LOG.md` entry for each contribution.
- The current workspace has no Git metadata; do not claim a commit hash or fabricate one.

## Steps

1. In `/Users/shayford/Desktop/Dev/Projects/neurodyne-ai/app/globals.css`, add the motion tokens to the existing `:root`, then replace only the sidebar's hard-coded width/flex-basis easing and the navigation chevron timing with the exact tokens above.
2. In `/Users/shayford/Desktop/Dev/Projects/neurodyne-ai/app/research-workspace.tsx`, replace the group's `hidden` attribute with an animatable panel/inner-wrapper structure. Apply `inert` and `aria-hidden` to the closed panel while retaining `aria-expanded`/`aria-controls` on the button. Ensure React's `inert` attribute is expressed in the form supported by the installed React 19 TypeScript definitions.
3. In `/Users/shayford/Desktop/Dev/Projects/neurodyne-ai/app/globals.css`, implement the reversible grid-row/opacity transition and chevron rotation; preserve desktop collapsed icon-rail links and the mobile collapsed horizontal row. Remove the old `.nav-group-children[hidden]` and `.app-shell .nav-group-collapsed > .nav-group-children { display: none; }` rules once no longer used.
4. In `/Users/shayford/Desktop/Dev/Projects/neurodyne-ai/app/research-workspace.tsx`, add one route-keyed entrance boundary for page content. Preserve `<main id="main">`; make route changes trigger the entry once while existing run/data state updates do not remount that boundary.
5. In `/Users/shayford/Desktop/Dev/Projects/neurodyne-ai/app/globals.css`, add the entry and capped 40ms sibling stagger styles for major page sections/cards; use only opacity and a subtle 8px translate for entrance. For panels that mount after an actual state/data transition, use a brief entrance without fabricated progress or measurement animation.
6. Update reduced-motion selectors in `/Users/shayford/Desktop/Dev/Projects/neurodyne-ai/app/globals.css` to immediately remove spatial movement, entrance, panel animation, and stagger while retaining focus and state styling. Confirm the `usePrefersReducedMotion()` handling of presentation replay remains consistent; do not introduce duplicate or continuously running timers.
7. Run the mechanical checks below. Start the app and complete browser acceptance at desktop and mobile sizes; if Playwright/Puppeteer remain unavailable, perform and record manual keyboard and viewport checks instead of claiming automated browser coverage.
8. Append a dated entry to `/Users/shayford/Desktop/Dev/Projects/neurodyne-ai/BUILD_LOG.md` only after actual implementation and validation. Record exact commands and observed results; explicitly state whether browser acceptance was manual or automated and note any unverified checks. Do not change the external Meta credentials blocker in this task.

## Boundaries

- Do NOT add a dependency or introduce a second animation system.
- Do NOT animate scientific meaning, create synthetic data/events/progress, or describe an animation as a scientific result.
- Do NOT animate every DOM node. Limit entry motion to route content and major visible page blocks; avoid replaying entrances on frequent data refreshes.
- Do NOT change route structure, route labels, sidebar session persistence, navigation grouping, visual design tokens unrelated to motion, science/API behavior, or responsive breakpoints.
- Do NOT remove keyboard accessibility, visible focus, the main landmark, or the existing navigation disclosure semantics.
- Do NOT use `transition: all`, `scale(0)`, long UI durations above 300ms, heavy blur, a fixed-height clipping cap, or keyframe animations for rapidly reversible group toggles.
- Do NOT claim completion until tests and browser/keyboard acceptance have actual recorded evidence in `BUILD_LOG.md`.
- If the React panel markup, CSS selectors, or page composition have materially drifted from the excerpts in this plan, stop and report the drift rather than applying selectors blindly.

## Verification

- **Mechanical**: from `/Users/shayford/Desktop/Dev/Projects/neurodyne-ai`, run `npm run lint`, `npm run typecheck`, `npm run build`, `python -m unittest discover -s tests -v`, and `python scripts/audit_datasets.py`. Expected: all exit successfully; record actual test count/output and route build output in `/Users/shayford/Desktop/Dev/Projects/neurodyne-ai/BUILD_LOG.md`.
- **Feel check (desktop)**: at widths 1280px and 1024px, expand/collapse each sidebar group, rapidly reverse a toggle mid-transition, collapse/expand the sidebar, and navigate among Overview, Experiment Studio, Research Results, Live Experiment, Reports, and Settings. Confirm groups remain interruptible; sidebar content reflows without overlap; each route has one concise entry; focus remains visible; no stale old page visibly overlaps the new one.
- **Feel check (mobile)**: at widths 390px and 320px, verify expanded groups push content without clipping, the collapsed sidebar retains horizontally scrollable icon navigation and child-link behavior, labels remain available to keyboard/focus users, and no horizontal page overflow is introduced.
- **Keyboard/accessibility**: use only Tab, Shift+Tab, Enter, and Space to traverse and toggle all five groups. Confirm `aria-expanded` updates immediately, closed descendants cannot be tabbed into, focus is not lost when a group closes, `aria-controls` still points to the panel, and the active route remains announced as the current page.
- **Reduced motion**: emulate `prefers-reduced-motion: reduce` in browser DevTools and repeat route changes, group toggles, and sidebar collapse. Confirm no positional movement, stagger, or delayed entry remains; content and navigation update immediately; focus/selected styles still work.
- **Truth/performance check**: inspect an empty evidence route and a route with persisted artifacts; confirm animation shows only actual rendered content, no invented progress/events, and numeric chart widths still derive from tool results. In DevTools' Animations/performance tools, confirm no expensive blur, `transition: all`, or repeated page-entry animation during event/data refreshes.
- **Done when**: mechanical checks pass; all 12 routes remain reachable; desktop, mobile, keyboard, and reduced-motion acceptance are recorded with actual results; `BUILD_LOG.md` documents precisely what passed and what remains blocked.