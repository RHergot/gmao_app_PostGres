"""
Vues pour l'interface web responsive GMAO Mobile
Interface en anglais avec support de traduction
"""
from django.shortcuts import render
from django.http import JsonResponse
from django.views.generic import TemplateView
from django.utils.translation import gettext as _
from django.contrib.auth.mixins import LoginRequiredMixin
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from django.db import transaction
from decimal import Decimal
from .serializers import (
    MaintenanceReportSerializer, InterventionPieceSerializer, 
    TechnicienSimpleSerializer, PieceSimpleSerializer
)

from mobile_api.models import OrdreTravail, Technicien, Machine, Piece
from mobile_api.serializers import OrdreTravailSerializer


class WorkOrdersView(TemplateView):
    """
    Vue principale pour afficher les ordres de travail en cours
    Interface read-only pour les OT avec statut "EnCours"
    """
    template_name = 'gmao_web/work_orders.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Titre de la page (traduisible)
        context['page_title'] = _('Work Orders In Progress')
        
        # Statistiques pour le dashboard (optionnel)
        context['stats'] = {
            'total_in_progress': OrdreTravail.objects.filter(statut='EnCours').count(),
            'high_priority': OrdreTravail.objects.filter(
                statut='EnCours', 
                priorite__in=['HAUTE', 'CRITIQUE']
            ).count(),
        }
        
        return context


class DashboardView(TemplateView):
    """
    Vue du dashboard principal (future extension)
    """
    template_name = 'gmao_web/dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = _('Dashboard')
        return context


class MaintenanceReportView(TemplateView):
    """Vue pour le formulaire de rapport de maintenance"""
    template_name = 'gmao_web/maintenance_report.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        ot_id = kwargs.get('ot_id')
        
        try:
            # Vérifier que l'OT existe
            ot = get_object_or_404(OrdreTravail, id_ot=ot_id)
            context['ot_id'] = ot_id
            context['work_order'] = {
                'numero_ot': ot.numero_ot,
                'description': ot.description,
                'machine_nom': ot.machine.nom if ot.machine else 'N/A',
                'site_nom': ot.machine.site.nom if ot.machine and ot.machine.site else 'N/A'
            }
            context['page_title'] = _('Maintenance Report') + f' - {ot.numero_ot}'
        except OrdreTravail.DoesNotExist:
            context['error'] = _('Work order not found')
            
        return context


@api_view(['GET'])
def work_orders_api(request):
    """
    API endpoint pour récupérer les ordres de travail
    Filtre automatiquement les OT "EnCours" pour l'interface web
    """
    # Filtrer uniquement les OT "EnCours" pour l'interface web
    queryset = OrdreTravail.objects.filter(statut='EnCours').select_related(
        'machine', 'machine__site', 'technicien_assigne'
    ).order_by('-date_creation')
    
    # Filtrage additionnel par priorité si demandé
    priority = request.GET.get('priority')
    if priority and priority != 'all':
        queryset = queryset.filter(priorite=priority.upper())
    
    # Filtrage par technicien si demandé
    technician_id = request.GET.get('technician')
    if technician_id:
        queryset = queryset.filter(technicien_assigne_id=technician_id)
    
    # Sérialisation
    serializer = OrdreTravailSerializer(queryset, many=True)
    
    return Response({
        'work_orders': serializer.data,
        'count': queryset.count(),
        'status': 'success'
    })


@api_view(['GET'])
def work_order_detail_api(request, work_order_id):
    """
    API endpoint pour récupérer les détails d'un ordre de travail
    """
    try:
        work_order = OrdreTravail.objects.select_related(
            'machine', 'machine__site', 'technicien_assigne', 'utilisateur_createur'
        ).get(id_ot=work_order_id)
        
        # Vérifier que l'OT est bien "EnCours"
        if work_order.statut != 'EnCours':
            return Response({
                'error': _('Work order is not in progress'),
                'status': 'error'
            }, status=400)
        
        serializer = OrdreTravailSerializer(work_order)
        
        return Response({
            'work_order': serializer.data,
            'status': 'success'
        })
        
    except OrdreTravail.DoesNotExist:
        return Response({
            'error': _('Work order not found'),
            'status': 'error'
        }, status=404)


