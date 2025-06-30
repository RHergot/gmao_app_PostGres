"""
Serializers pour l'application gmao_web.

Ces serializers, basés sur Django Rest Framework, définissent la manière dont les
objets complexes de Django (comme les modèles) sont convertis en types de données
natifs Python (comme les dictionnaires), qui peuvent ensuite être facilement rendus
en JSON pour l'API.

Chaque serializer est spécialisé pour un modèle ou un usage spécifique.
"""

from rest_framework import serializers
from mobile_api.models import (
    Maintenance,
    Technicien,
    Piece,
    InterventionPiece,
)


class MaintenanceReportSerializer(serializers.ModelSerializer):
    """
    Serializer pour la création et la mise à jour des rapports de maintenance.

    Ce serializer est utilisé pour valider et sauvegarder les données soumises
    depuis le formulaire de rapport de maintenance. Il calcule également la durée
    de l'intervention automatiquement.
    """
    class Meta:
        model = Maintenance
        fields = [
            "id_maintenance", "ot", "technicien", "date_debut_reelle",
            "date_fin_reelle", "type_reel", "description_travaux", "resultat",
            "evaluation_qualite", "impact_production", "notes_technicien",
            "cout_total",
        ]
        extra_kwargs = {
            # Ces champs sont protégés en écriture et gérés par le système.
            "id_maintenance": {"read_only": True},
            "cout_total": {"read_only": True},
        }

    def create(self, validated_data):
        """
        Surcharge de la méthode create pour ajouter une logique métier.

        Calcule et enregistre la durée de l'intervention en heures (`duree_intervention_h`)
        avant de créer l'objet Maintenance en base de données.
        """
        if "date_debut_reelle" in validated_data and "date_fin_reelle" in validated_data:
            debut = validated_data["date_debut_reelle"]
            fin = validated_data["date_fin_reelle"]
            if fin > debut:
                duree_secondes = (fin - debut).total_seconds()
                validated_data["duree_intervention_h"] = round(duree_secondes / 3600, 2)

        return super().create(validated_data)


class InterventionPieceSerializer(serializers.ModelSerializer):
    """
    Serializer pour les pièces détachées utilisées dans une intervention.

    Enrichit les données de l'intervention avec des informations lisibles
    provenant du modèle `Piece` associé (nom, référence, prix).
    """
    # Champs en lecture seule pour afficher les détails de la pièce
    piece_nom = serializers.CharField(source="piece.nom", read_only=True)
    piece_reference = serializers.CharField(source="piece.reference", read_only=True)
    piece_prix = serializers.DecimalField(
        source="piece.prix_unitaire", max_digits=10, decimal_places=2, read_only=True
    )

    class Meta:
        model = InterventionPiece
        fields = [
            "id", "piece_id", "quantite", "lot_numero", "cout_unitaire",
            "cout_total", "piece_nom", "piece_reference", "piece_prix",
        ]


class TechnicienSimpleSerializer(serializers.ModelSerializer):
    """
    Serializer simplifié pour afficher les informations de base d'un technicien.

    Utilisé pour peupler les listes déroulantes dans le formulaire de maintenance,
    en ne renvoyant que les informations strictement nécessaires.
    """
    # Propriété calculée dans le modèle Technicien
    nom_complet = serializers.CharField(read_only=True)

    class Meta:
        model = Technicien
        fields = ["id_technicien", "nom", "prenom", "nom_complet", "actif"]


class PieceSimpleSerializer(serializers.ModelSerializer):
    """
    Serializer simplifié pour afficher les informations de base d'une pièce.

    Utilisé pour peupler la liste des pièces disponibles dans le formulaire,
    en affichant les détails pertinents pour la sélection.
    """
    class Meta:
        model = Piece
        fields = [
            "id_piece", "reference", "nom", "prix_unitaire", "unite",
            "stock_actuel", "statut",
        ]
