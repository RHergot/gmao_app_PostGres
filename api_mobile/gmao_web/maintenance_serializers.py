"""
Serializers pour les opérations CRUD sur les rapports de maintenance.

Ce fichier contient les serializers spécialisés pour :
- La lecture détaillée des rapports de maintenance
- La modification des rapports existants
- La gestion des pièces associées
"""

from rest_framework import serializers
from mobile_api.models import (
    Maintenance, 
    OrdreTravail, 
    Technicien, 
    Machine, 
    InterventionPiece, 
    Piece
)


class MaintenanceListSerializer(serializers.ModelSerializer):
    """Serializer pour la liste des rapports de maintenance (vue résumée)."""
    
    # Champs calculés/relationnels
    ot_numero = serializers.CharField(source='ot.numero_ot', read_only=True)
    machine_nom = serializers.CharField(source='machine.nom', read_only=True)
    technicien_nom = serializers.CharField(source='technicien.nom_complet', read_only=True)
    duree_calculee = serializers.SerializerMethodField()
    
    class Meta:
        model = Maintenance
        fields = [
            'id_maintenance',
            'ot_numero',
            'machine_nom', 
            'technicien_nom',
            'date_debut_reelle',
            'date_fin_reelle',
            'duree_calculee',
            'type_reel',
            'resultat',
            'cout_total',
            'evaluation_qualite',
            'created_at'
        ]
    
    def get_duree_calculee(self, obj):
        """Calcule la durée de l'intervention en heures."""
        return obj.duree_calculee


class InterventionPieceDetailSerializer(serializers.ModelSerializer):
    """Serializer pour les pièces utilisées dans une maintenance."""
    
    piece_reference = serializers.CharField(source='piece.reference', read_only=True)
    piece_nom = serializers.CharField(source='piece.nom', read_only=True)
    prix_unitaire = serializers.FloatField(source='piece.prix_unitaire', read_only=True)
    cout_total_piece = serializers.SerializerMethodField()
    
    class Meta:
        model = InterventionPiece
        fields = [
            'id',
            'piece_reference',
            'piece_nom',
            'quantite',
            'lot',
            'prix_unitaire',
            'cout_total_piece'
        ]
    
    def get_cout_total_piece(self, obj):
        """Calcule le coût total pour cette pièce."""
        prix = obj.piece.prix_unitaire or 0.0
        return float(obj.quantite) * prix


class MaintenanceDetailSerializer(serializers.ModelSerializer):
    """Serializer pour le détail complet d'un rapport de maintenance."""
    
    # Informations de l'OT
    ot_numero = serializers.CharField(source='ot.numero_ot', read_only=True)
    ot_description = serializers.CharField(source='ot.description', read_only=True)
    ot_statut = serializers.CharField(source='ot.statut', read_only=True)
    
    # Informations de la machine
    machine_nom = serializers.CharField(source='machine.nom', read_only=True)
    machine_localisation = serializers.CharField(source='machine.localisation', read_only=True)
    
    # Informations du technicien
    technicien_nom = serializers.CharField(source='technicien.nom_complet', read_only=True)
    
    # Pièces utilisées
    pieces_utilisees = InterventionPieceDetailSerializer(many=True, read_only=True)
    
    # Champs calculés
    duree_calculee = serializers.SerializerMethodField()
    
    class Meta:
        model = Maintenance
        fields = [
            'id_maintenance',
            # Informations OT
            'ot_numero',
            'ot_description', 
            'ot_statut',
            # Informations machine
            'machine_nom',
            'machine_localisation',
            # Informations technicien
            'technicien_nom',
            # Détails de l'intervention
            'date_debut_reelle',
            'date_fin_reelle',
            'duree_calculee',
            'duree_intervention_h',
            'type_reel',
            'description_travaux',
            'resultat',
            # Coûts
            'cout_total',
            'cout_main_oeuvre',
            'cout_pieces_internes',
            'cout_pieces_externes',
            'cout_autres_frais',
            # Évaluation
            'evaluation_qualite',
            'impact_production',
            'notes_technicien',
            # Pièces
            'pieces_utilisees',
            # Métadonnées
            'created_at'
        ]
    
    def get_duree_calculee(self, obj):
        """Calcule la durée de l'intervention en heures."""
        return obj.duree_calculee


class MaintenanceUpdateSerializer(serializers.ModelSerializer):
    """Serializer pour la modification d'un rapport de maintenance."""
    
    # Champs pour mise à jour des pièces (optionnel)
    pieces = serializers.ListField(
        child=serializers.DictField(), 
        write_only=True, 
        required=False,
        help_text="Liste des pièces: [{'piece_id': 1, 'quantite': 2, 'lot': '...'}]"
    )
    
    class Meta:
        model = Maintenance
        fields = [
            'technicien',
            'date_debut_reelle',
            'date_fin_reelle',
            'duree_intervention_h',
            'type_reel',
            'description_travaux',
            'resultat',
            'evaluation_qualite',
            'impact_production',
            'notes_technicien',
            'pieces'  # Pour mise à jour des pièces
        ]
    
    def validate_technicien(self, value):
        """Valide que le technicien est actif."""
        if value and not value.actif:
            raise serializers.ValidationError("Le technicien sélectionné n'est pas actif.")
        return value
    
    def validate(self, data):
        """Validations globales."""
        if 'date_debut_reelle' in data and 'date_fin_reelle' in data:
            if data['date_debut_reelle'] >= data['date_fin_reelle']:
                raise serializers.ValidationError({
                    'date_fin_reelle': 'La date de fin doit être postérieure à la date de début.'
                })
        
        if 'evaluation_qualite' in data and data['evaluation_qualite'] is not None:
            if not (1 <= data['evaluation_qualite'] <= 5):
                raise serializers.ValidationError({
                    'evaluation_qualite': 'L\'évaluation doit être comprise entre 1 et 5.'
                })
        
        return data


class InterventionPieceUpdateSerializer(serializers.ModelSerializer):
    """Serializer pour la mise à jour des pièces d'une maintenance."""
    
    class Meta:
        model = InterventionPiece
        fields = ['piece', 'quantite', 'lot']
    
    def validate_quantite(self, value):
        """Valide que la quantité est positive."""
        if value <= 0:
            raise serializers.ValidationError("La quantité doit être positive.")
        return value
