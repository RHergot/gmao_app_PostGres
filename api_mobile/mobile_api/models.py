from django.db import models
from django.contrib.auth.models import AbstractUser

# Create your models here.

# ===== MODÈLES PRINCIPAUX POUR L'API MOBILE =====

class Site(models.Model):
    """Sites industriels"""
    id_site = models.AutoField(primary_key=True)
    nom = models.CharField(max_length=255, unique=True)
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
    """Fabricants d'équipements"""
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
    """Types de machines"""
    id_type_machine = models.AutoField(primary_key=True)
    nom = models.CharField(max_length=255, unique=True)
    description = models.TextField(blank=True, null=True)
    categorie = models.CharField(max_length=100, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'type_machine'

    def __str__(self):
        return self.nom


class Machine(models.Model):
    """Machines et équipements"""
    id_machine = models.AutoField(primary_key=True)
    nom = models.CharField(max_length=255)
    serial = models.CharField(max_length=255, unique=True, blank=True, null=True)
    modele = models.CharField(max_length=255, blank=True, null=True)
    date_installation = models.DateField(blank=True, null=True)
    localisation = models.CharField(max_length=255, blank=True, null=True)
    etat = models.CharField(max_length=50, blank=True, null=True)
    informations_techniques = models.TextField(blank=True, null=True)
    type_machine = models.ForeignKey(TypeMachine, on_delete=models.PROTECT)
    site = models.ForeignKey(Site, on_delete=models.PROTECT)
    fabricant = models.ForeignKey(Fabricant, on_delete=models.PROTECT)
    parent_machine = models.ForeignKey('self', on_delete=models.CASCADE, blank=True, null=True)
    criticite = models.CharField(max_length=50, blank=True, null=True)
    garantie_fin = models.DateField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        managed = False
        db_table = 'machine'

    def __str__(self):
        return f"{self.nom} ({self.serial or 'N/A'})"


class Equipe(models.Model):
    """Équipes de techniciens"""
    id_equipe = models.AutoField(primary_key=True)
    nom = models.CharField(max_length=255, unique=True)
    domaine_expertise = models.CharField(max_length=255, blank=True, null=True)
    responsable = models.ForeignKey('Technicien', on_delete=models.SET_NULL, blank=True, null=True, related_name='equipes_dirigees')

    class Meta:
        managed = False
        db_table = 'equipe'

    def __str__(self):
        return self.nom


class Technicien(models.Model):
    """Techniciens de maintenance"""
    id_technicien = models.AutoField(primary_key=True)
    nom = models.CharField(max_length=255)
    prenom = models.CharField(max_length=255, blank=True, null=True)
    qualification = models.CharField(max_length=255, blank=True, null=True)
    contact = models.CharField(max_length=255, blank=True, null=True)
    cout_horaire = models.DecimalField(max_digits=8, decimal_places=2, blank=True, null=True)
    equipe = models.ForeignKey(Equipe, on_delete=models.SET_NULL, blank=True, null=True)
    actif = models.BooleanField(default=True)

    class Meta:
        managed = False
        db_table = 'technicien'

    def __str__(self):
        return f"{self.nom} {self.prenom or ''}".strip()

    @property
    def nom_complet(self):
        return f"{self.nom} {self.prenom or ''}".strip()


class Utilisateur(models.Model):
    """Utilisateurs du système"""
    id_utilisateur = models.AutoField(primary_key=True)
    login = models.CharField(max_length=255, unique=True)
    mot_de_passe_hash = models.CharField(max_length=255)
    nom_complet = models.CharField(max_length=255, blank=True, null=True)
    role = models.CharField(max_length=50)
    email = models.EmailField(unique=True, blank=True, null=True)
    actif = models.BooleanField(default=True)
    derniere_connexion = models.DateTimeField(blank=True, null=True)
    technicien = models.ForeignKey(Technicien, on_delete=models.SET_NULL, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        managed = False
        db_table = 'utilisateur'

    def __str__(self):
        return f"{self.nom_complet or self.login} ({self.role})"

    @property
    def is_technicien(self):
        return self.technicien is not None


class OrdreTravail(models.Model):
    """Ordres de travail"""
    STATUT_CHOICES = [
        ('PLANIFIE', 'Planifié'),
        ('ASSIGNE', 'Assigné'),
        ('EN_COURS', 'En cours'),
        ('TERMINE', 'Terminé'),
        ('ANNULE', 'Annulé'),
    ]
    
    TYPE_CHOICES = [
        ('PREVENTIF', 'Préventif'),
        ('CORRECTIF', 'Correctif'),
        ('AMELIORATION', 'Amélioration'),
    ]
    
    PRIORITE_CHOICES = [
        ('BASSE', 'Basse'),
        ('NORMALE', 'Normale'),
        ('HAUTE', 'Haute'),
        ('CRITIQUE', 'Critique'),
    ]

    id_ot = models.AutoField(primary_key=True)
    numero_ot = models.CharField(max_length=50, unique=True, blank=True, null=True)
    machine = models.ForeignKey(Machine, on_delete=models.PROTECT)
    gamme_id = models.IntegerField(blank=True, null=True)
    type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    description = models.TextField()
    date_creation = models.DateTimeField(auto_now_add=True)
    date_prevue = models.DateTimeField(blank=True, null=True)
    duree_prevue_min = models.IntegerField(blank=True, null=True)
    priorite = models.CharField(max_length=20, choices=PRIORITE_CHOICES, default='NORMALE')
    urgence = models.IntegerField(default=0)
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default='PLANIFIE')
    technicien_assigne = models.ForeignKey(Technicien, on_delete=models.SET_NULL, blank=True, null=True)
    utilisateur_createur = models.ForeignKey(Utilisateur, on_delete=models.PROTECT)
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
        return self.statut in ['PLANIFIE', 'ASSIGNE']

    @property
    def is_en_cours(self):
        return self.statut == 'EN_COURS'


class Fournisseur(models.Model):
    """Fournisseurs de pièces"""
    id_fournisseur = models.AutoField(primary_key=True)
    nom = models.CharField(max_length=255, unique=True)
    contact = models.TextField(blank=True, null=True)
    adresse = models.TextField(blank=True, null=True)
    telephone = models.CharField(max_length=50, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    delai_livraison_moyen_j = models.IntegerField(blank=True, null=True)
    devise = models.CharField(max_length=10, blank=True, null=True)
    note_qualite = models.DecimalField(max_digits=3, decimal_places=1, blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        managed = False
        db_table = 'fournisseur'

    def __str__(self):
        return self.nom


class Piece(models.Model):
    """Pièces détachées"""
    STATUT_CHOICES = [
        ('ACTIF', 'Actif'),
        ('OBSOLETE', 'Obsolète'),
        ('DISCONTINUE', 'Discontinué'),
    ]

    id_piece = models.AutoField(primary_key=True)
    reference = models.CharField(max_length=255, unique=True)
    nom = models.CharField(max_length=255)
    fournisseur_pref = models.ForeignKey(Fournisseur, on_delete=models.SET_NULL, blank=True, null=True)
    prix_unitaire = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    stock_alerte = models.IntegerField(blank=True, null=True)
    stock_actuel = models.IntegerField(default=0)
    stock_reserve = models.IntegerField(default=0)
    unite = models.CharField(max_length=50)
    categorie = models.CharField(max_length=100, blank=True, null=True)
    emplacement_stockage = models.CharField(max_length=255, blank=True, null=True)
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default='ACTIF')
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        managed = False
        db_table = 'piece'

    def __str__(self):
        return f"{self.reference} - {self.nom}"

    @property
    def stock_disponible(self):
        return max(0, self.stock_actuel - self.stock_reserve)

    @property
    def alerte_stock(self):
        return self.stock_alerte and self.stock_actuel <= self.stock_alerte


class TypeMouvement(models.Model):
    """Types de mouvements de stock"""
    id = models.AutoField(primary_key=True)
    nom = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True, null=True)
    impact_stock = models.IntegerField()  # 1 pour entrée, -1 pour sortie
    actif = models.BooleanField(default=True)

    class Meta:
        managed = False
        db_table = 'type_mouvement'

    def __str__(self):
        return self.nom


class Emplacement(models.Model):
    """Emplacements de stockage"""
    id = models.AutoField(primary_key=True)
    nom = models.CharField(max_length=100, unique=True)
    type = models.CharField(max_length=50, blank=True, null=True)
    allee = models.CharField(max_length=50, blank=True, null=True)
    etagere = models.CharField(max_length=50, blank=True, null=True)
    niveau = models.CharField(max_length=50, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'emplacement'

    def __str__(self):
        return self.nom


class MouvementStock(models.Model):
    """Mouvements de stock - Structure réelle de la DB"""
    STATUT_CHOICES = [
        ('EN_ATTENTE', 'En attente'),
        ('CONFIRME', 'Confirmé'),
        ('ANNULE', 'Annulé'),
    ]

    id = models.AutoField(primary_key=True)
    piece = models.ForeignKey(Piece, on_delete=models.PROTECT)
    type_mouvement = models.ForeignKey(TypeMouvement, on_delete=models.PROTECT)
    quantite = models.IntegerField()
    emplacement_source = models.ForeignKey(Emplacement, on_delete=models.SET_NULL, blank=True, null=True, related_name='mouvements_source')
    emplacement_destination = models.ForeignKey(Emplacement, on_delete=models.SET_NULL, blank=True, null=True, related_name='mouvements_destination')
    utilisateur = models.ForeignKey(Utilisateur, on_delete=models.SET_NULL, blank=True, null=True)
    date_mouvement = models.DateTimeField(auto_now_add=True)
    reference_document = models.CharField(max_length=100, blank=True, null=True)
    commentaire = models.TextField(blank=True, null=True)
    cout_unitaire = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    cout_total = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    stock_avant = models.IntegerField()
    stock_apres = models.IntegerField()
    valide = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    statut_mouvement = models.CharField(max_length=20, choices=STATUT_CHOICES, default='CONFIRME')

    class Meta:
        managed = False
        db_table = 'mouvement_stock'
        ordering = ['-date_mouvement']

    def __str__(self):
        return f"{self.type_mouvement.nom} - {self.piece.reference} ({self.quantite})"


class Maintenance(models.Model):
    """Rapports d'intervention de maintenance"""
    TYPE_CHOICES = [
        ('PREVENTIF', 'Préventif'),
        ('CORRECTIF', 'Correctif'),
        ('AMELIORATION', 'Amélioration'),
    ]

    id_maintenance = models.AutoField(primary_key=True)
    ot = models.OneToOneField(OrdreTravail, on_delete=models.CASCADE)
    machine = models.ForeignKey(Machine, on_delete=models.PROTECT, blank=True, null=True)
    technicien = models.ForeignKey(Technicien, on_delete=models.PROTECT)
    date_debut_reelle = models.DateTimeField()
    date_fin_reelle = models.DateTimeField()
    duree_intervention_h = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    type_reel = models.CharField(max_length=20, choices=TYPE_CHOICES)
    description_travaux = models.TextField()
    resultat = models.TextField()
    cout_manuel_v1 = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    cout_main_oeuvre = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    cout_pieces_internes = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    cout_pieces_externes = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    cout_autres_frais = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    cout_total = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    evaluation_qualite = models.IntegerField(blank=True, null=True)
    impact_production = models.CharField(max_length=255, blank=True, null=True)
    notes_technicien = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = False
        db_table = 'maintenance'

    def __str__(self):
        return f"Maintenance {self.ot.numero_ot} - {self.technicien.nom_complet}"

    @property
    def duree_calculee(self):
        if self.date_debut_reelle and self.date_fin_reelle:
            delta = self.date_fin_reelle - self.date_debut_reelle
            return round(delta.total_seconds() / 3600, 2)
        return None


class InterventionPiece(models.Model):
    """Pièces utilisées lors d'une intervention"""
    id = models.AutoField(primary_key=True)
    maintenance = models.ForeignKey(Maintenance, on_delete=models.CASCADE, related_name='pieces_utilisees')
    piece = models.ForeignKey(Piece, on_delete=models.PROTECT)
    quantite = models.IntegerField()
    lot = models.CharField(max_length=100, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'intervention_piece'
        unique_together = [['maintenance', 'piece']]

    def __str__(self):
        return f"{self.piece.reference} x{self.quantite} - {self.maintenance.ot.numero_ot}"
