# 09 — Weather and crop-model extension (explicitly optional)

NASA POWER daily API can supply weather time series, but a weather series alone cannot identify genotype-specific irrigation response. For a valid AquaCrop-style simulation, acquire soil hydraulic parameters, planting dates, management, crop parameters and initial conditions; verify software licensing, API and calibration examples.

## Gate sequence
1. Source lawful weather and crop parameters; record attribution, spatial resolution, units and time basis (UTC vs LST).
2. Run unmodified model example; document version and license.
3. Calibrate to observed data only when corresponding soil/management/yield measurements exist.
4. Validate against held-out observations; report uncertainty and model domain.
5. Only then let Meta propose bounded irrigation schedules. Never pass genotype ID to a generic model as if calibrated to that genotype.

## Fallback
If no defensible calibration is available, omit irrigation optimization from the judged demo. Use **autonomous observational research** as P0 and say so clearly. A toy surrogate may be displayed only as 'illustrative synthetic simulation', separated from scientific results.
