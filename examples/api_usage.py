#!/usr/bin/env python3
"""
Exemple d'utilisation de l'API GeneWeb-py avec FastAPI.

Ce script démontre comment utiliser l'API REST pour manipuler
les données généalogiques.
"""

import requests
import json
from typing import Dict, Any


class GeneWebAPIClient:
    """Client pour l'API GeneWeb-py."""
    
    def __init__(self, base_url: str = "http://127.0.0.1:8000"):
        """
        Initialise le client API.
        
        Args:
            base_url: URL de base de l'API
        """
        self.base_url = base_url
        self.session = requests.Session()
    
    def health_check(self) -> Dict[str, Any]:
        """Vérifie l'état de santé de l'API."""
        response = self.session.get(f"{self.base_url}/health")
        response.raise_for_status()
        return response.json()
    
    def get_stats(self) -> Dict[str, Any]:
        """Récupère les statistiques de la généalogie."""
        response = self.session.get(f"{self.base_url}/api/v1/genealogy/stats")
        response.raise_for_status()
        return response.json()
    
    def create_person(self, person_data: Dict[str, Any]) -> Dict[str, Any]:
        """Crée une nouvelle personne."""
        response = self.session.post(
            f"{self.base_url}/api/v1/persons/",
            json=person_data
        )
        response.raise_for_status()
        return response.json()
    
    def get_person(self, person_id: str) -> Dict[str, Any]:
        """Récupère une personne par son ID."""
        response = self.session.get(f"{self.base_url}/api/v1/persons/{person_id}")
        response.raise_for_status()
        return response.json()
    
    def list_persons(self, page: int = 1, size: int = 20) -> Dict[str, Any]:
        """Liste les personnes avec pagination."""
        params = {"page": page, "size": size}
        response = self.session.get(f"{self.base_url}/api/v1/persons/", params=params)
        response.raise_for_status()
        return response.json()
    
    def create_family(self, family_data: Dict[str, Any]) -> Dict[str, Any]:
        """Crée une nouvelle famille."""
        response = self.session.post(
            f"{self.base_url}/api/v1/families/",
            json=family_data
        )
        response.raise_for_status()
        return response.json()
    
    def list_families(self, page: int = 1, size: int = 20) -> Dict[str, Any]:
        """Liste les familles avec pagination."""
        params = {"page": page, "size": size}
        response = self.session.get(f"{self.base_url}/api/v1/families/", params=params)
        response.raise_for_status()
        return response.json()
    
    def import_genealogy_file(self, file_path: str) -> Dict[str, Any]:
        """Importe un fichier généalogique."""
        with open(file_path, 'rb') as f:
            files = {'file': f}
            response = self.session.post(
                f"{self.base_url}/api/v1/genealogy/import",
                files=files
            )
        response.raise_for_status()
        return response.json()


def main():
    """Fonction principale de démonstration."""
    print("🚀 Démonstration de l'API GeneWeb-py")
    print("=" * 50)
    
    # Initialisation du client
    client = GeneWebAPIClient()
    
    try:
        # Vérification de l'état de santé
        print("1. Vérification de l'état de santé...")
        health = client.health_check()
        print(f"   ✅ API Status: {health['status']}")
        print(f"   📋 Version: {health['version']}")
        print()
        
        # Statistiques initiales
        print("2. Statistiques initiales...")
        stats = client.get_stats()
        data = stats['data']
        print(f"   👥 Personnes: {data['total_persons']}")
        print(f"   👨‍👩‍👧‍👦 Familles: {data['total_families']}")
        print(f"   📅 Événements: {data['total_events']}")
        print()
        
        # Création d'une personne
        print("3. Création d'une personne...")
        person_data = {
            "first_name": "Jean",
            "surname": "DUPONT",
            "public_name": "Jean DUPONT",
            "sex": "m",
            "access_level": "apubl"
        }
        
        person_result = client.create_person(person_data)
        person_id = person_result['data']['id']
        print(f"   ✅ Personne créée avec l'ID: {person_id}")
        print(f"   📝 Nom: {person_result['data']['first_name']} {person_result['data']['surname']}")
        print()
        
        # Récupération de la personne
        print("4. Récupération de la personne...")
        person = client.get_person(person_id)
        print(f"   ✅ Personne récupérée: {person['data']['first_name']} {person['data']['surname']}")
        print(f"   🚻 Sexe: {person['data']['sex']}")
        print()
        
        # Liste des personnes
        print("5. Liste des personnes...")
        persons_list = client.list_persons()
        print(f"   ✅ {len(persons_list['items'])} personne(s) trouvée(s)")
        for person_item in persons_list['items']:
            print(f"   - {person_item['first_name']} {person_item['surname']} ({person_item['id']})")
        print()
        
        # Création d'une famille
        print("6. Création d'une famille...")
        family_data = {
            "husband_id": person_id,
            "wife_id": None,
            "children": [],
            "marriage_status": "nm",  # Non marié pour l'exemple
            "notes": ["Famille créée via l'API"],
            "sources": []
        }
        
        family_result = client.create_family(family_data)
        family_id = family_result['data']['id']
        print(f"   ✅ Famille créée avec l'ID: {family_id}")
        print(f"   👨 Époux: {family_result['data']['husband_id']}")
        print()
        
        # Liste des familles
        print("7. Liste des familles...")
        families_list = client.list_families()
        print(f"   ✅ {len(families_list['items'])} famille(s) trouvée(s)")
        for family_item in families_list['items']:
            print(f"   - Famille {family_item['id']}: {family_item['husband_id']} & {family_item['wife_id']}")
        print()
        
        # Statistiques finales
        print("8. Statistiques finales...")
        final_stats = client.get_stats()
        final_data = final_stats['data']
        print(f"   👥 Personnes: {final_data['total_persons']}")
        print(f"   👨‍👩‍👧‍👦 Familles: {final_data['total_families']}")
        print(f"   📅 Événements: {final_data['total_events']}")
        print()
        
        print("🎉 Démonstration terminée avec succès !")
        print("\n📚 Documentation disponible à:")
        print("   - Swagger UI: http://127.0.0.1:8000/docs")
        print("   - ReDoc: http://127.0.0.1:8000/redoc")
        
    except requests.exceptions.ConnectionError:
        print("❌ Erreur: Impossible de se connecter à l'API.")
        print("   Assurez-vous que le serveur est démarré avec:")
        print("   python run_api.py --host 127.0.0.1 --port 8000")
        
    except requests.exceptions.HTTPError as e:
        print(f"❌ Erreur HTTP: {e}")
        if hasattr(e.response, 'text'):
            print(f"   Détails: {e.response.text}")
            
    except Exception as e:
        print(f"❌ Erreur inattendue: {e}")


if __name__ == "__main__":
    main()
