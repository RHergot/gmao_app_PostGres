"""
Serializers pour l'API mobile GMAO
Gestion de la sérialisation/désérialisation des modèles Django
"""

from rest_framework import serializers
from .models import (
    OrdreTravail,
    Technicien,
    Piece,
    Maintenance,
    MouvementStock,
    Machine,
)


class TechnicienSerializer(serializers.ModelSerializer):
    """Serializer pour les techniciens"""

    nom_complet = serializers.ReadOnlyField()
    equipe_nom = serializers.CharField(source="equipe.nom", read_only=True)

    class Meta:
        model = Technicien
        fields = [
            "id_technicien",
            "nom",
            "prenom",
            "nom_complet",
            "contact",
            "qualification",
            "cout_horaire",
            "equipe",
            "equipe_nom",
            "actif",
        ]
        read_only_fields = ["id_technicien", "nom_complet", "equipe_nom"]


class PieceSerializer(serializers.ModelSerializer):
    """Serializer pour les pièces détachées"""

    stock_disponible = serializers.ReadOnlyField()
    alerte_stock = serializers.ReadOnlyField()

    class Meta:
        model = Piece
        fields = [
            "id_piece",
            "nom",
            "reference",
            "stock_actuel",
            "stock_reserve",
            "stock_disponible",
            "alerte_stock",
            "stock_alerte",
            "prix_unitaire",
            "unite",
            "emplacement_stockage",
            "categorie",
            "statut",
            "fournisseur_pref",
        ]
        read_only_fields = ["id_piece", "stock_disponible", "alerte_stock"]


class MachineSerializer(serializers.ModelSerializer):
    """Serializer pour les machines"""

    site_nom = serializers.CharField(source="site.nom", read_only=True)
    fabricant_nom = serializers.CharField(source="fabricant.nom", read_only=True)
    type_machine_nom = serializers.CharField(source="type_machine.nom", read_only=True)

    class Meta:
        model = Machine
        fields = [
            "id_machine",
            "nom",
            "serial",
            "modele",
            "site",
            "site_nom",
            "fabricant",
            "fabricant_nom",
            "type_machine",
            "type_machine_nom",
            "date_installation",
            "etat",
            "localisation",
            "criticite",
        ]
        read_only_fields = [
            "id_machine",
            "site_nom",
            "fabricant_nom",
            "type_machine_nom",
        ]


class OrdreTravailSerializer(serializers.ModelSerializer):
    """Serializer pour les ordres de travail"""

    technicien_nom = serializers.CharField(
        source="technicien_assigne.nom_complet", read_only=True
    )
    machine_nom = serializers.CharField(source="machine.nom", read_only=True)
    site_nom = serializers.CharField(source="machine.site.nom", read_only=True)
    is_assignable = serializers.ReadOnlyField()
    is_en_cours = serializers.ReadOnlyField()

    class Meta:
        model = OrdreTravail
        fields = [
            "id_ot",
            "numero_ot",
            "description",
            "date_creation",
            "date_prevue",
            "duree_prevue_min",
            "statut",
            "priorite",
            "type",
            "urgence",
            "technicien_assigne",
            "technicien_nom",
            "machine",
            "machine_nom",
            "site_nom",
            "utilisateur_createur",
            "notes_planification",
            "is_assignable",
            "is_en_cours",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id_ot",
            "numero_ot",
            "date_creation",
            "created_at",
            "updated_at",
            "technicien_nom",
            "machine_nom",
            "site_nom",
            "is_assignable",
            "is_en_cours",
        ]

    def validate(self, data):
        """Validation métier des ordres de travail"""
        # Vérifier que la date prévue n'est pas dans le passé
        if "date_prevue" in data and data["date_prevue"]:
            from django.utils import timezone

            if data["date_prevue"] < timezone.now():
                raise serializers.ValidationError(
                    {"date_prevue": "La date prévue ne peut pas être dans le passé"}
                )

        # Vérifier la cohérence priorité/urgence
        if "priorite" in data and "urgence" in data:
            priorite = data["priorite"]
            urgence = data["urgence"]

            if priorite == "CRITIQUE" and urgence < 8:
                raise serializers.ValidationError(
                    {"urgence": "Une priorité CRITIQUE doit avoir une urgence >= 8"}
                )
            elif priorite == "HAUTE" and urgence < 5:
                raise serializers.ValidationError(
                    {"urgence": "Une priorité HAUTE doit avoir une urgence >= 5"}
                )

        return data


