"""
Définition des modèles de données pour l'application GMAO.

Ce fichier est la source de vérité pour la structure de la base de données.

NOTE IMPORTANTE SUR L'ARCHITECTURE :
Tous les modèles de ce fichier utilisent `class Meta: managed = False`.
Cela signifie que Django n'a PAS la responsabilité de gérer le schéma de la
base de données (création, modification, suppression des tables).

Le schéma de la base de données est supposé être géré par un autre système
(par exemple, une application externe ou des scripts SQL manuels).
Django se contente de lire et d'écrire dans des tables qui existent déjà,
mappées via l'attribut `db_table`.
"""

from django.db import models


# =============================================================================
# MODÈLES DE CONFIGURATION DE BASE (Sites, Fabricants, etc.)
# =============================================================================

class Site(models.Model):
    """Représente un site industriel ou géographique."""
    id_site = models.AutoField(primary_key=True)
    nom = models.CharField(max_length=255, unique=True, help_text="Nom unique du site")
    adresse = models.TextField(blank=True, null=True)
    ville = models.CharField(max_length=100, blank=True, null=True)
    pays = models.CharField(max_length=100, blank=True, null=True)
    contact_principal = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'site'

    def __str__(self):
        return self.nom


class Fabricant(models.Model):
    """Représente un fabricant d'équipements."""
    id_fabricant = models.AutoField(primary_key=True)
    nom = models.CharField(max_length=255, unique=True)
    contact = models.TextField(blank=True, null=True)
    site_web = models.URLField(blank=True, null=True)
    support_technique = models.TextField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'fabricant'

    def __str__(self):
        return self.nom


