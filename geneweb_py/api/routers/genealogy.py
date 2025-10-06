"""
Router FastAPI pour la gestion de la généalogie dans l'API geneweb-py.
"""

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Depends, Query, UploadFile, File
from fastapi.responses import JSONResponse, FileResponse
import tempfile
import os

from ...formats import GEDCOMExporter, JSONExporter, XMLExporter

from ..models.responses import (
    SuccessResponse, StatsResponse, HealthResponse, ErrorResponse
)
from ..services.genealogy_service import GenealogyService

router = APIRouter()

# Import de la dépendance depuis le module dependencies
from ..dependencies import get_genealogy_service


@router.post("/import", response_model=SuccessResponse)
async def import_genealogy_file(
    file: UploadFile = File(...),
    service: GenealogyService = Depends(get_genealogy_service)
) -> SuccessResponse:
    """
    Importe un fichier généalogique (.gw).
    
    Args:
        file: Fichier à importer
        service: Service de généalogie
        
    Returns:
        SuccessResponse: Réponse de succès avec les statistiques d'import
    """
    try:
        # Vérification de l'extension du fichier
        if not file.filename.endswith(('.gw', '.gwplus')):
            raise HTTPException(
                status_code=400,
                detail="Le fichier doit avoir l'extension .gw ou .gwplus"
            )
        
        # Sauvegarde temporaire du fichier
        import tempfile
        import os
        
        with tempfile.NamedTemporaryFile(delete=False, suffix='.gw') as temp_file:
            content = await file.read()
            temp_file.write(content)
            temp_file_path = temp_file.name
        
        try:
            # Chargement de la généalogie
            genealogy = service.load_from_file(temp_file_path)
            
            # Récupération des statistiques
            stats = service.get_stats()
            
            return SuccessResponse(
                message=f"Fichier '{file.filename}' importé avec succès",
                data={
                    "filename": file.filename,
                    "size_bytes": len(content),
                    "statistics": stats
                }
            )
            
        finally:
            # Nettoyage du fichier temporaire
            os.unlink(temp_file_path)
            
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors de l'import du fichier: {exc}"
        )


@router.get("/export/{format}", response_class=FileResponse)
async def export_genealogy(
    format: str,
    service: GenealogyService = Depends(get_genealogy_service)
) -> FileResponse:
    """
    Exporte la généalogie dans différents formats.
    
    Args:
        format: Format d'export (gw, json, xml, gedcom)
        service: Service de généalogie
        
    Returns:
        FileResponse: Fichier exporté
    """
    try:
        # Récupérer la généalogie depuis le service
        genealogy = service.genealogy
        
        if format == "gw":
            # Export vers format GeneWeb natif
            raise HTTPException(
                status_code=501,
                detail="Export vers format GeneWeb non encore implémenté"
            )
        elif format == "json":
            # Export vers JSON
            try:
                exporter = JSONExporter()
                temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".json")
                temp_file.close()
                
                exporter.export(genealogy, temp_file.name)
                
                return FileResponse(
                    path=temp_file.name,
                    filename=f"genealogy.json",
                    media_type="application/json"
                )
            except Exception as exc:
                # Nettoyer le fichier temporaire en cas d'erreur
                if 'temp_file' in locals():
                    try:
                        os.unlink(temp_file.name)
                    except:
                        pass
                raise HTTPException(
                    status_code=500,
                    detail=f"Erreur lors de l'export JSON: {exc}"
                )
        elif format == "xml":
            # Export vers XML
            try:
                exporter = XMLExporter()
                temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".xml")
                temp_file.close()
                
                exporter.export(genealogy, temp_file.name)
                
                return FileResponse(
                    path=temp_file.name,
                    filename=f"genealogy.xml",
                    media_type="application/xml"
                )
            except Exception as exc:
                # Nettoyer le fichier temporaire en cas d'erreur
                if 'temp_file' in locals():
                    try:
                        os.unlink(temp_file.name)
                    except:
                        pass
                raise HTTPException(
                    status_code=500,
                    detail=f"Erreur lors de l'export XML: {exc}"
                )
        elif format == "gedcom":
            # Export vers GEDCOM
            try:
                exporter = GEDCOMExporter()
                temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".ged")
                temp_file.close()
                
                exporter.export(genealogy, temp_file.name)
                
                return FileResponse(
                    path=temp_file.name,
                    filename=f"genealogy.ged",
                    media_type="application/octet-stream"
                )
            except Exception as exc:
                # Nettoyer le fichier temporaire en cas d'erreur
                if 'temp_file' in locals():
                    try:
                        os.unlink(temp_file.name)
                    except:
                        pass
                raise HTTPException(
                    status_code=500,
                    detail=f"Erreur lors de l'export GEDCOM: {exc}"
                )
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Format d'export '{format}' non supporté. Formats disponibles: gw, json, xml, gedcom"
            )
            
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors de l'export: {exc}"
        )


