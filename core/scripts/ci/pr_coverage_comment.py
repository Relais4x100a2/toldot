#!/usr/bin/env python3
"""Génère le corps du commentaire PR pour la couverture et la régression.

Lit ``coverage.json`` (branche courante) et optionnellement
``coverage_baseline.json`` (merge-base avec la branche de base).
Écrit le markdown dans le fichier passé en ``--output``.

Codes de sortie :
    0 : pas de régression par rapport à la baseline (ou baseline absente)
    1 : couverture courante strictement inférieure à la baseline
"""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any, Dict, Optional, TextIO

MARKER = "<!-- geneweb-py-coverage-regression -->"


def _load_totals(path: str) -> Optional[float]:
    """Retourne ``percent_covered`` ou ``None`` si fichier absent ou invalide."""
    try:
        with open(path, encoding="utf-8") as f:
            data: Dict[str, Any] = json.load(f)
        return float(data["totals"]["percent_covered"])
    except (OSError, ValueError, KeyError, TypeError):
        return None


def _format_delta(current: float, baseline: Optional[float]) -> str:
    if baseline is None:
        return "_Baseline indisponible (merge-base non mesuré)._"
    delta = current - baseline
    if delta > 0:
        return f"+{delta:.2f} points par rapport à la baseline (`{baseline:.2f}%`)."
    if delta < 0:
        return f"{delta:.2f} points par rapport à la baseline (`{baseline:.2f}%`)."
    return f"Identique à la baseline (`{baseline:.2f}%`)."


def build_body(
    *,
    current: float,
    baseline: Optional[float],
    baseline_ref: str,
    fail_under: float,
    tests_outcome: str,
    marker: str = MARKER,
) -> str:
    """Construit le corps du commentaire markdown."""
    lines = [
        marker,
        "## Couverture et régression",
        "",
        "| Indicateur | Valeur |",
        "|------------|--------|",
        f"| Couverture (cette branche) | **{current:.2f}%** |",
    ]
    if baseline is not None:
        lines.append(
            f"| Baseline (merge-base `{baseline_ref}`) | **{baseline:.2f}%** |"
        )
    else:
        lines.append("| Baseline (merge-base) | _non disponible_ |")
    lines.extend(
        [
            f"| Seuil `--cov-fail-under` | **{fail_under:.0f}%** |",
            f"| Jobs tests | **{tests_outcome}** |",
            "",
            "### Détail",
            "",
            _format_delta(current, baseline),
            "",
            "— _Workflow `pr-checks.yml`_",
        ]
    )
    return "\n".join(lines)


def parse_args(argv: Optional[list[str]] = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Commentaire régression couverture PR.")
    p.add_argument("--current", default="coverage.json", help="Rapport JSON courant.")
    p.add_argument(
        "--baseline",
        default="coverage_baseline.json",
        help="Rapport JSON au merge-base (optionnel).",
    )
    p.add_argument(
        "--fail-under",
        type=float,
        default=84.0,
        help="Seuil documenté dans le commentaire.",
    )
    p.add_argument(
        "--tests-outcome",
        default="success",
        help="Résumé affiché (ex. succès ou échec pytest).",
    )
    p.add_argument(
        "--base-ref",
        default="main",
        help="Référence de la branche de base (affichage).",
    )
    p.add_argument(
        "--output",
        "-o",
        default="",
        help=(
            "Fichier markdown de sortie "
            "(omis = pas d'écriture, utile pour --fail-on-regression)."
        ),
    )
    p.add_argument(
        "--fail-on-regression",
        action="store_true",
        help="Code 1 si current < baseline (baseline présente).",
    )
    p.add_argument(
        "--regression-epsilon",
        type=float,
        default=0.0,
        metavar="PCT",
        help=(
            "Tolérance en points de pourcentage avant échec vs baseline "
            "(ex. 0.15 pour compenser arrondis ou ajout de lignes peu couvertes)."
        ),
    )
    return p.parse_args(argv)


def main(argv: Optional[list[str]] = None, stdout: TextIO = sys.stdout) -> int:
    args = parse_args(argv)
    current = _load_totals(args.current)
    baseline = _load_totals(args.baseline)

    if current is None:
        print(
            "Avertissement : impossible de lire la couverture courante.",
            file=stdout,
        )
        body = "\n".join(
            [
                MARKER,
                "## Couverture et régression",
                "",
                "Le fichier `coverage.json` est absent ou invalide après les tests.",
                "",
                "— _Workflow `pr-checks.yml`_",
            ]
        )
        if args.output:
            with open(args.output, "w", encoding="utf-8") as out:
                out.write(body)
        return 0

    body = build_body(
        current=current,
        baseline=baseline,
        baseline_ref=args.base_ref,
        fail_under=args.fail_under,
        tests_outcome=args.tests_outcome,
    )

    if args.output:
        with open(args.output, "w", encoding="utf-8") as out:
            out.write(body)

    eff_baseline = baseline - args.regression_epsilon if baseline is not None else None
    if (
        args.fail_on_regression
        and eff_baseline is not None
        and current + 1e-9 < eff_baseline
    ):
        eps_note = (
            f" (seuil effectif {eff_baseline:.2f}% avec ε={args.regression_epsilon:g})"
            if args.regression_epsilon > 0
            else ""
        )
        print(
            (
                f"Régression de couverture : {current:.2f}% "
                f"< baseline {baseline:.2f}%{eps_note}"
            ),
            file=stdout,
        )
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
