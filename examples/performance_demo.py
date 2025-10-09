#!/usr/bin/env python3
"""
Démonstration des optimisations de performance du parser GeneWeb

Ce script montre comment utiliser les différentes options de performance
et comment mesurer les gains en temps et en mémoire.
"""

import time
import tracemalloc
from pathlib import Path

from geneweb_py.core.parser.gw_parser import GeneWebParser
from geneweb_py.core.parser.streaming import (
    should_use_streaming,
    estimate_memory_usage
)


def demo_automatic_mode():
    """Démonstration du mode automatique (recommandé)"""
    print("\n" + "=" * 80)
    print("DÉMONSTRATION : MODE AUTOMATIQUE")
    print("=" * 80)
    
    # Le parser détecte automatiquement la taille du fichier
    # et choisit le mode optimal
    parser = GeneWebParser()
    
    # Exemple avec un petit fichier
    small_file = Path(__file__).parent.parent / "tests" / "fixtures" / "simple_family.gw"
    if small_file.exists():
        print(f"\n1. Parsing d'un petit fichier : {small_file.name}")
        print(f"   Taille : {small_file.stat().st_size / 1024:.2f} KB")
        
        start = time.perf_counter()
        genealogy = parser.parse_file(small_file)
        elapsed = time.perf_counter() - start
        
        print(f"   Mode utilisé : NORMAL (automatique)")
        print(f"   Temps : {elapsed:.3f}s")
        print(f"   Personnes : {len(genealogy.persons)}")
        print(f"   Familles : {len(genealogy.families)}")


def demo_streaming_mode():
    """Démonstration du mode streaming forcé"""
    print("\n" + "=" * 80)
    print("DÉMONSTRATION : MODE STREAMING FORCÉ")
    print("=" * 80)
    
    # Forcer le mode streaming (pour tests ou besoins spécifiques)
    parser = GeneWebParser(stream_mode=True)
    
    test_file = Path(__file__).parent.parent / "tests" / "fixtures" / "test_complete.gw"
    if test_file.exists():
        print(f"\nParsing avec mode streaming forcé : {test_file.name}")
        print(f"Taille : {test_file.stat().st_size / 1024:.2f} KB")
        
        start = time.perf_counter()
        genealogy = parser.parse_file(test_file)
        elapsed = time.perf_counter() - start
        
        print(f"Mode utilisé : STREAMING (forcé)")
        print(f"Temps : {elapsed:.3f}s")
        print(f"Personnes : {len(genealogy.persons)}")
        print(f"Familles : {len(genealogy.families)}")


def demo_memory_measurement():
    """Démonstration de la mesure d'utilisation mémoire"""
    print("\n" + "=" * 80)
    print("DÉMONSTRATION : MESURE DE L'UTILISATION MÉMOIRE")
    print("=" * 80)
    
    test_file = Path(__file__).parent.parent / "tests" / "fixtures" / "test_complete.gw"
    if not test_file.exists():
        print("\nFichier de test non trouvé")
        return
    
    # Mesurer avec mode normal
    print(f"\n1. Parsing en mode NORMAL avec mesure mémoire")
    
    tracemalloc.start()
    start = time.perf_counter()
    
    parser = GeneWebParser(stream_mode=False)
    genealogy = parser.parse_file(test_file)
    
    elapsed = time.perf_counter() - start
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    
    print(f"   Temps : {elapsed:.3f}s")
    print(f"   Mémoire courante : {current / 1024 / 1024:.2f} MB")
    print(f"   Mémoire pic : {peak / 1024 / 1024:.2f} MB")
    
    # Mesurer avec mode streaming
    print(f"\n2. Parsing en mode STREAMING avec mesure mémoire")
    
    tracemalloc.start()
    start = time.perf_counter()
    
    parser = GeneWebParser(stream_mode=True)
    genealogy = parser.parse_file(test_file)
    
    elapsed_streaming = time.perf_counter() - start
    current_streaming, peak_streaming = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    
    print(f"   Temps : {elapsed_streaming:.3f}s")
    print(f"   Mémoire courante : {current_streaming / 1024 / 1024:.2f} MB")
    print(f"   Mémoire pic : {peak_streaming / 1024 / 1024:.2f} MB")
    
    # Calcul des gains
    print(f"\n3. Gains avec le mode streaming")
    time_diff = ((elapsed - elapsed_streaming) / elapsed) * 100
    memory_diff = ((peak - peak_streaming) / peak) * 100
    print(f"   Temps : {time_diff:+.1f}%")
    print(f"   Mémoire : {memory_diff:+.1f}%")


def demo_memory_estimate():
    """Démonstration de l'estimation mémoire"""
    print("\n" + "=" * 80)
    print("DÉMONSTRATION : ESTIMATION MÉMOIRE AVANT PARSING")
    print("=" * 80)
    
    test_file = Path(__file__).parent.parent / "tests" / "fixtures" / "test_complete.gw"
    if not test_file.exists():
        print("\nFichier de test non trouvé")
        return
    
    print(f"\nFichier : {test_file.name}")
    print(f"Taille : {test_file.stat().st_size / 1024:.2f} KB")
    
    # Vérifier si le streaming est recommandé
    use_streaming = should_use_streaming(test_file)
    print(f"\nMode recommandé : {'STREAMING' if use_streaming else 'NORMAL'}")
    
    # Obtenir l'estimation détaillée
    parser = GeneWebParser()
    estimate = parser.get_memory_estimate(test_file)
    
    print(f"\nEstimations mémoire :")
    print(f"  Taille fichier : {estimate['file_size_mb']:.2f} MB")
    print(f"  Mode normal : {estimate['estimated_normal_memory_mb']:.2f} MB")
    print(f"  Mode streaming : {estimate['estimated_streaming_memory_mb']:.2f} MB")
    print(f"  Économie estimée : {estimate['memory_saving_percent']:.1f}%")


