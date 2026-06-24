# gmao_app/app/data/repositories/type_machine_repository.py
""" Repository pour l'entité TypeMachine. """
import logging
import psycopg2
from typing import Optional, List
from app.data.database import execute_query, fetch_one, fetch_all, DatabaseError
from app.core.models.type_machine import TypeMachine

logger = logging.getLogger(__name__)

class TypeMachineRepository:

    def add(self, type_machine: TypeMachine) -> Optional[int]:
        """ Ajoute un nouveau type de machine. Retourne son ID. """
        sql = "INSERT INTO TYPE_MACHINE (nom, description, categorie) VALUES (%s, %s, %s) RETURNING id_type_machine"
        params = (type_machine.nom, type_machine.description, type_machine.categorie)
        try:
            row = fetch_one(sql, params)
            new_id = row.get("id_type_machine") if row else None
            logger.info(f"TypeMachine '{type_machine.nom}' ajouté avec ID: {new_id}")
            return new_id
        except psycopg2.IntegrityError as e:
            logger.warning(f"Impossible d'ajouter TypeMachine '{type_machine.nom}'. Contrainte unique 'nom'? {e}")
            raise DatabaseError(f"Le nom de type machine '{type_machine.nom}' existe déjà.") from e
        except DatabaseError as e:
            logger.error(f"Erreur DB ajout TypeMachine '{type_machine.nom}': {e}")
            raise

    def get_by_id(self, type_machine_id: int) -> Optional[TypeMachine]:
        """ Récupère un type de machine par son ID. """
        sql = "SELECT * FROM TYPE_MACHINE WHERE id_type_machine = %s"
        try:
            row = fetch_one(sql, (type_machine_id,))
            return TypeMachine.from_db_row(row)
        except DatabaseError as e:
            logger.error(f"Erreur DB get_by_id TypeMachine {type_machine_id}: {e}")
            raise

    def get_by_name(self, name: str) -> Optional[TypeMachine]:
        """ Récupère un type de machine par son nom (unique). """
        sql = "SELECT * FROM TYPE_MACHINE WHERE nom = %s"
        try:
            row = fetch_one(sql, (name,))
            return TypeMachine.from_db_row(row)
        except DatabaseError as e:
            logger.error(f"Erreur DB get_by_name TypeMachine '{name}': {e}")
            raise

    def get_all(self) -> List[TypeMachine]:
        """ Récupère tous les types de machine. """
        sql = "SELECT * FROM TYPE_MACHINE ORDER BY categorie, nom"
        try:
            rows = fetch_all(sql)
            return [TypeMachine.from_db_row(row) for row in rows if row]
        except DatabaseError as e:
            logger.error(f"Erreur DB get_all TypeMachine: {e}")
            raise

    def update(self, type_machine: TypeMachine) -> bool:
        """ Met à jour un type de machine existant. """
        if type_machine.id_type_machine is None: return False
        sql = """UPDATE TYPE_MACHINE SET nom = %s, description = %s, categorie = %s
                 WHERE id_type_machine = %s"""
        params = (type_machine.nom, type_machine.description, type_machine.categorie, type_machine.id_type_machine)
        try:
            cursor = execute_query(sql, params)
            success = cursor.rowcount > 0
            if success: logger.info(f"TypeMachine ID {type_machine.id_type_machine} mis à jour.")
            return success
        except psycopg2.IntegrityError as e:
            logger.warning(f"Échec màj TypeMachine ID {type_machine.id_type_machine}. Contrainte unique 'nom'? {e}")
            raise DatabaseError(f"Le nom de type machine '{type_machine.nom}' est déjà utilisé.") from e
        except DatabaseError as e:
            logger.error(f"Erreur DB update TypeMachine ID {type_machine.id_type_machine}: {e}")
            raise

    def delete(self, type_machine_id: int) -> bool:
        """ Supprime un type de machine. """
        # La contrainte FK sur MACHINE est ON DELETE RESTRICT
        sql = "DELETE FROM TYPE_MACHINE WHERE id_type_machine = %s"
        try:
            cursor = execute_query(sql, (type_machine_id,))
            success = cursor.rowcount > 0
            if success: logger.info(f"TypeMachine ID {type_machine_id} supprimé.")
            return success
        except psycopg2.IntegrityError as e:
            logger.error(f"Impossible de supprimer TypeMachine ID {type_machine_id}. Des machines/gammes y sont liées: {e}")
            raise DatabaseError("Impossible de supprimer ce type car des machines ou gammes y sont associées.") from e
        except DatabaseError as e:
            logger.error(f"Erreur DB delete TypeMachine ID {type_machine_id}: {e}")
            raise