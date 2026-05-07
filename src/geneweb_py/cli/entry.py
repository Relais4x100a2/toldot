"""Point d'entrée minimal du binaire ``geneweb-py`` (import différé des deps CLI)."""


def main() -> None:
    """Lance le groupe de commandes Click après vérification des dépendances."""
    try:
        from geneweb_py.cli.commands import cli
    except ImportError:
        import sys

        sys.stderr.write(
            'Dépendances CLI absentes. Installez : pip install "geneweb-py[cli]"\n'
        )
        raise SystemExit(1) from None
    cli()