class TypeMachine(models.Model):
    """Catégorise les machines (ex: "Presse hydraulique", "Robot de soudure")."""
    id_type_machine = models.AutoField(primary_key=True)
    nom = models.CharField(max_length=255, unique=True)
    description = models.TextField(blank=True, null=True)
    categorie = models.CharField(max_length=100, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'type_machine'

    def __str__(self):
        return self.nom


# =============================================================================
# MODÈLES CENTRAUX (Machines, Techniciens, Utilisateurs)
# =============================================================================

class Machine(models.Model):
    """Représente un équipement ou une machine physique."""
    id_machine = models.AutoField(primary_key=True)
    nom = models.CharField(max_length=255)
    serial = models.CharField(max_length=255, unique=True, blank=True, null=True, help_text="Numéro de série unique")
    modele = models.CharField(max_length=255, blank=True, null=True)
    date_installation = models.DateField(blank=True, null=True)
    localisation = models.CharField(max_length=255, blank=True, null=True, help_text="Ex: 'Bâtiment A, Ligne 3'")
    etat = models.CharField(max_length=50, blank=True, null=True, help_text="Ex: 'En service', 'En panne'")
    informations_techniques = models.TextField(blank=True, null=True)
    type_machine = models.ForeignKey(TypeMachine, on_delete=models.PROTECT, related_name='machines')
    site = models.ForeignKey(Site, on_delete=models.PROTECT, related_name='machines')
    fabricant = models.ForeignKey(Fabricant, on_delete=models.PROTECT, related_name='machines')
    parent_machine = models.ForeignKey('self', on_delete=models.CASCADE, blank=True, null=True, help_text="Pour les sous-équipements")
    criticite = models.CharField(max_length=50, blank=True, null=True, help_text="Ex: 'Haute', 'Moyenne', 'Basse'")
    garantie_fin = models.DateField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        managed = False
        db_table = 'machine'

    def __str__(self):
        return f"{self.nom} ({self.serial or 'N/A'})"


class Equipe(models.Model):
    """Représente une équipe de techniciens."""
    id_equipe = models.AutoField(primary_key=True)
    nom = models.CharField(max_length=255, unique=True)
    domaine_expertise = models.CharField(max_length=255, blank=True, null=True, help_text="Ex: 'Électricité', 'Mécanique'")
    responsable = models.ForeignKey('Technicien', on_delete=models.SET_NULL, blank=True, null=True, related_name='equipes_dirigees')

    class Meta:
        managed = False
        db_table = 'equipe'

    def __str__(self):
        return self.nom


class Technicien(models.Model):
    """Représente un technicien de maintenance."""
    id_technicien = models.AutoField(primary_key=True)
    nom = models.CharField(max_length=255)
    prenom = models.CharField(max_length=255, blank=True, null=True)
    qualification = models.CharField(max_length=255, blank=True, null=True)
    contact = models.CharField(max_length=255, blank=True, null=True, help_text="Numéro de téléphone ou email")
    cout_horaire = models.FloatField(blank=True, null=True, help_text="Coût pour le calcul des interventions")
    equipe = models.ForeignKey(Equipe, on_delete=models.SET_NULL, blank=True, null=True, related_name='techniciens')
    actif = models.BooleanField(default=True, help_text="Indique si le technicien est actuellement en service")

    class Meta:
        managed = False
        db_table = 'technicien'

    def __str__(self):
        return self.nom_complet

    @property
    def nom_complet(self):
        """Retourne le nom complet du technicien."""
        return f"{self.nom} {self.prenom or ''}".strip()


class Utilisateur(models.Model):
    """Représente un utilisateur du système (potentiellement non-technicien)."""
    id_utilisateur = models.AutoField(primary_key=True)
    login = models.CharField(max_length=255, unique=True)
    mot_de_passe_hash = models.CharField(max_length=255, help_text="Doit être un hash sécurisé")
    nom_complet = models.CharField(max_length=255, blank=True, null=True)
    role = models.CharField(max_length=50, help_text="Ex: 'Admin', 'Manager', 'Technicien'")
    email = models.EmailField(unique=True, blank=True, null=True)
    actif = models.BooleanField(default=True, help_text="Indique si l'utilisateur est actif")
    derniere_connexion = models.DateTimeField(blank=True, null=True)
    technicien = models.ForeignKey(Technicien, on_delete=models.SET_NULL, blank=True, null=True, related_name='comptes_utilisateur')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        managed = False
        db_table = 'utilisateur'

    def __str__(self):
        return f"{self.nom_complet or self.login} ({self.role})"

    @property
    def is_technicien(self):
        """Vérifie si cet utilisateur est lié à un profil technicien."""
        return self.technicien is not None


# =============================================================================
# MODÈLES OPÉRATIONNELS (Ordres de Travail, Maintenance)
# =============================================================================

class OrdreTravail(models.Model):
    """L'objet central de la GMAO : un ordre de travail (OT)."""
    STATUT_CHOICES = [
        ("PLANIFIE", "Planifié"),
        ("ASSIGNE", "Assigné"),
        ("EN_COURS", "En cours"),
        ("TERMINE", "Terminé"),
        ("ANNULE", "Annulé"),
    ]
    TYPE_CHOICES = [
        ("PREVENTIF", "Préventif"),
        ("CORRECTIF", "Correctif"),
        ("AMELIORATION", "Amélioration"),
    ]
    PRIORITE_CHOICES = [
        ("BASSE", "Basse"),
        ("NORMALE", "Normale"),
        ("HAUTE", "Haute"),
        ("CRITIQUE", "Critique"),
    ]

    id_ot = models.AutoField(primary_key=True)
    numero_ot = models.CharField(max_length=50, unique=True, blank=True, null=True, help_text="Identifiant lisible de l'OT")
    machine = models.ForeignKey(Machine, on_delete=models.PROTECT, related_name='ordres_travail')
    gamme_id = models.IntegerField(blank=True, null=True, help_text="ID d'une gamme de maintenance standard, si applicable")
    type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    description = models.TextField()
    date_creation = models.DateTimeField(auto_now_add=True)
    date_prevue = models.DateTimeField(blank=True, null=True)
    duree_prevue_min = models.IntegerField(blank=True, null=True)
    priorite = models.CharField(max_length=20, choices=PRIORITE_CHOICES, default="NORMALE")
    urgence = models.IntegerField(default=0)
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default="PLANIFIE")
    technicien_assigne = models.ForeignKey(Technicien, on_delete=models.SET_NULL, blank=True, null=True, related_name='ots_assignes')
    utilisateur_createur = models.ForeignKey(Utilisateur, on_delete=models.PROTECT, related_name='ots_crees')
    notes_planification = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        managed = False
        db_table = 'ordre_travail'
        ordering = ['-date_creation']

    def __str__(self):
        return f"OT {self.numero_ot or self.id_ot} - {self.machine.nom}"

    @property
    def is_assignable(self):
        """Vérifie si l'OT peut être assigné."""
        return self.statut in ["PLANIFIE", "ASSIGNE"]

    @property
    def is_en_cours(self):
        """Vérifie si l'OT est en cours d'exécution."""
        return self.statut == "EN_COURS"


