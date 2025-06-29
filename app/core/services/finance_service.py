# gmao_app/app/core/services/finance_service.py
""" 
Service pour la gestion financière et les calculs de coûts.
Implémente la Phase 11 de la roadmap technique (Gestion Financière & Coûts).
"""
import logging
from decimal import Decimal
from typing import Dict, List, Optional, Tuple, Any

from app.core.models.maintenance import Maintenance
from app.core.models.maintenance_intervenant import MaintenanceIntervenant
from app.core.models.maintenance_frais_externe import MaintenanceFraisExterne
from app.core.models.intervention_piece import InterventionPiece
from app.core.models.piece import Piece

from app.data.repositories.maintenance_repository import MaintenanceRepository
from app.data.repositories.maintenance_intervenant_repository import MaintenanceIntervenantRepository
from app.data.repositories.maintenance_frais_externe_repository import MaintenanceFraisExterneRepository
from app.data.repositories.intervention_piece_repository import InterventionPieceRepository
from app.data.repositories.piece_repository import PieceRepository

logger = logging.getLogger(__name__)

class FinanceService:
    """
    Service responsable des calculs financiers liés aux maintenances.
    Calcule les coûts des interventions à partir des différentes sources:
    - Main d'œuvre (intervenants internes et externes)
    - Pièces du stock interne
    - Frais externes (pièces hors stock, déplacements, sous-traitance, etc.)
    """
    
    def __init__(self, 
                 maintenance_repo: Optional[MaintenanceRepository] = None,
                 intervenant_repo: Optional[MaintenanceIntervenantRepository] = None,
                 frais_repo: Optional[MaintenanceFraisExterneRepository] = None,
                 intervention_piece_repo: Optional[InterventionPieceRepository] = None,
                 piece_repo: Optional[PieceRepository] = None):
        """Initialise le service avec les repositories nécessaires"""
        self.maintenance_repo = maintenance_repo or MaintenanceRepository()
        self.intervenant_repo = intervenant_repo or MaintenanceIntervenantRepository()
        self.frais_repo = frais_repo or MaintenanceFraisExterneRepository()
        self.intervention_piece_repo = intervention_piece_repo or InterventionPieceRepository()
        self.piece_repo = piece_repo or PieceRepository()
    
    def calculer_couts_maintenance(self, maintenance_id: int) -> Dict[str, float]:
        """
        Calcule tous les coûts associés à une maintenance et met à jour l'enregistrement.
        Retourne un dictionnaire avec le détail des coûts calculés.
        """
        # Récupération de la maintenance
        maintenance = self.maintenance_repo.get_by_id(maintenance_id)
        if not maintenance:
            logger.error(f"Impossible de calculer les coûts: Maintenance ID {maintenance_id} non trouvée")
            return {}
        
        # 1. Calcul du coût de main d'œuvre
        cout_main_oeuvre = self._calculer_cout_main_oeuvre(maintenance_id)
        
        # 2. Calcul du coût des pièces internes
        cout_pieces_internes = self._calculer_cout_pieces_internes(maintenance_id)
        
        # 3. Calcul du coût des pièces externes et autres frais
        cout_pieces_externes, cout_autres_frais = self._calculer_couts_frais_externes(maintenance_id)
        
        # 4. Calcul du coût total
        cout_total = cout_main_oeuvre + cout_pieces_internes + cout_pieces_externes + cout_autres_frais
        
        # Préparation des données financières à mettre à jour
        financial_data = {
            'cout_main_oeuvre': cout_main_oeuvre,
            'cout_pieces_internes': cout_pieces_internes,
            'cout_pieces_externes': cout_pieces_externes,
            'cout_autres_frais': cout_autres_frais,
            'cout_total': cout_total
        }
        
        # Mise à jour des données financières dans la base de données
        success = self.maintenance_repo.update_financial_data(maintenance_id, financial_data)
        
        if success:
            logger.info(f"Données financières de la maintenance {maintenance_id} mises à jour avec succès")
        else:
            logger.warning(f"Échec de la mise à jour des données financières pour la maintenance {maintenance_id}")
        
        return financial_data
    
    def _calculer_cout_main_oeuvre(self, maintenance_id: int) -> float:
        """Calcule le coût total de la main d'œuvre pour une maintenance"""
        intervenants = self.intervenant_repo.get_by_maintenance_id(maintenance_id)
        total = sum(intervenant.cout_total for intervenant in intervenants)
        logger.debug(f"Maintenance {maintenance_id}: Coût main d'œuvre calculé = {total:.2f}")
        return round(total, 2)
    
    def _calculer_cout_pieces_internes(self, maintenance_id: int) -> float:
        """Calcule le coût total des pièces du stock interne utilisées"""
        # Récupération des pièces utilisées dans l'intervention
        interventions_pieces = self.intervention_piece_repo.get_by_maintenance_id(maintenance_id)
        
        total = 0.0
        for ip in interventions_pieces:
            # Récupération des informations de la pièce
            piece = self.piece_repo.get_by_id(ip.piece_id)
            if piece:
                cout_piece = piece.prix_unitaire * ip.quantite
                total += cout_piece
                logger.debug(f"Pièce {piece.reference}: {ip.quantite} x {piece.prix_unitaire:.2f} = {cout_piece:.2f}")
        
        logger.debug(f"Maintenance {maintenance_id}: Coût pièces internes calculé = {total:.2f}")
        return round(total, 2)
    
    def _calculer_couts_frais_externes(self, maintenance_id: int) -> Tuple[float, float]:
        """
        Calcule les coûts des frais externes, séparés en:
        - Pièces externes (type_frais = 'PIECE_EXTERNE')
        - Autres frais (autres types)
        Retourne un tuple (cout_pieces_externes, cout_autres_frais)
        """
        frais_externes = self.frais_repo.get_by_maintenance_id(maintenance_id)
        
        cout_pieces_externes = 0.0
        cout_autres_frais = 0.0
        
        for frais in frais_externes:
            # Calculer le montant total de ce frais (montant * quantité)
            montant_total = frais.montant_total
            
            # Classer selon le type de frais
            if frais.type_frais == 'PIECE_EXTERNE':
                cout_pieces_externes += montant_total
            else:
                cout_autres_frais += montant_total
        
        logger.debug(f"Maintenance {maintenance_id}: Coût pièces externes calculé = {cout_pieces_externes:.2f}")
        logger.debug(f"Maintenance {maintenance_id}: Coût autres frais calculé = {cout_autres_frais:.2f}")
        
        return round(cout_pieces_externes, 2), round(cout_autres_frais, 2)
    
    def get_resume_couts_maintenance(self, maintenance_id: int) -> Dict[str, Any]:
        """
        Récupère un résumé détaillé des coûts d'une maintenance avec ventilation.
        Utile pour l'affichage dans les interfaces ou rapports.
        """
        # Récupération de la maintenance
        maintenance = self.maintenance_repo.get_by_id(maintenance_id)
        if not maintenance:
            logger.error(f"Maintenance ID {maintenance_id} non trouvée")
            return {}
        
        # Récupération des détails
        intervenants = self.intervenant_repo.get_by_maintenance_id(maintenance_id)
        frais_externes = self.frais_repo.get_by_maintenance_id(maintenance_id)
        interventions_pieces = self.intervention_piece_repo.get_by_maintenance_id(maintenance_id)
        
        # Préparation des pièces avec détails
        pieces_details = []
        for ip in interventions_pieces:
            piece = self.piece_repo.get_by_id(ip.piece_id)
            if piece:
                pieces_details.append({
                    'reference': piece.reference,
                    'nom': piece.nom,
                    'quantite': ip.quantite,
                    'prix_unitaire': piece.prix_unitaire,
                    'cout_total': piece.prix_unitaire * ip.quantite
                })
        
        # Création du résumé
        resume = {
            'maintenance_id': maintenance_id,
            'ot_id': maintenance.ot_id,
            'cout_total': maintenance.cout_total or 0.0,
            'ventilation': {
                'main_oeuvre': {
                    'total': maintenance.cout_main_oeuvre or 0.0,
                    'details': [
                        {
                            'id_intervenant': i.id_intervenant,
                            'nom': i.nom_intervenant_externe if i.nom_intervenant_externe else f"Technicien {i.technicien_id}",
                            'technicien_id': i.technicien_id,  # Pour identifier si interne/externe
                            'heures': i.heures_travaillees,
                            'cout_horaire': i.cout_horaire,
                            'cout_total': i.cout_total
                        } for i in intervenants
                    ]
                },
                'pieces_internes': {
                    'total': maintenance.cout_pieces_internes or 0.0,
                    'details': pieces_details
                },
                'frais_externes': {
                    'pieces_externes': {
                        'total': maintenance.cout_pieces_externes or 0.0,
                        'details': [
                            {
                                'frais_id': f.id_frais,
                                'description': f.description,
                                'montant': f.montant,
                                'quantite': f.quantite,
                                'montant_total': f.montant_total,
                                'fournisseur': getattr(f, 'fournisseur', '') if hasattr(f, 'fournisseur') else ''
                            } for f in frais_externes if f.type_frais == 'PIECE_EXTERNE'
                        ]
                    },
                    'autres_frais': {
                        'total': maintenance.cout_autres_frais or 0.0,
                        'details': [
                            {
                                'frais_id': f.id_frais,
                                'type': f.type_frais,
                                'description': f.description,
                                'montant': f.montant,
                                'quantite': f.quantite,
                                'montant_total': f.montant_total,
                                'fournisseur': getattr(f, 'fournisseur', '') if hasattr(f, 'fournisseur') else ''
                            } for f in frais_externes if f.type_frais != 'PIECE_EXTERNE'
                        ]
                    }
                }
            }
        }
        
        return resume