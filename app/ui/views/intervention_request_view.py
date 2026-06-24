from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QTextEdit, QComboBox,
    QRadioButton, QButtonGroup, QPushButton, QMessageBox, QHBoxLayout
)
from PySide6.QtCore import Signal

class InterventionRequestView(QDialog):
    request_submitted = Signal(dict)

    def __init__(self, machine_list=None, machine_id_map=None, current_user=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle(self.tr("Demande intervention"))
        self.setMinimumWidth(400)
        layout = QVBoxLayout(self)

        self.machine_id_map = machine_id_map or {}
        self.current_user = current_user

        # Titre
        title = QLabel(f"<h2>{self.tr('Demande intervention')}</h2>")
        layout.addWidget(title)

        # Description du besoin
        layout.addWidget(QLabel(self.tr("Décrivez le problème ou le besoin :")))
        self.description_edit = QTextEdit()
        layout.addWidget(self.description_edit)

        # Sélection de la machine
        layout.addWidget(QLabel(self.tr("Choisissez la machine concernée :")))
        self.machine_combo = QComboBox()
        if machine_list:
            for name in machine_list:
                machine_id = self.machine_id_map.get(name)
                self.machine_combo.addItem(name, machine_id)
        else:
            self.machine_combo.addItem(self.tr("Aucune machine disponible"), None)
        layout.addWidget(self.machine_combo)

        # Urgence
        layout.addWidget(QLabel(self.tr("Degré urgence :")))
        urgency_layout = QHBoxLayout()
        self.urgency_group = QButtonGroup(self)
        self.urgency_low = QRadioButton(self.tr("Faible"))
        self.urgency_normal = QRadioButton(self.tr("Normal"))
        self.urgency_urgent = QRadioButton(self.tr("Urgent"))
        self.urgency_normal.setChecked(True)
        self.urgency_group.addButton(self.urgency_low, 0)
        self.urgency_group.addButton(self.urgency_normal, 1)
        self.urgency_group.addButton(self.urgency_urgent, 2)
        urgency_layout.addWidget(self.urgency_low)
        urgency_layout.addWidget(self.urgency_normal)
        urgency_layout.addWidget(self.urgency_urgent)
        layout.addLayout(urgency_layout)

        # Bouton d’envoi
        self.submit_btn = QPushButton(self.tr("Envoyer la demande"))
        self.submit_btn.setStyleSheet("font-size: 18px; padding: 10px;")
        layout.addWidget(self.submit_btn)
        self.submit_btn.clicked.connect(self.submit_request)

    def submit_request(self):
        """Soumet la demande d'intervention et crée un OT de type 'Demande'."""
        from PySide6.QtWidgets import QMessageBox
        description = self.description_edit.toPlainText().strip()
        machine = self.machine_combo.currentText()
        machine_id = self.machine_combo.currentData()
        urgence = self.urgency_group.checkedId()
        utilisateur_createur_id = getattr(self.current_user, 'id_utilisateur', None) if self.current_user else None

        if not description or not machine_id or not utilisateur_createur_id:
            QMessageBox.warning(self, self.tr("Erreur"), self.tr("Veuillez remplir tous les champs."))
            return
        try:
            # On suppose que le parent WelcomeView a un accès au maintenance_service via self.parent().parent().maintenance_service
            maintenance_service = None
            if hasattr(self.parent(), 'maintenance_service'):
                maintenance_service = getattr(self.parent(), 'maintenance_service')
            elif hasattr(self.parent().parent(), 'maintenance_service'):
                maintenance_service = getattr(self.parent().parent(), 'maintenance_service')
            if not maintenance_service:
                raise Exception("Service de maintenance non disponible.")
            ot = maintenance_service.create_intervention_request_ot(
                machine_id=machine_id,
                description=description,
                urgence=urgence,
                utilisateur_createur_id=utilisateur_createur_id
            )
            QMessageBox.information(self, self.tr("Succès"), self.tr("Demande enregistrée sous OT numéro : ") + getattr(ot, 'numero_ot', '?'))
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, self.tr("Erreur"), self.tr("Erreur lors de la création de la demande : ") + str(e))
            return
        urgency = self.urgency_group.checkedButton().text()
        data = {
            "description": description,
            "machine": machine,
            "urgency": urgency
        }
        self.request_submitted.emit(data)
        self.description_edit.clear()
        self.machine_combo.setCurrentIndex(0)
        self.urgency_normal.setChecked(True)