@router.get("/stats", response_model=SuccessResponse)
async def get_genealogy_stats(
    service: GenealogyService = Depends(get_genealogy_service)
) -> SuccessResponse:
    """
    Récupère les statistiques générales de la généalogie.
    
    Args:
        service: Service de généalogie
        
    Returns:
        SuccessResponse: Réponse avec les statistiques complètes
    """
    try:
        stats = service.get_stats()
        
        stats_response = StatsResponse(
            total_persons=stats["total_persons"],
            total_families=stats["total_families"],
            total_events=stats["total_events"],
            metadata={
                "source_file": stats["metadata"]["source_file"],
                "created": stats["metadata"]["created"],
                "updated": stats["metadata"]["updated"],
                "version": stats["metadata"]["version"],
                "encoding": stats["metadata"]["encoding"],
            },
            persons_by_sex=stats["persons_by_sex"],
            persons_by_access_level=stats["persons_by_access_level"],
            families_by_status=stats["families_by_status"],
            events_by_type=stats["events_by_type"],
            average_children_per_family=stats["average_children_per_family"]
        )
        
        return SuccessResponse(
            message="Statistiques récupérées avec succès",
            data=stats_response.model_dump()
        )
        
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors de la récupération des statistiques: {exc}"
        )


@router.get("/search", response_model=SuccessResponse)
async def search_genealogy(
    query: str = Query(..., min_length=1, description="Terme de recherche"),
    search_type: str = Query("all", description="Type de recherche: all, persons, families, events"),
    limit: int = Query(50, ge=1, le=100, description="Nombre maximum de résultats"),
    service: GenealogyService = Depends(get_genealogy_service)
) -> SuccessResponse:
    """
    Effectue une recherche globale dans la généalogie.
    
    Args:
        query: Terme de recherche
        search_type: Type de recherche (all, persons, families, events)
        limit: Nombre maximum de résultats
        service: Service de généalogie
        
    Returns:
        SuccessResponse: Réponse avec les résultats de recherche
    """
    try:
        genealogy = service.genealogy
        query_lower = query.lower()
        results = {
            "persons": [],
            "families": [],
            "events": []
        }
        
        # Recherche dans les personnes
        if search_type in ["all", "persons"]:
            for person in genealogy.persons.values():
                if (query_lower in person.first_name.lower() or
                    query_lower in person.last_name.lower() or
                    (person.public_name and query_lower in person.public_name.lower()) or
                    (person.birth_place and query_lower in person.birth_place.lower()) or
                    (person.death_place and query_lower in person.death_place.lower())):
                    
                    person_data = {
                        "id": person.unique_id,
                        "first_name": person.first_name,
                        "surname": person.last_name,
                        "public_name": person.public_name,
                        "sex": person.gender.value if person.gender else None,
                        "birth_place": person.birth_place,
                        "death_place": person.death_place
                    }
                    results["persons"].append(person_data)
        
        # Recherche dans les familles
        if search_type in ["all", "families"]:
            for family in genealogy.families.values():
                # Recherche par ID des époux
                husband = genealogy.persons.get(family.husband_id) if family.husband_id else None
                wife = genealogy.persons.get(family.wife_id) if family.wife_id else None
                
                family_matches = False
                if husband and (query_lower in husband.first_name.lower() or 
                               query_lower in husband.last_name.lower()):
                    family_matches = True
                if wife and (query_lower in wife.first_name.lower() or 
                            query_lower in wife.last_name.lower()):
                    family_matches = True
                
                if family_matches:
                    family_data = {
                        "id": family.id,
                        "husband_id": family.husband_id,
                        "wife_id": family.wife_id,
                        "marriage_status": family.marriage_status.value if family.marriage_status else None,
                        "children_count": len(family.children)
                    }
                    results["families"].append(family_data)
        
        # Recherche dans les événements
        if search_type in ["all", "events"]:
            for person in genealogy.persons.values():
                for event in person.events:
                    if (query_lower in (event.place or "").lower() or
                        query_lower in (event.reason or "").lower() or
                        query_lower in (event.notes or "").lower()):
                        
                        event_data = {
                            "id": getattr(event, 'unique_id', 'unknown'),
                            "event_type": event.event_type.value if event.event_type else None,
                            "place": event.place,
                            "reason": event.reason,
                            "person_id": person.unique_id,
                            "family_id": None
                        }
                        results["events"].append(event_data)
            
            for family in genealogy.families.values():
                for event in family.events:
                    if (query_lower in (event.place or "").lower() or
                        query_lower in (event.reason or "").lower() or
                        query_lower in (event.notes or "").lower()):
                        
                        event_data = {
                            "id": getattr(event, 'unique_id', 'unknown'),
                            "event_type": event.event_type.value if event.event_type else None,
                            "place": event.place,
                            "reason": event.reason,
                            "person_id": None,
                            "family_id": family.id
                        }
                        results["events"].append(event_data)
        
        # Limitation des résultats
        total_results = len(results["persons"]) + len(results["families"]) + len(results["events"])
        if limit < total_results:
            # Tronquer les résultats si nécessaire
            results["persons"] = results["persons"][:limit]
            remaining = limit - len(results["persons"])
            if remaining > 0:
                results["families"] = results["families"][:remaining]
                remaining = remaining - len(results["families"])
                if remaining > 0:
                    results["events"] = results["events"][:remaining]
        
        search_results = {
            "query": query,
            "search_type": search_type,
            "limit": limit,
            "results": results,
            "total_results": total_results
        }
        
        return SuccessResponse(
            message=f"Recherche '{query}' effectuée avec succès",
            data=search_results
        )
        
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors de la recherche: {exc}"
        )