@api_view(['GET'])
def technicians_api(request):
    """
    API endpoint pour récupérer la liste des techniciens actifs
    """
    technicians = Technicien.objects.filter(statut='ACTIF').order_by('nom', 'prenom')
    
    data = [{
        'id': tech.id_technicien,
        'name': tech.nom_complet,
        'email': tech.contact,
        'team': tech.equipe.nom if tech.equipe else None
    } for tech in technicians]
    
    return Response({
        'technicians': data,
        'count': len(data),
        'status': 'success'
    })


@api_view(['GET'])
def maintenance_form_data(request, ot_id):
    """Récupère les données nécessaires pour le formulaire de rapport de maintenance"""
    try:
        # Récupérer l'OT
        ot = get_object_or_404(OrdreTravail, id_ot=ot_id)
        
        # Récupérer les techniciens actifs
        techniciens = Technicien.objects.filter(statut='ACTIF').order_by('nom', 'prenom')
        
        # Récupérer les pièces disponibles (avec stock > 0)
        pieces = Piece.objects.filter(
            statut='ACTIF',
            stock_actuel__gt=0
        ).order_by('reference')
        
        # Constantes pour les choix
        type_options = ['Préventif', 'Correctif', 'Demande', 'Amélioration']
        resultat_options = ['Réparé', 'Remplacé', 'Ajusté', 'Nettoyé', 'Lubrifié', 'Inspecté']
        evaluation_options = [
            {'value': 1, 'label': '1 - Médiocre'},
            {'value': 2, 'label': '2 - Insuffisant'},
            {'value': 3, 'label': '3 - Moyen'},
            {'value': 4, 'label': '4 - Bon'},
            {'value': 5, 'label': '5 - Excellent'}
        ]
        impact_options = ['Aucun', 'Mineur', 'Majeur', 'Arrêt Production']
        
        return Response({
            'ordre_travail': {
                'id_ot': ot.id_ot,
                'numero_ot': ot.numero_ot,
                'description': ot.description,
                'machine_nom': ot.machine.nom if ot.machine else 'N/A',
                'site_nom': ot.machine.site.nom if ot.machine and ot.machine.site else 'N/A'
            },
            'techniciens': TechnicienSimpleSerializer(techniciens, many=True).data,
            'pieces': PieceSimpleSerializer(pieces, many=True).data,
            'options': {
                'types': type_options,
                'resultats': resultat_options,
                'evaluations': evaluation_options,
                'impacts': impact_options
            }
        })
        
    except Exception as e:
        return Response(
            {'error': f'Erreur lors du chargement des données: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
def maintenance_form_data_api(request, ot_id):
    """
    API endpoint pour récupérer les données nécessaires au formulaire de maintenance
    """
    try:
        # Vérifier que l'OT existe
        ot = get_object_or_404(OrdreTravail, id_ot=ot_id)
        
        # Récupérer les techniciens actifs
        techniciens = Technicien.objects.filter(actif=True).select_related('utilisateur')
        
        # Récupérer les pièces disponibles
        pieces = Piece.objects.filter(statut='ACTIF').exclude(
            stock_actuel__lte=0
        )
        
        # Préparer les données
        data = {
            'work_order': {
                'id_ot': ot.id_ot,
                'numero_ot': ot.numero_ot,
                'description': ot.description,
                'machine_nom': ot.machine.nom if ot.machine else 'N/A',
                'site_nom': ot.machine.site.nom if ot.machine and ot.machine.site else 'N/A',
                'priorite': ot.priorite,
                'type_ot': ot.type_ot
            },
            'techniciens': [
                {
                    'id': tech.id_technicien,
                    'nom_complet': tech.nom_complet,
                    'taux_horaire': float(tech.taux_horaire) if tech.taux_horaire else 0.0
                }
                for tech in techniciens
            ],
            'pieces': [
                {
                    'id': piece.id_piece,
                    'reference': piece.reference,
                    'nom': piece.nom,
                    'prix_unitaire': float(piece.prix_unitaire) if piece.prix_unitaire else 0.0,
                    'stock_disponible': piece.stock_disponible,
                    'unite': piece.unite or 'pcs'
                }
                for piece in pieces
            ]
        }
        
        return Response({
            'success': True,
            'data': data
        })
        
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=500)


@api_view(['POST'])
def calculate_maintenance_cost(request):
    """Calcule le coût total d'une maintenance en temps réel"""
    try:
        data = request.data
        pieces_utilisees = data.get('pieces', [])
        duree_minutes = data.get('duree_minutes', 0)
        technicien_id = data.get('technicien_id')
        
        cout_total = Decimal('0.00')
        cout_pieces = Decimal('0.00')
        cout_main_oeuvre = Decimal('0.00')
        
        # Calcul coût des pièces
        pieces_detail = []
        for piece_data in pieces_utilisees:
            try:
                piece = Piece.objects.get(id_piece=piece_data['piece_id'])
                quantite = Decimal(str(piece_data['quantite']))
                prix_unitaire = piece.prix_unitaire or Decimal('0.00')
                cout_piece = quantite * prix_unitaire
                cout_pieces += cout_piece
                
                pieces_detail.append({
                    'piece_id': piece.id_piece,
                    'reference': piece.reference,
                    'nom': piece.nom,
                    'quantite': float(quantite),
                    'prix_unitaire': float(prix_unitaire),
                    'cout_total': float(cout_piece)
                })
            except Piece.DoesNotExist:
                continue
        
        # Calcul coût main d'œuvre (taux horaire fictif de 45€/h)
        if duree_minutes > 0 and technicien_id:
            try:
                technicien = Technicien.objects.get(id_technicien=technicien_id)
                taux_horaire = Decimal('45.00')  # Taux fictif
                heures = Decimal(str(duree_minutes)) / Decimal('60')
                cout_main_oeuvre = heures * taux_horaire
            except Technicien.DoesNotExist:
                pass
        
        cout_total = cout_pieces + cout_main_oeuvre
        
        return Response({
            'cout_total': float(cout_total),
            'detail': {
                'pieces': {
                    'cout_total': float(cout_pieces),
                    'items': pieces_detail
                },
                'main_oeuvre': {
                    'cout_total': float(cout_main_oeuvre),
                    'duree_heures': float(duree_minutes / 60) if duree_minutes > 0 else 0,
                    'taux_horaire': 45.00
                }
            }
        })
        
    except Exception as e:
        return Response(
            {'error': f'Erreur lors du calcul des coûts: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['POST'])
def create_maintenance_report(request, ot_id):
    """Crée un nouveau rapport de maintenance"""
    try:
        with transaction.atomic():
            # Récupérer l'OT
            ot = get_object_or_404(OrdreTravail, id_ot=ot_id)
            
            # Créer le rapport de maintenance
            maintenance_data = request.data.get('maintenance', {})
            maintenance_data['id_ot'] = ot_id
            
            serializer = MaintenanceReportSerializer(data=maintenance_data)
            if serializer.is_valid():
                maintenance = serializer.save()
                
                # Ajouter les pièces utilisées
                pieces_data = request.data.get('pieces', [])
                for piece_data in pieces_data:
                    piece = get_object_or_404(Piece, id_piece=piece_data['piece_id'])
                    quantite = Decimal(str(piece_data['quantite']))
                    
                    InterventionPiece.objects.create(
                        maintenance=maintenance,
                        piece=piece,
                        quantite=quantite,
                        lot_numero=piece_data.get('lot_numero', ''),
                        cout_unitaire=piece.prix_unitaire or Decimal('0.00'),
                        cout_total=(piece.prix_unitaire or Decimal('0.00')) * quantite
                    )
                
                # Calculer et mettre à jour le coût total
                cout_response = calculate_maintenance_cost(request)
                if cout_response.status_code == 200:
                    cout_total = Decimal(str(cout_response.data['cout_total']))
                    maintenance.cout_total = cout_total
                    maintenance.save()
                
                # Mettre à jour le statut de l'OT
                ot.statut = 'TERMINE'
                ot.save()
                
                return Response({
                    'success': True,
                    'maintenance_id': maintenance.id_maintenance,
                    'message': 'Rapport de maintenance créé avec succès'
                })
            else:
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
                
    except Exception as e:
        return Response(
            {'error': f'Erreur lors de la création du rapport: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


def handler404(request, exception):
    """
    Gestionnaire d'erreur 404 personnalisé
    """
    return render(request, 'gmao_web/404.html', status=404)


def handler500(request):
    """
    Gestionnaire d'erreur 500 personnalisé
    """
    return render(request, 'gmao_web/500.html', status=500)
