# gmao_app/app/ui/dialogs/ot_dialog.py
""" Dialogue pour ajouter/modifier un Ordre de Travail (OT). """
import logging
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QLineEdit, QTextEdit, QComboBox,
    QDateTimeEdit, QSpinBox, QCheckBox, QDialogButtonBox, QMessageBox, QLabel,
    QGroupBox
)
from PySide6.QtCore import Slot, QDateTime, Qt
from typing import Optional, Dict, Any, List
from datetime import datetime

# Importer modèles et services
from app.core.models.ordre_travail import OrdreTravail
from app.core.models.machine import Machine
from app.core.models.technicien import Technicien
from app.core.services.machine_service import MachineService
from app.core.services.maintenance_service import (
    MaintenanceService, OT_TYPES, OT_PRIORITES, OT_STATUTS_OUVERT, OT_STATUTS_FERME
)
from app.utils.exceptions import BusinessLogicError

logger = logging.getLogger(__name__)

class OTDialog(QDialog):
    """Dialogue pour créer ou éditer un Ordre de Travail."""

    VALID_OT_STATUTS = OT_STATUTS_OUVERT + OT_STATUTS_FERME # Tous les statuts possibles

    def __init__(self,
                 machine_service: MachineService,
                 maintenance_service: MaintenanceService,
                 ot: Optional[OrdreTravail] = None,
                 selected_machine_id: Optional[int] = None,
                 current_user_id: Optional[int] = None,
                 initial_data: Optional[Dict[str, Any]] = None,
                 parent=None,
                 app_language=None):
        super().__init__(parent)
        self.machine_service = machine_service
        self.maintenance_service = maintenance_service
        self.ot_original = ot
        self.is_edit_mode = ot is not None
        self.current_user_id = current_user_id

        self.setWindowTitle(self.tr("Créer Ordre Travail") if not self.is_edit_mode else self.tr("Modifier OT {numero}").format(numero=ot.numero_ot or ot.id_ot))
        self.setMinimumWidth(550)

        self._machines: List[Machine] = []
        self._techniciens: List[Technicien] = []

        # --- Widgets ---
        self.numero_ot_label = QLabel(self.tr("Auto") if not self.is_edit_mode else (ot.numero_ot or self.tr("N/A")))
        self.date_creation_label = QLabel(datetime.now().strftime('%Y-%m-%d %H:%M') if not self.is_edit_mode else (ot.date_creation.strftime('%Y-%m-%d %H:%M') if ot and ot.date_creation else self.tr("N/A")))

        self.machine_combo = QComboBox(self)
        self.machine_combo.setObjectName("machine_combo")
        
        from app.utils.i18n import translate_type, translate_priority, translate_status
        self._lang = app_language
        self.type_combo = QComboBox(self)
        self.type_combo.setObjectName("type_combo")
        self.type_combo.clear()
        for t in OT_TYPES:
            self.type_combo.addItem(translate_type(t, self._lang), userData=t)
        
        self.description_edit = QTextEdit(self)
        self.description_edit.setPlaceholderText(self.tr("Description détaillée..."))
        self.description_edit.setMinimumHeight(60)
        
        self.priorite_combo = QComboBox(self)
        self.priorite_combo.setObjectName("priorite_combo")
        self.priorite_combo.clear()
        for p in OT_PRIORITES:
            self.priorite_combo.addItem(translate_priority(p, self._lang), userData=p)
        # Sélectionne la priorité par défaut
        idx = self.priorite_combo.findData("Moyenne")
        if idx >= 0:
            self.priorite_combo.setCurrentIndex(idx)
        
        self.urgence_check = QCheckBox(self.tr("Urgent"), self)
        
        self.date_prevue_edit = QDateTimeEdit(self)
        self.date_prevue_edit.setCalendarPopup(True)
        self.date_prevue_edit.setDateTime(QDateTime.currentDateTime().addDays(1))
        self.date_prevue_edit.setDisplayFormat("yyyy-MM-dd HH:mm")
        self.date_prevue_edit.setSpecialValueText(self.tr("Non planifié"))

        self.duree_prevue_spinbox = QSpinBox(self)
        self.duree_prevue_spinbox.setSuffix(self.tr(" min"))
        self.duree_prevue_spinbox.setRange(0, 9999)
        self.duree_prevue_spinbox.setSpecialValueText(self.tr("Non estimée"))

        self.technicien_combo = QComboBox(self)
        self.technicien_combo.setObjectName("technicien_combo")
        
        self.statut_combo = QComboBox(self) # Sera toujours modifiable
        self.statut_combo.setObjectName("statut_combo")
        self.statut_combo.clear()
        for s in self.VALID_OT_STATUTS:
            self.statut_combo.addItem(translate_status(s, self._lang), userData=s)

        self.notes_edit = QTextEdit(self)
        self.notes_edit.setPlaceholderText(self.tr("Notes additionnelles..."))
        self.notes_edit.setMinimumHeight(60)

        # --- Layouts ---
        main_layout = QVBoxLayout(self)
        if self.is_edit_mode:
            group_info = QGroupBox(self.tr("Informations OT"))
            form_info = QFormLayout(group_info)
            form_info.addRow(self.tr("Numéro OT:"), self.numero_ot_label)
            form_info.addRow(self.tr("Date Création:"), self.date_creation_label)
            main_layout.addWidget(group_info)

        group_task = QGroupBox(self.tr("Détails de la Tâche"))
        form_task = QFormLayout(group_task)
        form_task.addRow(self.tr("Machine (*):"), self.machine_combo)
        form_task.addRow(self.tr("Type (*):"), self.type_combo)
        form_task.addRow(self.tr("Description (*):"), self.description_edit)
        main_layout.addWidget(group_task)

        group_planif = QGroupBox(self.tr("Planification & Priorité"))
        form_planif = QFormLayout(group_planif)
        form_planif.addRow(self.tr("Priorité:"), self.priorite_combo)
        form_planif.addRow(self.urgence_check)
        form_planif.addRow(self.tr("Date Prévue Début:"), self.date_prevue_edit)
        form_planif.addRow(self.tr("Durée Prévue:"), self.duree_prevue_spinbox)
        main_layout.addWidget(group_planif)

        group_assign = QGroupBox(self.tr("Assignation & Statut"))
        form_assign = QFormLayout(group_assign)
        form_assign.addRow(self.tr("Technicien Assigné:"), self.technicien_combo)
        form_assign.addRow(self.tr("Statut (*):"), self.statut_combo)
        # Petit avertissement sur le statut manuel
        status_warning_label = QLabel(self.tr("<font color='orange'><i>(Modification manuelle: utilisez les boutons d'action pour le workflow standard)</i></font>"))
        status_warning_label.setTextFormat(Qt.TextFormat.RichText)
        form_assign.addRow("", status_warning_label) # Ajoute l'avertissement
        form_assign.addRow(self.tr("Notes:"), self.notes_edit)
        main_layout.addWidget(group_assign)

        # Boutons
        self.button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel, self)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        main_layout.addWidget(self.button_box)
        self.setLayout(main_layout)

        # --- Peupler ComboBoxes ---
        self._load_combobox_data()

        # --- Logique Post-Layout ---
        if self.is_edit_mode and self.ot_original:
            self._populate_fields() # Mode édition normal
            if self.ot_original.statut in OT_STATUTS_FERME:
                self._set_read_only_mode(True)
        elif initial_data: # Si création ET données initiales fournies (duplication)
            self._apply_initial_data(initial_data)
            self.statut_combo.setCurrentText(self.tr("Créé")) # Forcer statut initial
        else: # Création normale sans duplication
             self.statut_combo.setCurrentText("Créé")
             if selected_machine_id is not None:
                 self._select_combo_item_by_data(self.machine_combo, selected_machine_id)

        logger.debug(self.tr("OTDialog initialisé mode {}" ).format('Édition' if self.is_edit_mode else ('Duplication' if initial_data else 'Création')))

    def _load_combobox_data(self):
        """ Charge machines et techniciens. """
        logger.debug("Chargement données ComboBox pour OTDialog...")
        error_msg = ""
        
        # Chargement des machines
        try:
            machines = self.machine_service.get_all_machines(sort_by="nom")
            logger.debug(f"{len(machines)} machines chargées depuis le service")
            self._machines = machines
            self.machine_combo.clear()
            self.machine_combo.addItem("", None)
            
            for idx, machine in enumerate(machines):
                try:
                    if not hasattr(machine, 'nom') or machine.nom is None:
                        logger.warning(f"Machine {idx} n'a pas d'attribut 'nom' valide: {machine}")
                        continue
                        
                    nom = str(machine.nom) if machine.nom else "Sans nom"
                    serial = f" (S/N:{machine.serial})" if hasattr(machine, 'serial') and machine.serial else ""
                    txt = f"{nom}{serial}"
                    machine_id = machine.id_machine if hasattr(machine, 'id_machine') else None
                    
                    if machine_id is None:
                        logger.warning(f"Machine {idx} n'a pas d'ID valide: {machine}")
                        continue
                        
                    self.machine_combo.addItem(txt, userData=machine_id)
                except Exception as e:
                    logger.error(f"Erreur lors du traitement de la machine {idx}: {e}", exc_info=True)
                    
        except Exception as e:
            error_msg = f"Erreur lors du chargement des machines: {str(e)}\n"
            logger.error("Erreur dans _load_combobox_data pour les machines:", exc_info=True)
        
        # Chargement des techniciens
        try:
            techs = self.maintenance_service.get_all_techniciens(include_inactive=False)
            logger.debug(f"{len(techs)} techniciens chargés depuis le service")
            self._techniciens = techs
            self.technicien_combo.clear()
            self.technicien_combo.addItem(self.tr("Non assigné"), None)
            
            for tech in techs:
                try:
                    if not hasattr(tech, 'nom_complet') or not tech.nom_complet:
                        logger.warning(f"Technicien sans nom complet: {tech}")
                        continue
                    if not hasattr(tech, 'id_technicien'):
                        logger.warning(f"Technicien sans ID: {tech}")
                        continue
                    self.technicien_combo.addItem(tech.nom_complet, userData=tech.id_technicien)
                except Exception as e:
                    logger.error(f"Erreur lors du traitement d'un technicien: {e}", exc_info=True)
                    
        except Exception as e:
            error_msg += f"Erreur lors du chargement des techniciens: {str(e)}\n"
            logger.error("Erreur dans _load_combobox_data pour les techniciens:", exc_info=True)

        # Gestion des erreurs
        if error_msg:
            QMessageBox.warning(
                self,
                self.tr("Erreur de chargement"),
                self.tr("Des erreurs sont survenues lors du chargement des données :\n") + error_msg
            )
            self.button_box.button(QDialogButtonBox.StandardButton.Ok).setEnabled(False)
        else:
            logger.debug("Données ComboBox OTDialog chargées avec succès")

    # Dans la classe OTDialog

    def _populate_fields(self):
        """ Remplit les champs du formulaire avec les données de l'OT original (self.ot_original). """
        if not self.is_edit_mode or not self.ot_original:
            logger.warning("Appel à _populate_fields sans être en mode édition ou sans OT original.")
            return

        ot = self.ot_original # Raccourci

        # Sélectionner Machine et Technicien dans les ComboBoxes
        self._select_combo_item_by_data(self.machine_combo, ot.machine_id)
        self._select_combo_item_by_data(self.technicien_combo, ot.technicien_assigne_id)

        # Définir les valeurs des autres widgets
        idx_type = self.type_combo.findData(ot.type or "")
        if idx_type >= 0:
            self.type_combo.setCurrentIndex(idx_type)
        self.description_edit.setText(ot.description or "")
        idx_prio = self.priorite_combo.findData(ot.priorite or "Moyenne")
        if idx_prio >= 0:
            self.priorite_combo.setCurrentIndex(idx_prio)
        self.urgence_check.setChecked(ot.urgence or False)
        idx_statut = self.statut_combo.findData(ot.statut or "Créé")
        if idx_statut >= 0:
            self.statut_combo.setCurrentIndex(idx_statut)
        self.notes_edit.setText(ot.notes_planification or "")

        # Gérer la date prévue (avec la valeur spéciale "Non planifié")
        if ot.date_prevue:
            self.date_prevue_edit.setDateTime(QDateTime(ot.date_prevue))
        else:
            # Mettre la date/heure à la valeur minimale pour afficher le texte spécial
            self.date_prevue_edit.setDateTime(self.date_prevue_edit.minimumDateTime())

        # Gérer la durée prévue (avec la valeur spéciale "Non estimée")
        if ot.duree_prevue_min is not None:
            self.duree_prevue_spinbox.setValue(ot.duree_prevue_min)
        else:
             # Mettre la valeur au minimum pour afficher le texte spécial
            self.duree_prevue_spinbox.setValue(self.duree_prevue_spinbox.minimum())

        # Mettre à jour les labels (même si déjà fait dans __init__ pour édition)
        self.numero_ot_label.setText(ot.numero_ot or f"ID: {ot.id_ot}")
        date_creat_str = ot.date_creation.strftime('%Y-%m-%d %H:%M') if ot.date_creation else "N/A"
        self.date_creation_label.setText(date_creat_str)
        # Charger nom créateur si besoin ici (nécessite user_service)

    # Dans la classe OTDialog

    # ... (après _populate_fields) ...

    def _apply_initial_data(self, data: Dict[str, Any]):
        """ Pré-remplit les champs avec les données initiales fournies (pour duplication). """
        logger.debug(f"Application données initiales pour duplication: {data}")

        # Pré-sélectionner Machine
        self._select_combo_item_by_data(self.machine_combo, data.get('machine_id'))

        # Pré-remplir Type, Description, Priorité, Urgence, Durée
        self.type_combo.setCurrentText(data.get('type', "")) # Défaut vide si non fourni
        self.description_edit.setText(data.get('description', ""))
        self.priorite_combo.setCurrentText(data.get('priorite', "Moyenne"))
        self.urgence_check.setChecked(data.get('urgence', False))

        duree = data.get('duree_prevue_min')
        if duree is not None:
            self.duree_prevue_spinbox.setValue(duree)
        else:
            # Afficher "Non estimée"
            self.duree_prevue_spinbox.setValue(self.duree_prevue_spinbox.minimum())

        # --- Laisser les autres champs aux valeurs par défaut pour un nouvel OT ---
        # Statut est déjà mis à "Créé" dans __init__ si initial_data est fourni
        # Date prévue est déjà mise à demain
        # Technicien est déjà mis à "Non assigné"
        # Notes sont vides

