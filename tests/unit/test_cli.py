"""
Tests unitaires du binaire ``geneweb-py`` (Click + Rich).
"""

from pathlib import Path
from typing import Dict

import pytest
from click.testing import CliRunner, Result

pytest.importorskip("rich")

from geneweb_py.cli.commands import cli

FIXTURES_DIR = Path(__file__).resolve().parent.parent / "fixtures"
SIMPLE_GW = FIXTURES_DIR / "simple_test.gw"


def _combined_output(result: Result) -> str:
    """Concatène stdout/stderr selon CliRunner.mix_stderr (Click 8+).

    Par défaut Click mélange stderr dans ``result.output`` : accéder à
    ``result.stderr`` lève alors ``ValueError`` (CI Python 3.8/3.9).
    """
    try:
        err = result.stderr or ""
    except ValueError:
        return result.output or ""
    out = result.stdout or ""
    return f"{out}{err}"


@pytest.fixture
def runner() -> CliRunner:
    """Runner Click isolé."""
    return CliRunner()


@pytest.mark.unit
def test_cli_help_displays_commands(runner: CliRunner) -> None:
    """``--help`` liste les sous-commandes parse et export."""
    result = runner.invoke(cli, ["--help"])
    assert result.exit_code == 0
    assert "parse" in result.output
    assert "export" in result.output


@pytest.mark.unit
def test_cli_version(runner: CliRunner) -> None:
    """``--version`` affiche la version du package."""
    result = runner.invoke(cli, ["--version"])
    assert result.exit_code == 0
    assert "geneweb-py" in result.output


@pytest.mark.unit
def test_parse_command_summary(runner: CliRunner) -> None:
    """``parse`` affiche un résumé pour un fichier .gw valide."""
    result = runner.invoke(cli, ["parse", str(SIMPLE_GW)])
    assert result.exit_code == 0
    out = result.output
    assert "Résumé" in out or "Personnes" in out
    assert str(SIMPLE_GW) in out or SIMPLE_GW.name in out


@pytest.mark.unit
def test_parse_command_missing_file(runner: CliRunner) -> None:
    """Fichier absent : code de sortie non nul."""
    missing = FIXTURES_DIR / "n_existe_pas.gw"
    result = runner.invoke(cli, ["parse", str(missing)])
    assert result.exit_code != 0


@pytest.mark.unit
@pytest.mark.parametrize("fmt", ["gedcom", "json", "xml"])
def test_export_command_formats(runner: CliRunner, tmp_path: Path, fmt: str) -> None:
    """``export`` produit un fichier pour chaque format supporté."""
    if fmt == "gedcom":
        out_file = tmp_path / "out.ged"
    elif fmt == "json":
        out_file = tmp_path / "out.json"
    else:
        out_file = tmp_path / "out.xml"

    result = runner.invoke(
        cli,
        [
            "export",
            str(SIMPLE_GW),
            "--format",
            fmt,
            "-o",
            str(out_file),
        ],
    )
    assert result.exit_code == 0, _combined_output(result)
    assert out_file.is_file()
    assert out_file.stat().st_size > 0


@pytest.mark.unit
def test_export_requires_format(runner: CliRunner, tmp_path: Path) -> None:
    """``--format`` est obligatoire."""
    out_file = tmp_path / "x.ged"
    result = runner.invoke(
        cli,
        ["export", str(SIMPLE_GW), "-o", str(out_file)],
    )
    assert result.exit_code != 0


@pytest.mark.unit
def test_export_parse_error_shows_rich_panel(
    runner: CliRunner,
    tmp_path: Path,
) -> None:
    """Erreur de parsing : message sur stderr (Rich)."""
    bad = tmp_path / "bad.txt"
    bad.write_text("not a gw file", encoding="utf-8")
    out_file = tmp_path / "out.ged"
    result = runner.invoke(
        cli,
        ["export", str(bad), "--format", "gedcom", "-o", str(out_file)],
    )
    assert result.exit_code != 0
    combined = _combined_output(result)
    assert "Erreur" in combined or "extension" in combined.lower()


@pytest.mark.unit
def test_entry_main_imports_cli(monkeypatch: pytest.MonkeyPatch) -> None:
    """Le point d'entrée ``main`` délègue au groupe Click."""
    import geneweb_py.cli.commands as commands_module
    from geneweb_py.cli import entry

    called: Dict[str, bool] = {}

    def fake_cli() -> None:
        called["ok"] = True

    monkeypatch.setattr(commands_module, "cli", fake_cli)
    entry.main()
    assert called.get("ok") is True
