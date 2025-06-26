"""
Serializers pour l'interface web GMAO
"""
from rest_framework import serializers
from mobile_api.models import OrdreTravail, Maintenance, Technicien, Piece, InterventionPiece

class MaintenanceReportSerializer(serializers.ModelSerializer):
    """Serializer pour créer/modifier un rapport de maintenance"""
    
    class Meta:
        model = Maintenance
        fields = [
            'id_maintenance', 'id_ot', 'technicien_id', 'date_debut', 'date_fin',
            'type_reel', 'travaux_realises', 'resultat', 'evaluation_qualite',
            'impact_production', 'notes', 'cout_total'
        ]
        extra_kwargs = {
            'id_maintenance': {'read_only': True},
            'cout_total': {'read_only': True}
        }

class InterventionPieceSerializer(serializers.ModelSerializer):
    """Serializer pour les pièces utilisées dans une intervention"""
    piece_nom = serializers.CharField(source='piece.nom', read_only=True)
    piece_reference = serializers.CharField(source='piece.reference', read_only=True)
    piece_prix = serializers.DecimalField(source='piece.prix_unitaire', max_digits=10, decimal_places=2, read_only=True)
    
    class Meta:
        model = InterventionPiece
        fields = [
            'id', 'piece_id', 'quantite', 'lot_numero', 'cout_unitaire', 'cout_total',
            'piece_nom', 'piece_reference', 'piece_prix'
        ]

class TechnicienSimpleSerializer(serializers.ModelSerializer):
    """Serializer simple pour les techniciens"""
    nom_complet = serializers.CharField(read_only=True)
    
    class Meta:
        model = Technicien
        fields = ['id_technicien', 'nom', 'prenom', 'nom_complet', 'statut']

class PieceSimpleSerializer(serializers.ModelSerializer):
    """Serializer simple pour les pièces"""
    stock_disponible = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = Piece
        fields = [
            'id_piece', 'reference', 'nom', 'prix_unitaire', 'unite',
            'stock_actuel', 'stock_disponible', 'statut'
        ]
