# Portable scientific report and figures

The Reports view offers **Export evidence & figures data**. This authenticated read downloads the selected terminal run's persisted report, all numeric artifacts and saved events. The service rechecks ownership; other users and legacy unowned records receive 404. No owner/session records, credentials or new model calls are part of the bundle. Failed/partial terminal runs can be exported for auditing, but the figure exporter below requires a complete, consistent six-tool investigation.

Install the optional plotting environment and render a downloaded bundle:

```sh
python3 -m pip install -r requirements-figures.txt
python3 -m scripts.export_investigation --bundle saved-evidence.json --output maize-report
```

Use a new output directory; existing exports are preserved. The API's ordinary requirements do not install Matplotlib. Development requirements include plotting dependencies for export tests.

Outputs:

- `report.html`: self-contained, offline ten-section scientific report, including four embedded PNG figures, criteria/counterevidence, candidate trade-offs, scientific limits, proposed next experiments and reproducibility. Open locally in a browser; it contains no scripts, remote fonts or remote image requests. Source text is escaped; a restrictive content security policy further limits active content. Printing can produce a PDF through the browser, but no PDF rendering acceptance is claimed here.
- Four PNG/SVG figure pairs: observed regime means and conditional block-bootstrap contrast interval; five leading drought means compared with separately summarized well-watered means; seven trait–yield Spearman correlations overall and within observed drought environments; observed environment profiles of those same five candidates.
- `figure-data.json`: full unrounded plotting data, conditional correlation intervals, excluded counts and profile lineage. This file is the accessible numerical counterpart of the figures.
- `evidence.json`: the input bundle preserved byte-for-byte. Its SHA-256 is recorded in the report.

The exporter validates the result schema, six distinct tools, source agreement, artifact/report ID agreement, saved tool completion events and same-run event ownership. It rebuilds the scientific report from those artifacts and rejects a changed or inconsistent report. These checks establish internal consistency, not a digital signature or independent authentication of third-party evidence. Export only bundles obtained from a trusted service; no scientific validity claim follows from a successful export.

The exporter performs presentation only: no inference, new resampling, dataset join, source mutation or new scientific calculation. Plot values come from saved artifacts. Regimes remain confounded with environment; environment indices are not years. Candidate selection is retrospective; bars/connected environment means are not prediction bands. Stay-green score direction remains unverified. Numeric trait intervals are conditional and unadjusted for multiple screening. Future field designs remain proposals, not executed experiments.

## Actual recorded case

`verification/maize-investigation/` was generated from authenticated saved run `971d3426-4768-4784-bb0d-a665bdb0b007`: the exact supplied objective, six completed tools, six artifacts, 57 API lifecycle events, canonical source hash `2e37c07f30e00efb33b59954dd6d02a04f3d67349790d782b70dbedfdaff05bc`, loaded science code commit `62ff746`. The original recorded startup byte hashes remain intact; the exporter does not relabel the scientific run as having executed under a later presentation commit. All four actual PNGs were visually inspected locally for labels, legend/caption legibility and observed values. This is figure inspection, not app/browser screenshot acceptance. No live Meta call occurred.
