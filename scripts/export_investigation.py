"""Export saved evidence to a portable HTML report and actual-data PNG/SVG figures.

Install requirements-figures.txt, then:
python -m scripts.export_investigation --bundle saved-evidence.json --output report-directory
No inference, source mutation, network access or new scientific analysis occurs.
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import html
import json
import math
import platform
import tempfile
from pathlib import Path

from jsonschema import validate

from neurolab.hypothesis_contracts import HypothesisTest
from neurolab.scientific_report import REQUIRED_TOOLS, build_scientific_report

ROOT = Path(__file__).resolve().parents[1]
COLORS = ["#087f8c", "#c27c23", "#84549c", "#30734d", "#b45353"]


def validate_bundle(bundle):
    """Reject incomplete/mixed evidence; this is consistency checking, not a signature."""
    if bundle.get("bundle_version") != "neurolab-evidence-v1":
        raise ValueError("Unsupported evidence bundle version")
    report = bundle["report"]
    artifacts = bundle["artifacts"]
    if report["completion_status"] != "complete":
        raise ValueError("A complete six-tool investigation is required")
    if len(artifacts) != len(REQUIRED_TOOLS):
        raise ValueError("Exactly six distinct scientific artifacts are required")
    if {a["tool_name"] for a in artifacts} != REQUIRED_TOOLS:
        raise ValueError("Missing or duplicate investigation tools")
    ids = [a["artifact_id"] for a in artifacts]
    if len(set(ids)) != len(ids) or set(ids) != set(report["evidence_ids"]):
        raise ValueError("Report/artifact evidence IDs disagree")
    schema = json.loads((ROOT / "schemas/research_result.schema.json").read_text())
    for artifact in artifacts:
        validate(artifact, schema)
        if artifact["source_sha256"] != report["source_sha256"]:
            raise ValueError("Mixed or mismatched source hashes")
    events = bundle["events"]
    if any(event["run_id"] != report["run_id"] for event in events):
        raise ValueError("Events belong to a different run")
    completed = {
        e["payload"].get("artifact_id") for e in events if e["event_type"] == "tool.completed"
    }
    if not set(ids).issubset(completed):
        raise ValueError("Saved completion events are missing")
    science = build_scientific_report(
        report["objective"],
        artifacts,
        report["decisions"],
        report["reproducibility"],
        report["research_plan"]["hypotheses"],
        [
            HypothesisTest.model_validate(test)
            for test in report["research_plan"].get("hypothesis_tests", [])
        ],
    )
    if science != report["scientific_report"] or science["evidence_coverage"] != "complete":
        raise ValueError("Scientific report does not match its artifacts")
    return report, {a["tool_name"]: a for a in artifacts}


def _figure_data(report, index):
    science = report["scientific_report"]
    candidates = science["candidate_summaries"]
    stability = index["summarize_environment_stability"]["results"]["regimes"]["DROUGHT"]
    selected = {c["genotype_id"] for c in candidates}
    return {
        "regime_comparison": science["findings"]["observed_regime_comparison"],
        "candidate_comparisons": candidates,
        "trait_correlations": [
            {k: v for k, v in a.items() if k != "points"}
            for a in index["analyze_trait_associations"]["results"]["associations"]
        ],
        "environment_profiles": {
            "environment_codes": stability["environment_codes"],
            "genotypes": [g for g in stability["genotypes"] if g["genotype_id"] in selected],
        },
    }


def _save_figure(figure, folder, name, caption, source):
    figure.text(
        0.02,
        0.025,
        caption + f"\nSource SHA-256: {source[:20]}… · full identity and evidence IDs in report",
        fontsize=8,
        color="#43505b",
    )
    figure.savefig(folder / f"{name}.png", dpi=180, facecolor="white")
    figure.savefig(folder / f"{name}.svg", facecolor="white", metadata={"Date": None})


def _regime_figure(plt, data):
    comparison = data["regime_comparison"]
    results = comparison["results"]
    figure, axes = plt.subplots(1, 2, figsize=(11, 5.4), layout="constrained")
    figure.get_layout_engine().set(h_pad=0.6, w_pad=0.2)
    means = results["mean_yield_by_regime"]
    axes[0].bar(
        ["Managed drought", "Well-watered"],
        [means["DROUGHT"], means["WELL_WATERED"]],
        color=COLORS[:2],
    )
    axes[0].set(ylabel="Observed mean grain yield (kg/ha)", title="Separate observed trial regimes")
    uncertainty = comparison["uncertainty"]
    interval = uncertainty["yield_difference_95_ci_kg_ha"]
    estimate = results["yield_difference_kg_ha"]
    axes[1].plot(interval, [0, 0], color=COLORS[0], linewidth=3)
    axes[1].scatter([estimate], [0], color=COLORS[0], s=60)
    axes[1].axvline(0, color="#747b80", linestyle="--", linewidth=1)
    axes[1].set(
        yticks=[],
        xlabel="Drought − watered mean (kg/ha)",
        title="Conditional block-bootstrap interval",
    )
    return (
        figure,
        f"Observed plots: drought {results['plot_count_by_regime']['DROUGHT']}, watered {results['plot_count_by_regime']['WELL_WATERED']}. Regime/environment are confounded; not a causal irrigation effect.",
    )


def _candidate_figure(plt, data):
    candidates = data["candidate_comparisons"]
    figure, axis = plt.subplots(figsize=(11, 6.2), layout="constrained")
    figure.get_layout_engine().set(h_pad=0.6, w_pad=0.2)
    rows = list(range(len(candidates)))
    axis.barh(
        [y - 0.18 for y in rows],
        [c["drought_mean_kg_ha"] for c in candidates],
        height=0.34,
        label="Managed drought",
        color=COLORS[0],
    )
    axis.barh(
        [y + 0.18 for y in rows],
        [c["observed_regime_summary"]["well_watered_mean_kg_ha"] for c in candidates],
        height=0.34,
        label="Well-watered",
        color=COLORS[1],
    )
    axis.set(
        yticks=rows,
        yticklabels=[c["genotype_id"] for c in candidates],
        xlabel="Observed mean grain yield (kg/ha)",
        title="Five largest complete-coverage drought means",
    )
    axis.invert_yaxis()
    axis.legend(loc="lower right")
    return (
        figure,
        "Selected on these same observations; bars are descriptive means, not predictions or confidence intervals.",
    )


def _trait_figure(plt, data):
    import numpy as np

    traits = data["trait_correlations"]
    environments = sorted({e["environment_code"] for a in traits for e in a["per_environment"]})
    matrix = []
    for trait in traits:
        per_environment = {
            e["environment_code"]: e["spearman_rho"] for e in trait["per_environment"]
        }
        matrix.append([trait["spearman_rho"], *[per_environment.get(e) for e in environments]])
    values = np.array([[math.nan if x is None else x for x in row] for row in matrix])
    figure, axis = plt.subplots(figsize=(11, 6.6), layout="constrained")
    figure.get_layout_engine().set(h_pad=0.6, w_pad=0.2)
    image = axis.imshow(np.ma.masked_invalid(values), cmap="BrBG", vmin=-1, vmax=1, aspect="auto")
    axis.set(
        xticks=range(len(environments) + 1),
        xticklabels=["Equal-environment means", *environments],
        yticks=range(len(traits)),
        yticklabels=[a["trait"] for a in traits],
        title="Trait–yield Spearman correlations within drought trials",
    )
    for i, row in enumerate(values):
        for j, value in enumerate(row):
            axis.text(
                j,
                i,
                "NA" if math.isnan(value) else f"{value:.2f}",
                ha="center",
                va="center",
                fontsize=11,
            )
    figure.colorbar(image, ax=axis, label="Spearman ρ")
    return (
        figure,
        "One point per paired-complete genotype, n recorded in figure-data.json. STYG direction is unverified; no causal or multiplicity claim.",
    )


def _environment_figure(plt, data):
    profiles = data["environment_profiles"]
    codes = profiles["environment_codes"]
    figure, axis = plt.subplots(figsize=(11, 6.8), layout="constrained")
    figure.get_layout_engine().set(h_pad=0.6, w_pad=0.2)
    for color, genotype in zip(COLORS, profiles["genotypes"], strict=False):
        means = {
            e["environment_code"]: e["mean_yield_kg_ha"] for e in genotype["environment_means"]
        }
        axis.plot(
            range(len(codes)),
            [means.get(code, math.nan) for code in codes],
            marker="o",
            color=color,
            label=genotype["genotype_id"],
        )
    axis.set(
        xticks=range(len(codes)),
        xticklabels=codes,
        ylabel="Observed environment mean grain yield (kg/ha)",
        title="Observed environment variation of the five leading means",
    )
    axis.legend(loc="upper right", fontsize=8)
    return (
        figure,
        "Lines connect observed environment means for comparison. ENVT codes are not calendar years; this is not a forecast or G×E model.",
    )


def _render_value(value):
    if isinstance(value, dict):
        rows = "".join(
            f"<dt>{html.escape(key.replace('_', ' '))}</dt><dd>{_render_value(item)}</dd>"
            for key, item in value.items()
        )
        return f"<dl>{rows}</dl>"
    if isinstance(value, list):
        return "<ul>" + "".join(f"<li>{_render_value(item)}</li>" for item in value) + "</ul>"
    if value is None:
        return "<span>Not available</span>"
    return "<span>" + html.escape(str(value)).replace("\n", "<br>") + "</span>"


def _section(title, value):
    return f"<section><h2>{html.escape(title)}</h2>{_render_value(value)}</section>"


def _write_html(folder, report, figures, export_metadata, development_audit=None):
    science = report["scientific_report"]
    sections = [
        ("1. Research objective", report["objective"]),
        (
            "2. Sources and provenance",
            {"citations": science["source_citations"], "inventory": science["dataset_inventory"]},
        ),
        ("3. Hypotheses and counterevidence", science["hypothesis_evaluations"]),
        ("4. Methodology", science["methodology"]),
        ("5. Statistical findings", science["findings"]),
    ]
    content = "".join(_section(title, value) for title, value in sections)
    content += "<section><h2>6. Visualizations from saved numeric artifacts</h2>"
    for name, caption in figures:
        encoded = base64.b64encode((folder / f"{name}.png").read_bytes()).decode()
        content += f'<figure><img alt="{html.escape(caption, quote=True)}" src="data:image/png;base64,{encoded}"><figcaption>{html.escape(caption)}</figcaption></figure>'
    content += "</section>"
    for title, value in [
        (
            "7. Exploratory candidates",
            {
                "observational_answer": science.get("observational_answer"),
                "candidate_summaries": science["candidate_summaries"],
            },
        ),
        ("8. Scientific limitations", report["limitations"] + science["unresolved_scope"]),
        (
            "9. Next experiments — proposal, not executed",
            {
                "executed_follow_up": science["follow_up_analysis"],
                "proposed_trial": science["next_experiment"],
            },
        ),
        (
            "10. Reproducibility",
            {
                "source_sha256": report["source_sha256"],
                "seed": report["seed"],
                "configuration": report["research_configuration"],
                "plan": report["research_plan"],
                "evidence_ids": report["evidence_ids"],
                "loaded_code": report["reproducibility"],
                "export_metadata": export_metadata,
            },
        ),
    ]:
        content += _section(title, value)
    if development_audit:
        content += _section(
            "11. Development and verification history — engineering appendix",
            development_audit,
        )
    document = f"""<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><meta http-equiv="Content-Security-Policy" content="default-src 'none'; img-src data:; style-src 'unsafe-inline'"><title>NeuroLab — exploratory maize investigation</title><style>body{{font:16px/1.55 system-ui,sans-serif;color:#182d35;background:#f5f5f0;max-width:1100px;margin:40px auto;padding:24px}}h1,h2{{line-height:1.25}}h1{{font-size:36px}}h2{{margin-top:48px}}dl{{display:grid;grid-template-columns:minmax(120px,22%) 1fr;gap:10px 20px;border-top:1px solid #ccd4d1;padding-top:14px}}dt{{font-size:13px;font-weight:650;color:#42616a;text-transform:capitalize;overflow-wrap:anywhere}}dd{{margin:0;min-width:0;overflow-wrap:anywhere}}dd dl{{grid-template-columns:minmax(100px,28%) 1fr;font-size:14px}}li{{margin:8px 0}}@media(max-width:650px){{dl,dd dl{{display:block}}dt{{margin-top:14px}}}}pre{{white-space:pre-wrap;overflow-wrap:anywhere;font:13px/1.65 ui-monospace,monospace;background:white;padding:20px;border:1px solid #ccd4d1;border-radius:8px}}img{{width:100%;height:auto}}figure{{margin:24px 0}}figcaption,footer{{font-size:13px;color:#465c63}}aside{{border-left:4px solid #ad781f;padding:12px 20px;background:#f1ead7}}@media print{{body{{background:white;margin:0;max-width:none}}figure{{break-inside:avoid}}h2{{break-after:avoid}}}}</style><h1>Observed maize trials: evidence and limits</h1><p>NeuroLab AI · run {html.escape(report["run_id"])} · {html.escape(report["mode"])}</p><aside>{html.escape(science["scope"])}<br>Export presents persisted numeric evidence. No model was called by the exporter. Bundle consistency checks do not authenticate third-party edits or establish scientific validity.</aside>{content}<footer>Actual field-study data credited above. Figures are observed summaries, not simulated crops or field recommendations. Full unrounded plotting data and saved evidence accompany this report.</footer></html>"""
    (folder / "report.html").write_text(document, encoding="utf-8")


def export_bundle(bundle_path: Path, output: Path):
    raw = bundle_path.read_bytes()
    bundle = json.loads(raw)
    report, index = validate_bundle(bundle)
    # Optional dependency is isolated from the service and ordinary API installation.
    import matplotlib

    matplotlib.use("Agg")
    import numpy as np
    from matplotlib import pyplot as plt

    export_metadata = {
        "bundle_sha256": hashlib.sha256(raw).hexdigest(),
        "exporter_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "python_version": platform.python_version(),
        "matplotlib_version": matplotlib.__version__,
        "numpy_version": np.__version__,
        "presentation_only": True,
    }

    output.parent.mkdir(parents=True, exist_ok=True)
    if output.exists():
        raise FileExistsError("Choose a new output directory; existing exports are preserved")
    data = _figure_data(report, index)
    figures = []
    with tempfile.TemporaryDirectory(dir=output.parent) as temporary:
        folder = Path(temporary) / "report"
        folder.mkdir()
        with plt.rc_context(
            {
                "font.family": "DejaVu Sans",
                "text.usetex": False,
                "axes.spines.top": False,
                "axes.spines.right": False,
            }
        ):
            for name, renderer in [
                ("regime-comparison", _regime_figure),
                ("candidate-comparison", _candidate_figure),
                ("trait-correlations", _trait_figure),
                ("environment-profiles", _environment_figure),
            ]:
                figure, caption = renderer(plt, data)
                try:
                    _save_figure(figure, folder, name, caption, report["source_sha256"])
                finally:
                    plt.close(figure)
                figures.append((name, caption))
        (folder / "figure-data.json").write_text(json.dumps(data, indent=2, allow_nan=False) + "\n")
        (folder / "evidence.json").write_bytes(raw)
        (folder / "export-metadata.json").write_text(json.dumps(export_metadata, indent=2) + "\n")
        _write_html(folder, report, figures, export_metadata, bundle.get("development_audit"))
        folder.rename(output)
    return {
        "run_id": report["run_id"],
        "figure_count": len(figures),
        "report": str(output / "report.html"),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bundle", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(export_bundle(args.bundle, args.output), indent=2))


if __name__ == "__main__":
    main()
