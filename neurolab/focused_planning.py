"""Transparent keyword routing for focused replay; never model reasoning.

Rules describe supported tools, not scientific acceptance or complete semantic
understanding. Explicit method selections and the six-tool profile take priority.
"""

from __future__ import annotations

import re

RULES = (
    (
        "source structure",
        r"\b(?:profile|structure|provenance|source|records|rows|envt|calendar)\b|\bhow many plots\b",
        ("dataset_profile",),
    ),
    ("missing data", r"\b(?:missing\w*|absent|incomplete|data quality)\b", ("missingness_audit",)),
    (
        "trait associations",
        r"\b(?:correlat\w*|associat\w*|asi|anthesis|silking|stay.green)\b",
        ("trait_associations",),
    ),
    (
        "environment sensitivity",
        r"\b(?:stability|stable|variability|variation|sensitivity)\b|across environments|leave.one.environment",
        ("environment_stability",),
    ),
    (
        "genotype candidates",
        r"\b(?:rank\w*|candidates?)\b|\bwhich genotypes?\b|\bbest genotypes?\b",
        ("genotype_ranking",),
    ),
    (
        "regime comparison",
        r"\b(?:compare|comparisons?|contrast|retention|denominator|ratio|causal|irrigation)\b|\b(?:drought|watered).{0,30}\b(?:well.watered|drought)\b",
        ("block_bootstrap_contrast",),
    ),
)
FALLBACK_METHODS = ["block_bootstrap_contrast", "genotype_ranking", "missingness_audit"]
ROUTING_NOTICE = "Focused replay uses deterministic keyword routing v1, not Meta inference or complete semantic interpretation. Workflow completion means selected tasks finished; it does not establish every requested scientific claim."


def requests_maize_investigation(objective: str) -> bool:
    """Recognize an explicit multi-stage investigation, never infer its findings."""
    text = _positive_clauses(objective)
    return all(
        re.search(pattern, text)
        for pattern in (
            r"\bmaize\b",
            r"\bdrought\b",
            r"\bgenotypes?\b",
            r"\b(?:stable|stability)\b",
            r"\bhypothes\w*\b",
            r"\bnext experiment\b",
        )
    )


def _positive_clauses(objective):
    clauses = re.split(r"[;.!?\n]|\b(?:but|instead|only)\b", objective.casefold())
    parts = []
    for clause in clauses:
        excluded = re.search(
            r"\b(?:do not|don't|skip|exclude|avoid|without (?:running|calculating|computing))\b",
            clause,
        )
        parts.append(clause[: excluded.start()] if excluded else clause)
    return " ".join(parts)


def focused_methods(objective: str):
    text = _positive_clauses(objective)
    matches = [(label, methods) for label, pattern, methods in RULES if re.search(pattern, text)]
    methods = list(dict.fromkeys(method for _, entries in matches for method in entries))
    if not methods:
        return (
            list(FALLBACK_METHODS),
            [ROUTING_NOTICE],
            [
                "No supported focused keyword matched. A generic exploratory contrast/ranking/missingness workflow was selected; refine the objective or explicitly choose methods."
            ],
        )
    labels = ", ".join(label for label, _ in matches)
    return methods, [ROUTING_NOTICE, "Matched supported question topics: " + labels + "."], []
