# gmao_app/app/data/repositories/machine_repository.py
""" Repository pour l'entité Machine. """
import logging
import psycopg2
from typing import Optional, List, Dict, Any
from app.data.database import execute_query, fetch_one, fetch_all, DatabaseError
from app.core.models.machine import Machine
from datetime import date

logger = logging.getLogger(__name__)

class MachineRepository:

    def _format_date(self, d: Optional[date]) -> Optional[str]:
        """ Formate une date en string ISO ou retourne None. """
        return d.isoformat() if d else None

    def add(self, machine: Machine) -> Optional[int]:
        """ Ajoute une nouvelle machine. Retourne son ID. """
        sql = """
            INSERT INTO MACHINE (
                nom, serial, modele, date_installation, localisation, etat,
                informations_techniques, type_machine_id, site_id, fabricant_id,
                parent_machine_id, criticite, garantie_fin
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id_machine
        """
        params = (
            machine.nom, machine.serial, machine.modele,
            self._format_date(machine.date_installation), machine.localisation, machine.etat,
            machine.informations_techniques, machine.type_machine_id, machine.site_id, machine.fabricant_id,
            machine.parent_machine_id, machine.criticite, self._format_date(machine.garantie_fin)
        )
        try:
            row = fetch_one(sql, params)
            new_id = row['id_machine'] if row else None
            logger.info(f"Machine '{machine.nom}' ajoutée avec ID: {new_id}")
            return new_id
        except psycopg2.IntegrityError as e:
            # Identifier quelle contrainte a échoué
            if 'MACHINE.serial' in str(e):
                logger.warning(f"Erreur ajout Machine '{machine.nom}'. Numéro série '{machine.serial}' existe déjà: {e}")
                raise DatabaseError(f"Le numéro de série '{machine.serial}' est déjà utilisé.") from e
            elif 'FOREIGN KEY constraint failed' in str(e):
                 logger.error(f"Erreur ajout Machine '{machine.nom}'. Clé étrangère invalide (Site/Fabricant/Type/Parent%s): {e}")
                 raise DatabaseError("Référence invalide vers Site, Fabricant, Type ou Machine Parent.") from e
            else:
                logger.warning(f"Erreur ajout Machine '{machine.nom}'. Contrainte d'intégrité: {e}")
                raise DatabaseError("Erreur d'intégrité lors de l'ajout de la machine.") from e
        except DatabaseError as e:
            logger.error(f"Erreur DB ajout Machine '{machine.nom}': {e}")
            raise

    def get_by_id(self, machine_id: int) -> Optional[Machine]:
        """ Récupère une machine par son ID. """
        sql = "SELECT * FROM MACHINE WHERE id_machine = %s"
        try:
            row = fetch_one(sql, (machine_id,))
            return Machine.from_db_row(row)
        except DatabaseError as e:
            logger.error(f"Erreur DB get_by_id machine {machine_id}: {e}")
            raise

    def get_by_serial(self, serial: str) -> Optional[Machine]:
        """ Récupère une machine par son numéro de série (si unique). """
        if not serial: return None
        sql = "SELECT * FROM MACHINE WHERE serial = %s"
        try:
            row = fetch_one(sql, (serial,))
            return Machine.from_db_row(row)
        except DatabaseError as e:
            logger.error(f"Erreur DB get_by_serial machine '{serial}': {e}")
            raise

    def get_all(self, filters: Optional[Dict[str, Any]] = None,
                sort_by: str = "nom", sort_desc: bool = False) -> List[Machine]:
        """
        Récupère toutes les machines, avec filtres et tri optionnels.
        Exemple filters: {'site_id': 1, 'etat': 'En service'}
        """
        sql = "SELECT m.* FROM MACHINE m " # Utiliser alias pour futures jointures
        where_clauses = []
        params = []

        # Construire la clause WHERE dynamiquement
        if filters:
            for key, value in filters.items():
                 # S'assurer que la clé est un champ valide pour éviter injection
                 # TODO: Valider les clés de filtre
                 if key in ['id_machine', 'nom', 'serial', 'modele', 'localisation', 'etat',
                            'type_machine_id', 'site_id', 'fabricant_id', 'parent_machine_id', 'criticite']:
                      if value is not None:
                           if isinstance(value, str) and '%' in value:
                                where_clauses.append(f"m.{key} LIKE %s")
                                params.append(value)
                           else:
                                where_clauses.append(f"m.{key} = %s")
                                params.append(value)
                 # Ajouter des jointures ici si on filtre sur nom site, etc.

        if where_clauses:
            sql += " WHERE " + " AND ".join(where_clauses)

        # Ajouter le tri
        # TODO: Valider sort_by pour éviter injection
        valid_sort_columns = ['id_machine', 'nom', 'serial', 'modele', 'etat', 'criticite', 'date_installation', 'garantie_fin', 'created_at']
        if sort_by in valid_sort_columns:
             order = "DESC" if sort_desc else "ASC"
             sql += f" ORDER BY m.{sort_by} {order}"
        else:
             sql += f" ORDER BY m.nom ASC" # Tri par défaut

        try:
            logger.debug(f"Executing get_all machines: SQL={sql} PARAMS={params}")
            rows = fetch_all(sql, tuple(params))
            return [Machine.from_db_row(row) for row in rows if row]
        except DatabaseError as e:
            logger.error(f"Erreur DB get_all machines (filters={filters}, sort={sort_by}): {e}")
            raise

    def update(self, machine: Machine) -> bool:
        """ Met à jour une machine existante. """
        if machine.id_machine is None: return False
        sql = """
            UPDATE MACHINE SET
                nom = %s, serial = %s, modele = %s, date_installation = %s, localisation = %s, etat = %s,
                informations_techniques = %s, type_machine_id = %s, site_id = %s, fabricant_id = %s,
                parent_machine_id = %s, criticite = %s, garantie_fin = %s
            WHERE id_machine = %s
        """
        params = (
            machine.nom, machine.serial, machine.modele,
            self._format_date(machine.date_installation), machine.localisation, machine.etat,
            machine.informations_techniques, machine.type_machine_id, machine.site_id, machine.fabricant_id,
            machine.parent_machine_id, machine.criticite, self._format_date(machine.garantie_fin),
            machine.id_machine
        )
        try:
            cursor = execute_query(sql, params)
            success = cursor.rowcount > 0
            if success: logger.info(f"Machine ID {machine.id_machine} mise à jour.")
            return success
        except psycopg2.IntegrityError as e:
             if 'MACHINE.serial' in str(e):
                logger.warning(f"Erreur màj Machine ID {machine.id_machine}. Numéro série '{machine.serial}' existe déjà: {e}")
                raise DatabaseError(f"Le numéro de série '{machine.serial}' est déjà utilisé par une autre machine.") from e
             elif 'FOREIGN KEY constraint failed' in str(e):
                 logger.error(f"Erreur màj Machine ID {machine.id_machine}. Clé étrangère invalide: {e}")
                 raise DatabaseError("Référence invalide vers Site, Fabricant, Type ou Machine Parent lors de la mise à jour.") from e
             else:
                logger.warning(f"Erreur màj Machine ID {machine.id_machine}. Contrainte d'intégrité: {e}")
                raise DatabaseError("Erreur d'intégrité lors de la mise à jour de la machine.") from e
        except DatabaseError as e:
            logger.error(f"Erreur DB update machine ID {machine.id_machine}: {e}")
            raise

    def delete(self, machine_id: int) -> bool:
        """ Supprime une machine. """
        # Attention aux enfants et aux FK dans d'autres tables (OT, Maintenance, Compteur...)
        # Par défaut, les FK ON DELETE RESTRICT empêcheront la suppression si des OT/Maintenance existent.
        # La FK parent_machine_id est ON DELETE SET NULL
        sql = "DELETE FROM MACHINE WHERE id_machine = %s"
        try:
            cursor = execute_query(sql, (machine_id,))
            success = cursor.rowcount > 0
            if success: logger.info(f"Machine ID {machine_id} supprimée.")
            return success
        except psycopg2.IntegrityError as e:
             logger.error(f"Impossible de supprimer Machine ID {machine_id}. Elle est référencée ailleurs (OT, Maintenance, Enfants...): {e}")
             raise DatabaseError(f"Impossible de supprimer cette machine car elle est référencée par des Ordres de Travail, des Maintenances ou d'autres machines (enfants).") from e
        except DatabaseError as e:
            logger.error(f"Erreur DB delete machine ID {machine_id}: {e}")
            raise

    # --- Méthodes spécifiques optionnelles ---
    def get_children(self, parent_id: int) -> List[Machine]:
        """ Récupère les machines enfants directes d'une machine parent. """
        return self.get_all(filters={'parent_machine_id': parent_id})

    def get_machines_by_site(self, site_id: int) -> List[Machine]:
         """ Récupère toutes les machines d'un site donné. """
         return self.get_all(filters={'site_id': site_id})

    # Ajouter d'autres méthodes get_by... si nécessaire