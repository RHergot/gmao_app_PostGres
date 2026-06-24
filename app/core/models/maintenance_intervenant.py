# gmao_app/app/core/models/maintenance_intervenant.py
""" 
Modèle pour l'entité MaintenanceIntervenant - gestion des intervenants (techniciens internes ou externes)
sur une maintenance donnée.
"""
from dataclasses import dataclass
from typing import Any,  Dict,  Union,  Optional
import logging

logger = logging.getLogger(__name__)

@dataclass
class MaintenanceIntervenant:
    """ 
    Représente un intervenant (interne ou externe) ayant travaillé sur une maintenance.
    Permet de suivre le temps passé et le coût horaire pour chaque personne.
    """
    maintenance_id: int          # FK vers Maintenance
    heures_travaillees: float    # Temps passé en heures
    cout_horaire: float          # Coût horaire de l'intervenant
    technicien_id: Optional[int] = None  # FK vers Technicien (nullable si externe)
    nom_intervenant_externe: Optional[str] = None  # Nom de l'intervenant externe
    notes: Optional[str] = None  # Notes éventuelles
    id_intervenant: Optional[int] = None  # PK
    created_at: Optional[str] = None  # Date de création

    def __post_init__(self):
        """Validation après initialisation"""
        if not self.technicien_id and not self.nom_intervenant_externe:
            raise ValueError("Un intervenant doit être soit un technicien interne, soit un intervenant externe nommé")
        if self.heures_travaillees <= 0:
            raise ValueError("Les heures travaillées doivent être positives")
        if self.cout_horaire < 0:
            raise ValueError("Le coût horaire ne peut pas être négatif")

    @property
    def cout_total(self) -> float:
        """Calcule le coût total de cet intervenant pour la maintenance"""
        return self.heures_travaillees * self.cout_horaire

    @classmethod
    def from_db_row(cls, row: Optional[Union[Dict[str, Any], Any]]) -> Optional['MaintenanceIntervenant']:
        """Crée une instance à partir d'une ligne de base de données"""
        if row is None:
            return None
        try:
            return cls(
                id_intervenant=row['id_intervenant'],
                maintenance_id=row['maintenance_id'],
                technicien_id=row['technicien_id'],  # Peut être NULL
                nom_intervenant_externe=row['nom_intervenant_externe'],  # Peut être NULL
                heures_travaillees=float(row['heures_travaillees']),
                cout_horaire=float(row['cout_horaire']),
                notes=row['notes'],
                created_at=row['created_at']
            )
        except KeyError as e:
            logger.error(f"Clé manquante '{e}' dans MaintenanceIntervenant. Keys: {row.keys()}")
            return None
        except (ValueError, TypeError) as e:
            logger.error(f"Erreur de conversion de type dans MaintenanceIntervenant ID {row.get('id_intervenant', 'N/A')}: {e}", exc_info=True)
            return None
        except Exception as e:
            logger.error(f"Erreur inattendue lors de la création de MaintenanceIntervenant ID {row.get('id_intervenant', 'N/A')}: {e}", exc_info=True)
            return None
