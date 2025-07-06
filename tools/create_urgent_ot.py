#!/usr/bin/env python3
"""
Test pour créer un OT avec priorité Urgente pour tester le filtre.
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.services.maintenance_service import MaintenanceService, OT_PRIORITES
from app.data.repositories import OrdreTravailRepository, MaintenanceRepository, TechnicienRepository, EquipeRepository, InterventionPieceRepository, MaintenanceIntervenantRepository, MaintenanceFraisExterneRepository, PieceRepository, FournisseurRepository, MouvementStockRepository, MachineRepository
from app.core.services.stock_service import StockService
from datetime import datetime, timedelta

def create_urgent_ot():
    """Créer un OT avec priorité Urgente pour tester le filtre."""
    
    try:
        # Repositories
        ot_repo = OrdreTravailRepository()
        maintenance_repo = MaintenanceRepository()
        tech_repo = TechnicienRepository()
        equipe_repo = EquipeRepository()
        intervention_piece_repo = InterventionPieceRepository()
        maintenance_intervenant_repo = MaintenanceIntervenantRepository()
        maintenance_frais_externe_repo = MaintenanceFraisExterneRepository()
        
        # Stock service (requis) - Utiliser les repos disponibles
        piece_repo = PieceRepository()
        fournisseur_repo = FournisseurRepository()
        mouvement_stock_repo = MouvementStockRepository()
        stock_service = StockService(piece_repo, fournisseur_repo, mouvement_stock_repo)
        
        # Récupérer une machine existante directement via le repository
        machine_repo = MachineRepository()
        machines = machine_repo.get_all()
        if not machines:
            print("Aucune machine trouvée dans la base")
            return
        
        first_machine = machines[0]
        print(f"Machine trouvée: {first_machine.nom} (ID: {first_machine.id_machine})")
        
        # Service de maintenance
        maintenance_service = MaintenanceService(
            ot_repo, maintenance_repo, tech_repo, equipe_repo,
            machine_repo,  # MachineRepository pour les vérifications
            intervention_piece_repo, stock_service,
            maintenance_intervenant_repo, maintenance_frais_externe_repo
        )
        
        # Données pour créer un OT urgent
        ot_data = {
            'machine_id': first_machine.id_machine,
            'type': 'Correctif',
            'priorite': 'Urgente',  # Priorité urgente !
            'statut': 'Créé',
            'description': 'Test OT Urgent pour vérifier le filtre UrgentOnly',
            'date_prevue': datetime.now() + timedelta(days=1),
            'utilisateur_createur_id': 1  # ID utilisateur par défaut
        }
        
        print("\n=== Création OT Urgent ===")
        print(f"Données: {ot_data}")
        
        # Créer l'OT
        new_ot = maintenance_service.create_ot(ot_data)
        print(f"OT créé avec succès: ID {new_ot.id_ot}, Numéro: {new_ot.numero_ot}")
        print(f"Priorité: {new_ot.priorite}")
        
        # Vérifier que le filtre fonctionne maintenant
        print("\n=== Test filtre après création ===")
        urgent_ots = maintenance_service.get_all_ots(filters={'priorite': 'Urgente'})
        print(f"OTs avec priorité 'Urgente': {len(urgent_ots)}")
        
        if urgent_ots:
            for ot in urgent_ots:
                print(f"  - OT {ot.id_ot}: {ot.numero_ot} - Priorité: {ot.priorite}")
        
        return new_ot.id_ot
        
    except Exception as e:
        print(f"Erreur: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    ot_id = create_urgent_ot()
    if ot_id:
        print(f"\nOT urgent créé avec l'ID: {ot_id}")
        print("Vous pouvez maintenant tester le filtre UrgentOnly dans l'interface.")
