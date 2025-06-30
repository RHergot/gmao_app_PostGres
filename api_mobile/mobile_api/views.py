"""
Vues et ViewSets pour l'API mobile GMAO
Gestion des endpoints REST avec authentification et permissions
"""

from django.shortcuts import render
from django.utils import timezone
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import api_view, action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters

from .models import (
    OrdreTravail,
    Technicien,
    Piece,
    Utilisateur,
    Maintenance,
    MouvementStock,
    Machine,
    Site,
    Equipe,
    TypeMouvement,
)
from .serializers import (
    OrdreTravailSerializer,
    TechnicienSerializer,
    PieceSerializer,
    MaintenanceSerializer,
    MouvementStockSerializer,
    MachineSerializer,
    ReservationPieceSerializer,
    RapportInterventionSerializer,
)


@api_view(["GET"])
def api_status(request):
    """
    Endpoint de test pour vérifier que l'API fonctionne
    """
    return Response(
        {
            "status": "success",
            "message": "API GMAO Mobile opérationnelle",
            "version": "1.0.0",
            "timestamp": timezone.now().isoformat(),
        },
        status=status.HTTP_200_OK,
    )


class TechnicienViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet pour les techniciens (lecture seule)
    """

    # Utilisation d'extra() pour forcer le type INTEGER sur le champ actif
    queryset = Technicien.objects.extra(where=["actif = %s"], params=[1])
    serializer_class = TechnicienSerializer
    permission_classes = [AllowAny]  # Temporaire pour les tests
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ["equipe", "qualification"]
    search_fields = ["nom", "prenom", "contact"]

    def get_queryset(self):
        """Filtrer les techniciens selon l'utilisateur connecté"""
        queryset = super().get_queryset()
        # Pour l'instant, retourner tous les techniciens actifs
        # TODO: Filtrer selon les permissions de l'utilisateur connecté
        return queryset


class PieceViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet pour les pièces détachées (lecture seule + actions)
    """

    queryset = Piece.objects.filter(statut="ACTIF")
    serializer_class = PieceSerializer
    permission_classes = [AllowAny]  # Temporaire pour les tests
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ["emplacement_stockage", "unite", "categorie"]
    search_fields = ["nom", "reference"]

    def get_queryset(self):
        """Filtrer les pièces disponibles"""
        queryset = super().get_queryset()
        # Optionnel: filtrer par stock disponible > 0
        stock_only = self.request.query_params.get("stock_only", None)
        if stock_only == "true":
            queryset = queryset.filter(stock_actuel__gt=0)
        return queryset

    @action(detail=True, methods=["post"])
    def reserver(self, request, pk=None):
        """
        Action pour réserver une pièce
        """
        piece = self.get_object()
        serializer = ReservationPieceSerializer(data=request.data)

        if serializer.is_valid():
            quantite = serializer.validated_data["quantite"]
            commentaire = serializer.validated_data.get("commentaire", "")

            # Vérifier le stock disponible
            if quantite > piece.stock_disponible:
                return Response(
                    {
                        "error": f"Stock insuffisant. Disponible: {piece.stock_disponible}"
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # TODO: Créer le mouvement de réservation
            # Pour l'instant, simuler la réservation
            return Response(
                {
                    "success": True,
                    "message": f"{quantite} unité(s) de {piece.nom} réservée(s)",
                    "piece": piece.nom,
                    "quantite_reservee": quantite,
                    "stock_restant": piece.stock_disponible - quantite,
                },
                status=status.HTTP_200_OK,
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class MachineViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet pour les machines (lecture seule)
    """

    queryset = Machine.objects.all()
    serializer_class = MachineSerializer
    permission_classes = [AllowAny]  # Temporaire pour les tests
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ["site", "fabricant", "etat"]
    search_fields = ["nom", "serial", "modele"]