def demo_custom_threshold():
    """Démonstration de l'ajustement du seuil de streaming"""
    print("\n" + "=" * 80)
    print("DÉMONSTRATION : AJUSTEMENT DU SEUIL DE STREAMING")
    print("=" * 80)
    
    print("\nPar défaut, le streaming s'active automatiquement pour les fichiers >10MB")
    print("Vous pouvez ajuster ce seuil selon vos besoins :")
    
    print("\n1. Seuil bas (5MB) - Streaming plus agressif")
    parser_low = GeneWebParser(streaming_threshold_mb=5.0)
    print(f"   streaming_threshold_mb = 5.0")
    print(f"   → Économise plus de mémoire, utile pour systèmes contraints")
    
    print("\n2. Seuil par défaut (10MB) - Équilibré")
    parser_default = GeneWebParser()
    print(f"   streaming_threshold_mb = 10.0 (défaut)")
    print(f"   → Bon compromis temps/mémoire pour la plupart des cas")
    
    print("\n3. Seuil élevé (50MB) - Streaming moins fréquent")
    parser_high = GeneWebParser(streaming_threshold_mb=50.0)
    print(f"   streaming_threshold_mb = 50.0")
    print(f"   → Privilégie la vitesse sur systèmes avec beaucoup de RAM")


def demo_validation_options():
    """Démonstration des options de validation"""
    print("\n" + "=" * 80)
    print("DÉMONSTRATION : OPTIONS DE VALIDATION")
    print("=" * 80)
    
    test_file = Path(__file__).parent.parent / "tests" / "fixtures" / "test_complete.gw"
    if not test_file.exists():
        print("\nFichier de test non trouvé")
        return
    
    print("\n1. Avec validation (par défaut) - Plus sûr mais plus lent")
    tracemalloc.start()
    start = time.perf_counter()
    
    parser_validate = GeneWebParser(validate=True)
    genealogy = parser_validate.parse_file(test_file)
    
    elapsed_validate = time.perf_counter() - start
    _, peak_validate = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    
    print(f"   Temps : {elapsed_validate:.3f}s")
    print(f"   Mémoire pic : {peak_validate / 1024 / 1024:.2f} MB")
    
    print("\n2. Sans validation - Plus rapide mais moins sûr")
    tracemalloc.start()
    start = time.perf_counter()
    
    parser_no_validate = GeneWebParser(validate=False)
    genealogy = parser_no_validate.parse_file(test_file)
    
    elapsed_no_validate = time.perf_counter() - start
    _, peak_no_validate = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    
    print(f"   Temps : {elapsed_no_validate:.3f}s")
    print(f"   Mémoire pic : {peak_no_validate / 1024 / 1024:.2f} MB")
    
    # Gains
    time_gain = ((elapsed_validate - elapsed_no_validate) / elapsed_validate) * 100
    print(f"\n3. Gain en désactivant la validation : {time_gain:.1f}%")
    print(f"   ⚠️  Utiliser seulement pour fichiers de confiance")


def main():
    """Point d'entrée principal"""
    print("\n")
    print("╔" + "=" * 78 + "╗")
    print("║" + " " * 78 + "║")
    print("║" + "  DÉMONSTRATION DES OPTIMISATIONS DE PERFORMANCE - geneweb-py".center(78) + "║")
    print("║" + " " * 78 + "║")
    print("╚" + "=" * 78 + "╝")
    
    # Exécuter toutes les démos
    demo_automatic_mode()
    demo_streaming_mode()
    demo_memory_measurement()
    demo_memory_estimate()
    demo_custom_threshold()
    demo_validation_options()
    
    # Résumé
    print("\n" + "=" * 80)
    print("RÉSUMÉ DES BONNES PRATIQUES")
    print("=" * 80)
    print("""
1. 📋 Utiliser le mode automatique par défaut
   → parser = GeneWebParser()
   
2. 🚀 Forcer le streaming pour fichiers volumineux si besoin
   → parser = GeneWebParser(stream_mode=True)
   
3. 💾 Estimer la mémoire avant de parser de gros fichiers
   → estimate = parser.get_memory_estimate(file_path)
   
4. ⚡ Désactiver la validation pour gains de vitesse (si fichier de confiance)
   → parser = GeneWebParser(validate=False)
   
5. 🔧 Ajuster le seuil selon vos contraintes mémoire
   → parser = GeneWebParser(streaming_threshold_mb=5.0)
   
6. 📊 Mesurer les performances avec tracemalloc et time.perf_counter()

Pour plus d'informations, consultez doc/PERFORMANCE.md
    """)
    print("=" * 80 + "\n")


if __name__ == "__main__":
    main()