class MaintenanceSerializer(serializers.ModelSerializer):
    """Serializer pour les rapports de maintenance"""

    duree_calculee = serializers.ReadOnlyField()
    technicien_nom = serializers.CharField(
        source="technicien.nom_complet", read_only=True
    )
    ot_numero = serializers.CharField(source="ot.numero_ot", read_only=True)
    machine_nom = serializers.CharField(source="machine.nom", read_only=True)

    class Meta:
        model = Maintenance
        fields = [
            "id_maintenance",
            "ot",
            "ot_numero",
            "machine",
            "machine_nom",
            "technicien",
            "technicien_nom",
            "date_debut_reelle",
            "date_fin_reelle",
            "duree_calculee",
            "duree_intervention_h",
            "type_reel",
            "description_travaux",
            "resultat",
            "notes_technicien",
            "cout_main_oeuvre",
            "cout_pieces_internes",
            "cout_pieces_externes",
            "cout_autres_frais",
            "cout_total",
            "evaluation_qualite",
            "impact_production",
            "created_at",
        ]
        read_only_fields = [
            "id_maintenance",
            "duree_calculee",
            "technicien_nom",
            "ot_numero",
            "machine_nom",
            "created_at",
        ]

    def validate(self, data):
        """Validation métier des rapports de maintenance"""
        # Vérifier que la date de fin est après la date de début
        if data.get("date_debut_reelle") and data.get("date_fin_reelle"):
            if data["date_fin_reelle"] <= data["date_debut_reelle"]:
                raise serializers.ValidationError(
                    {
                        "date_fin_reelle": "La date de fin doit être postérieure à la date de début"
                    }
                )

        # Vérifier la cohérence de l'évaluation qualité
        if "evaluation_qualite" in data and data["evaluation_qualite"]:
            if not (1 <= data["evaluation_qualite"] <= 10):
                raise serializers.ValidationError(
                    {
                        "evaluation_qualite": "L'évaluation qualité doit être entre 1 et 10"
                    }
                )

        return data


class MouvementStockSerializer(serializers.ModelSerializer):
    """Serializer pour les mouvements de stock"""

    piece_nom = serializers.CharField(source="piece.nom", read_only=True)
    type_mouvement_nom = serializers.CharField(
        source="type_mouvement.nom", read_only=True
    )
    utilisateur_nom = serializers.CharField(
        source="utilisateur.nom_complet", read_only=True
    )

    class Meta:
        model = MouvementStock
        fields = [
            "id",
            "piece",
            "piece_nom",
            "type_mouvement",
            "type_mouvement_nom",
            "quantite",
            "emplacement_source",
            "emplacement_destination",
            "utilisateur",
            "utilisateur_nom",
            "date_mouvement",
            "reference_document",
            "commentaire",
            "cout_unitaire",
            "cout_total",
            "stock_avant",
            "stock_apres",
            "valide",
            "statut_mouvement",
        ]
        read_only_fields = [
            "id",
            "piece_nom",
            "type_mouvement_nom",
            "utilisateur_nom",
            "date_mouvement",
            "stock_avant",
            "stock_apres",
        ]

    def validate_quantite(self, value):
        """Validation de la quantité"""
        if value <= 0:
            raise serializers.ValidationError("La quantité doit être positive")
        return value


class ReservationPieceSerializer(serializers.Serializer):
    """Serializer pour la réservation de pièces"""

    piece_id = serializers.IntegerField()
    quantite = serializers.IntegerField(min_value=1)
    commentaire = serializers.CharField(
        max_length=500, required=False, allow_blank=True
    )

    def validate_piece_id(self, value):
        """Vérifier que la pièce existe"""
        try:
            piece = Piece.objects.get(id_piece=value)
            if not piece.actif:
                raise serializers.ValidationError("Cette pièce n'est plus active")
        except Piece.DoesNotExist:
            raise serializers.ValidationError("Pièce introuvable")
        return value

    def validate(self, data):
        """Validation globale de la réservation"""
        try:
            piece = Piece.objects.get(id_piece=data["piece_id"])
            if data["quantite"] > piece.stock_disponible:
                raise serializers.ValidationError(
                    f"Stock insuffisant. Disponible: {piece.stock_disponible}, "
                    f"Demandé: {data['quantite']}"
                )
        except Piece.DoesNotExist:
            pass  # Déjà géré dans validate_piece_id

        return data


class RapportInterventionSerializer(serializers.Serializer):
    """Serializer pour la soumission de rapport d'intervention"""

    ordre_travail_id = serializers.IntegerField()
    date_debut = serializers.DateTimeField()
    date_fin = serializers.DateTimeField()
    description_travaux = serializers.CharField(max_length=2000)
    pieces_utilisees = serializers.CharField(
        max_length=1000, required=False, allow_blank=True
    )
    observations = serializers.CharField(
        max_length=1000, required=False, allow_blank=True
    )
    statut_final = serializers.ChoiceField(
        choices=[
            ("RESOLU", "Résolu"),
            ("PARTIELLEMENT_RESOLU", "Partiellement résolu"),
            ("NON_RESOLU", "Non résolu"),
            ("REPORTE", "Reporté"),
        ]
    )

    def validate_ordre_travail_id(self, value):
        """Vérifier que l'OT existe et est assigné au technicien"""
        try:
            ot = OrdreTravail.objects.get(id_ot=value)
            # Note: La vérification du technicien sera faite dans la vue
            if ot.statut not in ["ASSIGNE", "EN_COURS"]:
                raise serializers.ValidationError(
                    "Cet ordre de travail ne peut pas être modifié"
                )
        except OrdreTravail.DoesNotExist:
            raise serializers.ValidationError("Ordre de travail introuvable")
        return value

    def validate(self, data):
        """Validation globale du rapport"""
        if data["date_fin"] <= data["date_debut"]:
            raise serializers.ValidationError(
                "La date de fin doit être postérieure à la date de début"
            )
        return data