class Maintenance(models.Model):
    """Représente le rapport d'une intervention de maintenance terminée."""
    TYPE_CHOICES = OrdreTravail.TYPE_CHOICES  # Réutilise les mêmes choix que l'OT

    id_maintenance = models.AutoField(primary_key=True)
    ot = models.OneToOneField(OrdreTravail, on_delete=models.CASCADE, related_name='rapport_maintenance')
    machine = models.ForeignKey(Machine, on_delete=models.PROTECT, blank=True, null=True, related_name='maintenances')
    technicien = models.ForeignKey(Technicien, on_delete=models.PROTECT, related_name='maintenances_realisees')
    date_debut_reelle = models.DateTimeField()
    date_fin_reelle = models.DateTimeField()
    duree_intervention_h = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True, help_text="Durée calculée en heures")
    type_reel = models.CharField(max_length=20, choices=TYPE_CHOICES, help_text="Le type de travail réellement effectué")
    description_travaux = models.TextField()
    resultat = models.TextField(help_text="Ex: 'Réparé', 'Remplacé', 'Ajusté'")
    
    # Champs de coût : `cout_total` est le champ principal. Les autres sont pour une ventilation détaillée.
    cout_total = models.FloatField(blank=True, null=True, help_text="Coût total calculé de l'intervention")
    cout_main_oeuvre = models.FloatField(blank=True, null=True)
    cout_pieces_internes = models.FloatField(blank=True, null=True)
    cout_pieces_externes = models.FloatField(blank=True, null=True)
    cout_autres_frais = models.FloatField(blank=True, null=True)
    cout_manuel_v1 = models.FloatField(blank=True, null=True, help_text="Champ hérité, potentiellement obsolète")

    evaluation_qualite = models.IntegerField(blank=True, null=True, help_text="Note de 1 à 5")
    impact_production = models.CharField(max_length=255, blank=True, null=True, help_text="Ex: 'Aucun', 'Mineur', 'Arrêt de production'")
    notes_technicien = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = False
        db_table = 'maintenance'

    def __str__(self):
        return f"Maintenance {self.ot.numero_ot} - {self.technicien.nom_complet}"

    @property
    def duree_calculee(self):
        """Calcule la durée de l'intervention à la volée."""
        if self.date_debut_reelle and self.date_fin_reelle:
            delta = self.date_fin_reelle - self.date_debut_reelle
            return round(delta.total_seconds() / 3600, 2)
        return None


# =============================================================================
# MODÈLES POUR LA GESTION DES PIÈCES ET DU STOCK
# =============================================================================

class Fournisseur(models.Model):
    """Représente un fournisseur de pièces détachées."""
    id_fournisseur = models.AutoField(primary_key=True)
    nom = models.CharField(max_length=255, unique=True)
    contact = models.TextField(blank=True, null=True)
    adresse = models.TextField(blank=True, null=True)
    telephone = models.CharField(max_length=50, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    delai_livraison_moyen_j = models.IntegerField(blank=True, null=True, help_text="En jours")
    devise = models.CharField(max_length=10, blank=True, null=True, help_text="Ex: 'EUR', 'USD'")
    note_qualite = models.DecimalField(max_digits=3, decimal_places=1, blank=True, null=True, help_text="Note sur 5 ou 10")
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        managed = False
        db_table = 'fournisseur'

    def __str__(self):
        return self.nom


class Piece(models.Model):
    """Représente une pièce détachée ou un consommable."""
    STATUT_CHOICES = [
        ("ACTIF", "Actif"),
        ("OBSOLETE", "Obsolète"),
        ("DISCONTINUE", "Discontinué"),
    ]

    id_piece = models.AutoField(primary_key=True)
    reference = models.CharField(max_length=255, unique=True, help_text="Référence unique du fabricant ou interne")
    nom = models.CharField(max_length=255)
    fournisseur_pref = models.ForeignKey(Fournisseur, on_delete=models.SET_NULL, blank=True, null=True, related_name='pieces')
    prix_unitaire = models.FloatField(blank=True, null=True)
    stock_actuel = models.IntegerField(default=0)
    stock_reserve = models.IntegerField(default=0, help_text="Quantité réservée pour des OT planifiés")
    stock_alerte = models.IntegerField(blank=True, null=True, help_text="Seuil pour déclencher une alerte de stock bas")
    unite = models.CharField(max_length=50, help_text="Ex: 'Unité', 'Litre', 'Mètre'")
    categorie = models.CharField(max_length=100, blank=True, null=True)
    emplacement_stockage = models.CharField(max_length=255, blank=True, null=True, help_text="Ex: 'Magasin A, Allée 5, Étagère 2'")
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default="ACTIF")
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        managed = False
        db_table = 'piece'

    def __str__(self):
        return f"{self.reference} - {self.nom}"

    @property
    def stock_disponible(self):
        """Retourne le stock réel moins le stock réservé."""
        return max(0, self.stock_actuel - self.stock_reserve)

    @property
    def alerte_stock(self):
        """Vérifie si le stock actuel est en dessous du seuil d'alerte."""
        return self.stock_alerte is not None and self.stock_actuel <= self.stock_alerte