# ... (reste de la classe OTDialog) ...
    
    # La méthode _select_combo_item_by_data(...) doit déjà exister

    def _select_combo_item_by_data(self, combo: QComboBox, target_id: Optional[int]):
        """ Sélectionne item par userData ID. """
        if target_id is None: 
            combo.setCurrentIndex(0)
            return
            
        for index in range(combo.count()):
            if combo.itemData(index) == target_id: 
                combo.setCurrentIndex(index)
                return
                
        combo_name = combo.objectName() or 'combo_inconnu'
        combo_type = {
            'machine_combo': 'machine',
            'technicien_combo': 'technicien',
            'type_combo': 'type',
            'priorite_combo': 'priorité',
            'statut_combo': 'statut'
        }.get(combo_name, combo_name)
        
        logger.warning(f"ID {target_id} non trouvé dans la liste des {combo_type}s. Défaut sur premier élément.")
        combo.setCurrentIndex(0)
        
    def _set_read_only_mode(self, read_only: bool):
        """ Met en lecture seule si OT fermé. """
        logger.info(f"Mise en lecture seule OTDialog : {read_only}")
        # Récupérer tous les widgets des types concernés
        widgets = []
        for t in (QLineEdit, QTextEdit, QComboBox, QDateTimeEdit, QSpinBox, QCheckBox):
            widgets += self.findChildren(t)
        for widget in widgets:
            if isinstance(widget, (QLineEdit, QTextEdit, QDateTimeEdit, QSpinBox)):
                widget.setReadOnly(read_only)
            else:
                # QComboBox et QCheckBox
                widget.setEnabled(not read_only)
        # Désactiver OK si lecture seule
        self.button_box.button(QDialogButtonBox.StandardButton.Ok).setEnabled(not read_only)

    @Slot()
    def accept(self):
        """ Valide avant de fermer. """
        # Si en mode édition et fermé, ne pas accepter (sécurité)
        if self.is_edit_mode and self.ot_original and self.ot_original.statut in OT_STATUTS_FERME:
            logger.warning("Tentative sauvegarde OT fermé ignorée.")
            super().reject() # Ou juste ne rien faire pour garder ouvert? Rejet silencieux OK.
            return

        if self._validate_input():
            logger.debug("Validation OTDialog réussie.")
            super().accept()
        else:
            logger.warning("Validation OTDialog échouée.")


    def _validate_input(self) -> bool:
        """
        Vérifie la validité des champs du formulaire OT. Affiche une QMessageBox en cas d'erreur.
        Retourne True si tout est valide, False sinon.
        """
        # Vérification machine obligatoire
        machine_id = self.machine_combo.currentData()
        if machine_id is None:
            QMessageBox.warning(self, self.tr("Validation"), self.tr("Veuillez sélectionner une machine."))
            logger.warning("Validation échouée: machine non sélectionnée.")
            return False
        # Vérification type obligatoire
        type_val = self.type_combo.currentText().strip()
        if not type_val:
            QMessageBox.warning(self, self.tr("Validation"), self.tr("Veuillez sélectionner un type d'OT."))
            logger.warning("Validation échouée: type non sélectionné.")
            return False
        # Vérification description obligatoire
        description = self.description_edit.toPlainText().strip()
        if not description:
            QMessageBox.warning(self, self.tr("Validation"), self.tr("Veuillez saisir une description."))
            logger.warning("Validation échouée: description vide.")
            return False
        # Vérification statut valide
        statut = self.statut_combo.currentData()
        if statut not in self.VALID_OT_STATUTS:
            QMessageBox.warning(self, self.tr("Validation"), self.tr("Statut d'OT invalide."))
            logger.warning(f"Validation échouée: statut invalide ({statut}).")
            return False
        # Vérification durée prévue (si renseignée)
        duree_val = self.duree_prevue_spinbox.value()
        if duree_val < 0:
            QMessageBox.warning(self, self.tr("Validation"), self.tr("La durée prévue ne peut pas être négative."))
            logger.warning("Validation échouée: durée négative.")
            return False
        # Si tout est OK
        return True

    def get_ot_data(self) -> Dict[str, Any]:
        """ Récupère les données pour le service. """
        date_prevue_val = self.date_prevue_edit.dateTime()
        date_prevue_dt = date_prevue_val.toPython() if date_prevue_val > self.date_prevue_edit.minimumDateTime() else None

        duree_prevue_val = self.duree_prevue_spinbox.value()
        duree_prevue_min = duree_prevue_val if duree_prevue_val > self.duree_prevue_spinbox.minimum() else None

        data = {
            "machine_id": self.machine_combo.currentData(),
            "type": self.type_combo.currentData(),  # Utilise la clé d'origine
            "description": self.description_edit.toPlainText().strip(),
            "priorite": self.priorite_combo.currentData(),  # Utilise la clé d'origine
            "urgence": self.urgence_check.isChecked(),
            "statut": self.statut_combo.currentData(),  # Utilise la clé d'origine
            "technicien_assigne_id": self.technicien_combo.currentData(),
            "date_prevue": date_prevue_dt,
            "duree_prevue_min": duree_prevue_min,
            "notes_planification": self.notes_edit.toPlainText().strip() or None,
        }

        if self.is_edit_mode and self.ot_original:
             data["id_ot"] = self.ot_original.id_ot
             data["utilisateur_createur_id"] = self.ot_original.utilisateur_createur_id # Important pour update
        else:
             # Le service utilisera current_user_id s'il est fourni à create_ot
             data["utilisateur_createur_id"] = self.current_user_id

        logger.debug(f"Données récupérées du OTDialog: {data}")
        return data
    
    # gmao_app/app/ui/dialogs/ot_dialog.py
# ... (imports)
