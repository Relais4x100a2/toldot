"""Tests du script CI de commentaire régression couverture."""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

SCRIPT = (
    Path(__file__).resolve().parents[2] / "scripts" / "ci" / "pr_coverage_comment.py"
)


def _load_comment_module():  # type: ignore[no-untyped-def]
    spec = importlib.util.spec_from_file_location("pr_coverage_comment", SCRIPT)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _write_cov(path: Path, percent: float) -> None:
    path.write_text(
        json.dumps({"totals": {"percent_covered": percent}}),
        encoding="utf-8",
    )


def test_build_body_shows_delta_positive() -> None:
    """Le tableau markdown inclut la baseline et un delta positif."""
    mod = _load_comment_module()
    body = mod.build_body(
        current=90.0,
        baseline=87.0,
        baseline_ref="main",
        fail_under=84.0,
        tests_outcome="succès",
    )
    assert "**90.00%**" in body
    assert "**87.00%**" in body
    assert "+3.00 points" in body


def test_fail_on_regression_exits_1(tmp_path: Path) -> None:
    """Retourne 1 si la couverture courante est strictement sous la baseline."""
    cur = tmp_path / "c.json"
    base = tmp_path / "b.json"
    _write_cov(cur, 80.0)
    _write_cov(base, 85.0)

    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--current",
            str(cur),
            "--baseline",
            str(base),
            "--base-ref",
            "main",
            "--fail-on-regression",
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 1


def test_equal_coverage_exits_0(tmp_path: Path) -> None:
    """Pas de régression si courante == baseline."""
    cur = tmp_path / "c.json"
    base = tmp_path / "b.json"
    out = tmp_path / "out.md"
    pct = 86.52
    _write_cov(cur, pct)
    _write_cov(base, pct)

    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--current",
            str(cur),
            "--baseline",
            str(base),
            "-o",
            str(out),
            "--fail-on-regression",
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    body = out.read_text(encoding="utf-8")
    assert body.startswith("<!-- geneweb-py-coverage-regression -->")


def test_without_baseline_file_no_failure_on_regression(tmp_path: Path) -> None:
    """Baseline absente : --fail-on-regression ne fait pas échouer."""
    cur = tmp_path / "c.json"
    missing_base = tmp_path / "pas_la.json"
    _write_cov(cur, 82.0)

    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--current",
            str(cur),
            "--baseline",
            str(missing_base),
            "--fail-on-regression",
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