class OrdreTravailViewSet(viewsets.ModelViewSet):
    """
    ViewSet pour les ordres de travail
    """

    queryset = OrdreTravail.objects.all()
    serializer_class = OrdreTravailSerializer
    permission_classes = [AllowAny]  # Temporaire pour les tests
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_fields = [
        "statut",
        "priorite",
        "type",
        "technicien_assigne",
        "machine__site",
    ]
    search_fields = ["numero_ot", "description"]
    ordering_fields = ["date_creation", "date_prevue", "priorite"]
    ordering = ["-date_creation"]

    def get_queryset(self):
        """
        Filtrer les OT selon le technicien connecté
        """
        queryset = super().get_queryset()

        # TODO: Filtrer par technicien assigné quand l'auth sera active
        technicien_id = self.request.query_params.get("mon_technicien", None)
        if technicien_id:
            queryset = queryset.filter(technicien_assigne_id=technicien_id)

        return queryset.order_by("-date_creation")

    @action(detail=True, methods=["post"])
    def commencer(self, request, pk=None):
        """
        Action pour commencer un ordre de travail
        """
        ot = self.get_object()

        if ot.statut != "ASSIGNE":
            return Response(
                {"error": "Cet ordre de travail ne peut pas être commencé"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Mettre à jour le statut et la date de début
        ot.statut = "EN_COURS"
        ot.date_debut = timezone.now()
        ot.save()

        return Response(
            {
                "success": True,
                "message": f"Ordre de travail {ot.numero_ot} commencé",
                "statut": ot.statut,
                "date_debut": ot.date_debut,
            },
            status=status.HTTP_200_OK,
        )

    @action(detail=True, methods=["post"])
    def terminer(self, request, pk=None):
        """
        Action pour terminer un ordre de travail avec rapport
        """
        ot = self.get_object()

        if ot.statut != "EN_COURS":
            return Response(
                {"error": "Cet ordre de travail ne peut pas être terminé"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Valider les données du rapport
        rapport_data = request.data.copy()
        rapport_data["ordre_travail_id"] = ot.id_ot

        serializer = RapportInterventionSerializer(data=rapport_data)
        if serializer.is_valid():
            # Mettre à jour l'OT
            ot.statut = "TERMINE"
            ot.date_fin = serializer.validated_data["date_fin"]
            ot.save()

            # TODO: Créer l'enregistrement Maintenance
            # Pour l'instant, simuler la création

            return Response(
                {
                    "success": True,
                    "message": f"Ordre de travail {ot.numero_ot} terminé",
                    "statut": ot.statut,
                    "date_fin": ot.date_fin,
                },
                status=status.HTTP_200_OK,
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class MaintenanceViewSet(viewsets.ModelViewSet):
    """
    ViewSet pour les rapports de maintenance
    """

    queryset = Maintenance.objects.all()
    serializer_class = MaintenanceSerializer
    permission_classes = [AllowAny]  # Temporaire pour les tests
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ["technicien", "ot", "type_reel"]
    ordering_fields = ["created_at", "date_debut_reelle"]
    ordering = ["-created_at"]

    def get_queryset(self):
        """Filtrer les rapports selon le technicien connecté"""
        queryset = super().get_queryset()

        # TODO: Filtrer par technicien connecté
        technicien_id = self.request.query_params.get("mon_technicien", None)
        if technicien_id:
            queryset = queryset.filter(technicien_id=technicien_id)

        return queryset


class MouvementStockViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet pour les mouvements de stock (lecture seule)
    """

    queryset = MouvementStock.objects.all()
    serializer_class = MouvementStockSerializer
    permission_classes = [AllowAny]  # Temporaire pour les tests
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ["piece", "type_mouvement", "utilisateur", "valide"]
    ordering_fields = ["date_mouvement"]
    ordering = ["-date_mouvement"]

    def get_queryset(self):
        """Filtrer les mouvements récents"""
        queryset = super().get_queryset()

        # Limiter aux mouvements récents par défaut
        recent_only = self.request.query_params.get("recent_only", "true")
        if recent_only == "true":
            # Derniers 30 jours
            from datetime import timedelta

            date_limite = timezone.now() - timedelta(days=30)
            queryset = queryset.filter(date_mouvement__gte=date_limite)

        return queryset