class InterventionPiece(models.Model):
    """Table de liaison qui enregistre les pièces utilisées pour une maintenance."""
    id = models.AutoField(primary_key=True)
    maintenance = models.ForeignKey(Maintenance, on_delete=models.CASCADE, related_name='pieces_utilisees')
    piece = models.ForeignKey(Piece, on_delete=models.PROTECT, related_name='utilisations')
    quantite = models.IntegerField()
    lot = models.CharField(max_length=100, blank=True, null=True, help_text="Numéro de lot ou de série de la pièce utilisée")

    class Meta:
        managed = False
        db_table = 'intervention_piece'
        unique_together = [['maintenance', 'piece']] # Empêche de mettre deux fois la même pièce sur le même rapport

    def __str__(self):
        return f"{self.piece.reference} (x{self.quantite}) pour OT {self.maintenance.ot.numero_ot}"


# =============================================================================
# MODÈLES OPTIONNELS (Gestion de stock avancée)
# =============================================================================

class Emplacement(models.Model):
    """Représente un emplacement de stockage physique."""
    id = models.AutoField(primary_key=True)
    nom = models.CharField(max_length=100, unique=True)
    type = models.CharField(max_length=50, blank=True, null=True, help_text="Ex: 'Rack', 'Armoire', 'Zone'")
    allee = models.CharField(max_length=50, blank=True, null=True)
    etagere = models.CharField(max_length=50, blank=True, null=True)
    niveau = models.CharField(max_length=50, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'emplacement'

    def __str__(self):
        return self.nom


class TypeMouvement(models.Model):
    """Définit les types de mouvements de stock (ex: 'Entrée', 'Sortie', 'Inventaire')."""
    id = models.AutoField(primary_key=True)
    nom = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True, null=True)
    impact_stock = models.IntegerField(help_text="1 pour une entrée, -1 pour une sortie")
    actif = models.BooleanField(default=True, help_text="Indique si le type de mouvement est actif")

    class Meta:
        managed = False
        db_table = 'type_mouvement'

    def __str__(self):
        return self.nom


class MouvementStock(models.Model):
    """Trace chaque mouvement de stock d'une pièce."""
    STATUT_CHOICES = [
        ("EN_ATTENTE", "En attente"),
        ("CONFIRME", "Confirmé"),
        ("ANNULE", "Annulé"),
    ]

    id = models.AutoField(primary_key=True)
    piece = models.ForeignKey(Piece, on_delete=models.PROTECT, related_name='mouvements_stock')
    type_mouvement = models.ForeignKey(TypeMouvement, on_delete=models.PROTECT)
    quantite = models.IntegerField()
    emplacement_source = models.ForeignKey(Emplacement, on_delete=models.SET_NULL, blank=True, null=True, related_name='mouvements_source')
    emplacement_destination = models.ForeignKey(Emplacement, on_delete=models.SET_NULL, blank=True, null=True, related_name='mouvements_destination')
    utilisateur = models.ForeignKey(Utilisateur, on_delete=models.SET_NULL, blank=True, null=True, related_name='mouvements_stock_realises')
    date_mouvement = models.DateTimeField(auto_now_add=True)
    reference_document = models.CharField(max_length=100, blank=True, null=True, help_text="Ex: 'Bon de livraison 123', 'OT 456'")
    commentaire = models.TextField(blank=True, null=True)
    cout_unitaire = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    cout_total = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    stock_avant = models.IntegerField()
    stock_apres = models.IntegerField()
    valide = models.BooleanField(default=True, help_text="Indique si le mouvement est validé")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    statut_mouvement = models.CharField(max_length=20, choices=STATUT_CHOICES, default="CONFIRME")

    class Meta:
        managed = False
        db_table = 'mouvement_stock'
        ordering = ['-date_mouvement']

    def __str__(self):
        return f"{self.type_mouvement.nom} - {self.piece.reference} (x{self.quantite})"