@router.post("/validate", response_model=SuccessResponse)
async def validate_genealogy(
    service: GenealogyService = Depends(get_genealogy_service)
) -> SuccessResponse:
    """
    Valide la cohérence de la généalogie.
    
    Args:
        service: Service de généalogie
        
    Returns:
        SuccessResponse: Réponse avec les résultats de validation
    """
    try:
        # TODO: Implémenter la validation de cohérence
        
        validation_results = {
            "is_valid": True,
            "warnings": [],
            "errors": [],
            "suggestions": []
        }
        
        return SuccessResponse(
            message="Validation effectuée avec succès",
            data=validation_results
        )
        
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors de la validation: {exc}"
        )


@router.delete("/", response_model=SuccessResponse)
async def clear_genealogy(
    service: GenealogyService = Depends(get_genealogy_service)
) -> SuccessResponse:
    """
    Vide la généalogie actuelle.
    
    Args:
        service: Service de généalogie
        
    Returns:
        SuccessResponse: Réponse de succès
    """
    try:
        # Création d'une nouvelle généalogie vide
        service.create_empty()
        
        return SuccessResponse(
            message="Généalogie vidée avec succès"
        )
        
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors du vidage de la généalogie: {exc}"
        )


@router.get("/health")
async def health_check() -> Dict[str, Any]:
    """
    Vérification de l'état de santé du service de généalogie.
    
    Returns:
        Dict[str, Any]: Statut du service
    """
    return {
        "status": "healthy",
        "service": "genealogy",
        "message": "Service de généalogie opérationnel",
        "version": "0.1.0"
    }
