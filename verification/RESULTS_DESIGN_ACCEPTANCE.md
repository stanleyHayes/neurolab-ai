# Results presentation acceptance — 2026-10-27

## Delivered surface

The existing evidence renderer now uses a four-measure summary, a primary observed-contrast panel, a confidence-interval graphic with exact printed bounds, and separate method/interpretation panels. Custom decorative SVG icons use consistent strokes. The genotype table initially shows eight rows and expands to every persisted row. Source lineage and original-artifact exports remain available. The layout follows the existing dark green, cream and gold identity.

All values come from saved tool artifacts. Missing intervals produce an explicit unavailable message. Inconsistent source hashes withhold comparisons. Ranking uncertainty is explicitly unestimated; trait/environment pages disclose when their requested scientific analyses are absent. Presentation changes do not add scientific methods or causal claims.

## Actual browser evidence

Used the running local production frontend on port 3107 and isolated API on 8107, signed into the local review account. Reviewed saved deterministic run `7eaec595-e0ee-461b-a13b-baaca37a6324` with three actual Ghana analysis artifacts. The displayed means were 1,230.3 and 2,616 kg/ha, descriptive retention 47%, and 72 summarized genotypes. The contrast and its interval remained tied to the persisted artifact.

Desktop screenshots were visually inspected at the existing 1452px viewport. Expanded the table: DOM contained all 72 data rows. Collapsed it: eight data rows. At 390×844, visually inspected the summary and interpretation/table sections; document width and viewport width were both 390px. The wider table scrolls inside its container. Restored normal viewport after testing. Screenshots were actual browser captures, not generated mockups.

## Automated evidence and limits

`make quality` passed: Ruff, ESLint, TypeScript, 61 Python tests, eight proxy tests, 41 UI tests, source integrity audit, Python compilation and Next.js production build. Six added UI cases cover saved estimates/units, complete table expansion/order, original exports/lineage, mismatched source withholding, missing intervals and partial reports. Renderer tests do not constitute GPU or screen-reader acceptance.

The owner's full scientific objective, missing trait/stability methods, live Meta quality acceptance and production operational gates remain separate unfinished work. This is a results presentation milestone.

Final SonarQube analysis at 17:08 UTC passed the unchanged quality gate: zero open issues, 81.4% new-code coverage and 0.21686% duplicated new lines. Three initial presentation findings were fixed before the successful scan; no rules or thresholds were relaxed. Lint, TypeScript, all 41 UI tests and the production build passed again after those small fixes.
