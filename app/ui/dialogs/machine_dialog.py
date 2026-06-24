# gmao_app/app/ui/dialogs/machine_dialog.py
"""
Fenêtre de dialogue pour ajouter ou modifier les informations d'une Machine.
"""
import logging
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QLineEdit, QTextEdit, QComboBox, QDateEdit,
    QDialogButtonBox, QMessageBox, QGroupBox, QSpinBox
)
from PySide6.QtCore import Slot, QDate
from typing import Optional, List, Dict, Any
from datetime import date

# Importer les modèles et le service (pour les listes déroulantes)
from app.core.models.machine import Machine
from app.core.models.site import Site
from app.core.models.fabricant import Fabricant
from app.core.models.type_machine import TypeMachine
from app.core.services.machine_service import MachineService
from app.utils.exceptions import BusinessLogicError

logger = logging.getLogger(__name__)

class MachineDialog(QDialog):
    """Dialogue pour créer ou éditer une Machine."""

    def __init__(self,
                 machine_service: MachineService, # Reçoit le service
                 machine: Optional[Machine] = None,
                 parent=None):
        """
        Initialise le dialogue.

        Args:
            machine_service (MachineService): Instance du service pour récupérer les listes.
            machine (Optional[Machine]): La Machine à éditer (None si création).
            parent: Le widget parent.
        """
        super().__init__(parent)
        self.machine_service = machine_service
        self.machine_original = machine
        self.is_edit_mode = machine is not None

        self.setWindowTitle(self.tr("Ajouter une Machine") if not self.is_edit_mode else self.tr("Modifier la Machine"))
        self.setMinimumWidth(550)

        # --- Données pour les ComboBox ---
        self._sites: List[Site] = []
        self._fabricants: List[Fabricant] = []
        self._types_machine: List[TypeMachine] = []
        # Machine parente possible (pour la hiérarchie)
        # Pourrait être complexe à charger ici, gérer via bouton séparé? Pour V1, on omet le parent.
        # self._potential_parents: List[Machine] = []

        # --- Widgets ---
        # Groupe Informations Générales
        self.nom_input = QLineEdit(self)
        self.type_combo = QComboBox(self)
        self.site_combo = QComboBox(self)
        self.fabricant_combo = QComboBox(self)
        self.localisation_input = QLineEdit(self) # Localisation dans le site
        self.criticite_combo = QComboBox(self) # A, B, C
        self.criticite_combo.addItems(["", self.tr("A - Critique"), self.tr("B - Important"), self.tr("C - Normal")]) # Ajouter valeurs
        self.etat_combo = QComboBox(self) # Statuts machine
        # TODO: Charger statuts depuis config/nomenclature
        self.etat_combo.addItems([self.tr("Inconnu"), self.tr("En service"), self.tr("Arrêt planifié"), self.tr("En panne"), self.tr("En maintenance"), self.tr("Hors service")])

        # Groupe Identification & Installation
        self.serial_input = QLineEdit(self)
        self.modele_input = QLineEdit(self)
        self.date_installation_edit = QDateEdit(self)
        self.date_installation_edit.setCalendarPopup(True)
        self.date_installation_edit.setDisplayFormat("yyyy-MM-dd")
        self.date_installation_edit.setDate(QDate.currentDate()) # Défaut
        self.date_installation_edit.setSpecialValueText(self.tr("Non définie")) # Permettre vide
        self.garantie_fin_edit = QDateEdit(self)
        self.garantie_fin_edit.setCalendarPopup(True)
        self.garantie_fin_edit.setDisplayFormat("yyyy-MM-dd")
        self.garantie_fin_edit.setDate(QDate(2000,1,1)) # Date lointaine par défaut si vide
        self.garantie_fin_edit.setSpecialValueText(self.tr("Non définie"))

        # Groupe Infos Techniques
        self.info_tech_edit = QTextEdit(self)
        self.info_tech_edit.setPlaceholderText(self.tr("Caractéristiques, puissance, etc."))
        self.info_tech_edit.setMaximumHeight(100) # Limiter la hauteur

        # --- Peupler les ComboBox ---
        self._load_combobox_data()

        # --- Layout ---
        form_layout = QFormLayout()

        # Groupe 1
        group1_box = QGroupBox(self.tr("Informations Générales"))
        group1_layout = QFormLayout(group1_box)
        group1_layout.addRow(self.tr("Nom (*)"), self.nom_input)
        group1_layout.addRow(self.tr("Type (*)"), self.type_combo)
        group1_layout.addRow(self.tr("Site (*)"), self.site_combo)
        group1_layout.addRow(self.tr("Fabricant (*)"), self.fabricant_combo)
        group1_layout.addRow(self.tr("Localisation"), self.localisation_input)
        group1_layout.addRow(self.tr("Criticité"), self.criticite_combo)
        group1_layout.addRow(self.tr("État"), self.etat_combo)

        # Groupe 2
        group2_box = QGroupBox(self.tr("Identification & Dates"))
        group2_layout = QFormLayout(group2_box)
        group2_layout.addRow(self.tr("N° Série"), self.serial_input)
        group2_layout.addRow(self.tr("Modèle"), self.modele_input)
        group2_layout.addRow(self.tr("Date Installation"), self.date_installation_edit)
        group2_layout.addRow(self.tr("Fin Garantie"), self.garantie_fin_edit)

         # Groupe 3
        group3_box = QGroupBox(self.tr("Informations Techniques"))
        group3_layout = QVBoxLayout(group3_box) # QVBoxLayout pour QTextEdit
        group3_layout.addWidget(self.info_tech_edit)

        # Ajout des groupes au layout principal
        form_layout.addRow(group1_box)
        form_layout.addRow(group2_box)
        form_layout.addRow(group3_box)

        # Boutons OK / Annuler
        self.button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel, self)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)

        main_layout = QVBoxLayout(self)
        main_layout.addLayout(form_layout)
        main_layout.addWidget(self.button_box)
        self.setLayout(main_layout)

        # --- Pré-remplir si mode édition ---
        if self.is_edit_mode and self.machine_original:
            self._populate_fields()

        logger.debug(f"MachineDialog initialisé en mode {'Édition' if self.is_edit_mode else 'Création'}")

    def _load_combobox_data(self):
        """Charge les données pour les listes déroulantes depuis le service."""
        logger.debug("Chargement données ComboBox pour MachineDialog...")
        try:
            # Sites
            self._sites = self.machine_service.get_all_sites()
            self.site_combo.clear()
            self.site_combo.addItem("", userData=None) # Option vide
            for site in self._sites:
                self.site_combo.addItem(site.nom, userData=site.id_site)

            # Fabricants
            self._fabricants = self.machine_service.get_all_fabricants()
            self.fabricant_combo.clear()
            self.fabricant_combo.addItem("", userData=None) # Option vide
            for fab in self._fabricants:
                self.fabricant_combo.addItem(fab.nom, userData=fab.id_fabricant)

            # Types Machine
            self._types_machine = self.machine_service.get_all_type_machines()
            self.type_combo.clear()
            self.type_combo.addItem("", userData=None) # Option vide
            for tm in self._types_machine:
                # Afficher Catégorie + Nom pour clarté si catégorie existe
                display_text = f"{tm.categorie} - {tm.nom}" if tm.categorie else tm.nom
                self.type_combo.addItem(display_text, userData=tm.id_type_machine)

            # TODO: Charger parents possibles si nécessaire
            logger.debug("Données ComboBox chargées.")

        except BusinessLogicError as e:
            logger.error(f"Erreur chargement données ComboBox: {e}")
            # Afficher message ou désactiver dialogue? Pour l'instant on logge.
            error_msg = self.tr("Impossible de charger les listes pour les menus déroulants.\nVérifiez la base de données ou l'état des services.\nDétail: {e}").format(e=e)
            QMessageBox.warning(self, self.tr("Erreur de Chargement"), error_msg)
            # On pourrait fermer le dialogue ou désactiver les champs
            self.button_box.button(QDialogButtonBox.StandardButton.Ok).setEnabled(False)

    def _populate_fields(self):
        """Remplit les champs avec les données de self.machine_original."""
        m = self.machine_original
        self.nom_input.setText(m.nom or "")
        self.serial_input.setText(m.serial or "")
        self.modele_input.setText(m.modele or "")
        self.localisation_input.setText(m.localisation or "")
        self.info_tech_edit.setText(m.informations_techniques or "")
        self.etat_combo.setCurrentText(m.etat or "Inconnu")

        # Sélectionner Criticité
        crit_text = ""
        if m.criticite == "A": crit_text = "A - Critique"
        elif m.criticite == "B": crit_text = "B - Important"
        elif m.criticite == "C": crit_text = "C - Normal"
        self.criticite_combo.setCurrentText(crit_text)

        # Sélectionner Dates
        self.date_installation_edit.setDate(QDate(m.date_installation) if m.date_installation else QDate(2000,1,1))
        if not m.date_installation: self.date_installation_edit.clear() # Utilise SpecialValueText

        self.garantie_fin_edit.setDate(QDate(m.garantie_fin) if m.garantie_fin else QDate(2000,1,1))
        if not m.garantie_fin: self.garantie_fin_edit.clear()

        # Sélectionner les items dans les ComboBox par ID
        self._select_combo_item_by_data(self.site_combo, m.site_id)
        self._select_combo_item_by_data(self.fabricant_combo, m.fabricant_id)
        self._select_combo_item_by_data(self.type_combo, m.type_machine_id)

        # TODO: Gérer parent_machine_id si implémenté

    def _select_combo_item_by_data(self, combo: QComboBox, target_id: Optional[int]):
        """ Trouve et sélectionne l'item dans le QComboBox basé sur userData (ID). """
        if target_id is None:
             combo.setCurrentIndex(0) # Sélectionner l'item vide
             return
        for index in range(combo.count()):
            item_data = combo.itemData(index)
            if item_data == target_id:
                combo.setCurrentIndex(index)
                return
        logger.warning(f"ID {target_id} non trouvé dans le ComboBox {combo.objectName()}.")
        combo.setCurrentIndex(0) # Item vide par défaut si non trouvé

    def _validate_input(self) -> bool:
        """Vérifie les champs obligatoires."""
        nom = self.nom_input.text().strip()
        type_id = self.type_combo.currentData()
        site_id = self.site_combo.currentData()
        fabricant_id = self.fabricant_combo.currentData()

        if not nom:
            QMessageBox.warning(self, self.tr("Champ manquant"), self.tr("Le 'Nom' de la machine est obligatoire."))
            self.nom_input.setFocus()
            return False
        if type_id is None:
            QMessageBox.warning(self, self.tr("Champ manquant"), self.tr("Le 'Type' de machine est obligatoire."))
            self.type_combo.setFocus()
            return False
        if site_id is None:
            QMessageBox.warning(self, self.tr("Champ manquant"), self.tr("Le 'Site' est obligatoire."))
            self.site_combo.setFocus()
            return False
        if fabricant_id is None:
            QMessageBox.warning(self, self.tr("Champ manquant"), self.tr("Le 'Fabricant' est obligatoire."))
            self.fabricant_combo.setFocus()
            return False

        # TODO: Valider dates (ex: fin garantie > install)?
        # TODO: Valider unicité numéro série si fourni? (Mieux fait par service/repo)

        return True

    @Slot()
    def accept(self):
        """Valide avant de fermer."""
        if self._validate_input():
            logger.debug("Validation MachineDialog réussie.")
            super().accept()
        else:
            logger.warning("Validation MachineDialog échouée.")

    def get_machine_data(self) -> Dict[str, Any]:
        """Récupère les données saisies sous forme de dictionnaire pour le service."""
        date_install = self.date_installation_edit.date().toPython() \
                       if not self.date_installation_edit.date().isNull() else None
        garantie_fin = self.garantie_fin_edit.date().toPython() \
                       if not self.garantie_fin_edit.date().isNull() else None

        criticite_text = self.criticite_combo.currentText()
        criticite_code = None
        if "A -" in criticite_text: criticite_code = "A"
        elif "B -" in criticite_text: criticite_code = "B"
        elif "C -" in criticite_text: criticite_code = "C"

        data = {
            "nom": self.nom_input.text().strip(),
            "type_machine_id": self.type_combo.currentData(),
            "site_id": self.site_combo.currentData(),
            "fabricant_id": self.fabricant_combo.currentData(),
            "serial": self.serial_input.text().strip() or None,
            "modele": self.modele_input.text().strip() or None,
            "date_installation": date_install,
            "localisation": self.localisation_input.text().strip() or None,
            "etat": self.etat_combo.currentText() or "Inconnu",
            "informations_techniques": self.info_tech_edit.toPlainText().strip() or None,
            # "parent_machine_id": None, # A gérer si hiérarchie implémentée
            "criticite": criticite_code,
            "garantie_fin": garantie_fin
        }

        # En mode édition, on ajoute l'ID pour l'update
        if self.is_edit_mode and self.machine_original:
             data["id_machine"] = self.machine_original.id_machine

        logger.debug(f"Données récupérées du MachineDialog: {data}")
        return data