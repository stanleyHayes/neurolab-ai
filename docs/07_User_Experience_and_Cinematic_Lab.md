# 07 — Cinematic scientific laboratory design

## Visual language
Dark research-console aesthetic with restrained gold/cyan accents, glass panels, precise typography, strong chart contrast, accessible light mode and reduced-motion mode. Three.js maize visualization optional and illustrative; never imply it reflects measured plant geometry unless grounded in source.

## Screens
Landing mission -> dataset provenance -> hypothesis workbench -> live execution timeline -> evidence comparison -> genotype explorer -> uncertainty / limitations -> reproducible report -> presenter mode.

## Animation contract
Every state transition originates from backend SSE. Use Motion for component enter/exit, GSAP for orchestrated sequences, Three.js/R3F for illustrative crop scene, D3/Plotly for real charts. Animations must never imply new computations when replaying cached results; display 'Replay' prominently.

## High-value visuals
Drought vs control distributions; paired/stratified genotype dot plots; uncertainty whiskers; year-by-genotype heatmap; trait correlation with caveats; provenance panel showing source DOI, license, hash and actual tool call; timeline of agent decisions; model provider badge.

## Interaction and accessibility
Keyboard support, semantic controls, color-independent encoding, text alternatives, focus management, reduced motion, no critical insight hidden in 3D. Presentation mode optimized for 1080p screen recording. Degrade gracefully without WebGL or paid inference.

## Demo safety
Never fabricate a successful run to make animation impressive. A seeded replay of a previously *real* completed run is permitted only if explicitly labeled. Keep source and uncertainty visible during 'discovery'.
