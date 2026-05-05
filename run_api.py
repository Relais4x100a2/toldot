#!/usr/bin/env python3
"""
Script de lancement pour l'API GeneWeb-py.

Ce script permet de lancer l'API FastAPI avec uvicorn pour le développement
et la production.
"""

import argparse
import sys
from pathlib import Path

import uvicorn

# Ajout du répertoire src au path Python (structure src/)
root_dir = Path(__file__).parent
sys.path.insert(0, str(root_dir / "src"))


def main():
    """Fonction principale de lancement de l'API."""
    parser = argparse.ArgumentParser(
        description="Lance l'API GeneWeb-py avec FastAPI et uvicorn"
    )

    parser.add_argument(
        "--host",
        default="127.0.0.1",
        help="Adresse IP du serveur (défaut: 127.0.0.1)",
    )

    parser.add_argument(
        "--port", type=int, default=8000, help="Port du serveur (défaut: 8000)"
    )

    parser.add_argument(
        "--reload",
        action="store_true",
        help="Active le rechargement automatique en cas de modification des fichiers",
    )

    parser.add_argument(
        "--log-level",
        choices=["critical", "error", "warning", "info", "debug", "trace"],
        default="info",
        help="Niveau de logging (défaut: info)",
    )

    parser.add_argument(
        "--workers", type=int, default=1, help="Nombre de workers uvicorn (défaut: 1)"
    )

    parser.add_argument(
        "--env",
        choices=["dev", "prod", "test"],
        default="dev",
        help="Environnement d'exécution (défaut: dev)",
    )

    args = parser.parse_args()

    # Configuration selon l'environnement
    if args.env == "prod":
        # Configuration de production
        reload = False
        log_level = "warning"
        workers = args.workers if args.workers > 1 else 4
    elif args.env == "test":
        # Configuration de test
        reload = False
        log_level = "debug"
        workers = 1
    else:
        # Configuration de développement
        reload = args.reload
        log_level = args.log_level
        workers = 1

    print("🚀 Lancement de l'API GeneWeb-py")
    print(f"📍 Environnement: {args.env}")
    print(f"🌐 Serveur: http://{args.host}:{args.port}")
    print(f"📚 Documentation: http://{args.host}:{args.port}/docs")
    print(f"📖 ReDoc: http://{args.host}:{args.port}/redoc")
    print(f"🔄 Rechargement: {'Activé' if reload else 'Désactivé'}")
    print(f"👥 Workers: {workers}")
    print(f"📝 Log level: {log_level}")
    print("-" * 50)

    try:
        # Lancement du serveur
        uvicorn.run(
            "geneweb_py.api.main:app",
            host=args.host,
            port=args.port,
            reload=reload,
            log_level=log_level,
            workers=workers,
            access_log=True,
        )
    except KeyboardInterrupt:
        print("\n🛑 Arrêt du serveur demandé par l'utilisateur")
    except Exception as exc:
        print(f"❌ Erreur lors du lancement du serveur: {exc}")
        sys.exit(1)


if __name__ == "__main__":
    main()
