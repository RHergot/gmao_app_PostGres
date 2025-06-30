"""
Vues pour l'interface web responsive GMAO Mobile
Interface en anglais avec support de traduction
"""
from django.shortcuts import render
from django.http import JsonResponse, HttpRequest
from django.views.generic import TemplateView
from django.utils.translation import gettext as _
from django.contrib.auth.mixins import LoginRequiredMixin
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from django.db import transaction
from decimal import Decimal
from datetime import datetime

from mobile_api.models import (
    OrdreTravail, Technicien, Piece, Machine, Site, 
    Maintenance, InterventionPiece
)
from .serializers import (
    TechnicienSimpleSerializer, PieceSimpleSerializer, 
    MaintenanceReportSerializer, InterventionPieceSerializer
)
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


class MaintenanceListView(TemplateView):
    """Vue pour la liste des rapports de maintenance"""
    template_name = 'gmao_web/maintenance_list.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        try:
            # Récupérer tous les rapports de maintenance avec les infos des OT
            maintenances = Maintenance.objects.select_related(
                'ot', 'technicien', 'machine'
            ).order_by('-date_debut_reelle')
            
            context['maintenances'] = maintenances
            context['page_title'] = _('Maintenance Reports List')
        except Exception as e:
            context['error'] = _('Error loading maintenance reports')
            
        return context


class MaintenanceEditView(TemplateView):
    """Vue pour l'édition d'un rapport de maintenance existant"""
    template_name = 'gmao_web/maintenance_report.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        maintenance_id = kwargs.get('maintenance_id')
        
        try:
            # Récupérer le rapport de maintenance
            maintenance = get_object_or_404(Maintenance, id_maintenance=maintenance_id)
            ot = maintenance.ot
            
            # Contexte de base
            context['ot_id'] = ot.id_ot
            context['maintenance_id'] = maintenance_id
            context['mode'] = 'edit'
            context['work_order'] = {
                'numero_ot': ot.numero_ot,
                'description': ot.description,
                'machine_nom': ot.machine.nom if ot.machine else 'N/A',
                'site_nom': ot.machine.site.nom if ot.machine and ot.machine.site else 'N/A'
            }
            
            # Données du rapport existant pour le pré-remplissage
            def format_datetime_for_input(dt_value):
                """Convertit un datetime en format compatible avec datetime-local input"""
                if dt_value is None:
                    return ""
                try:
                    if hasattr(dt_value, 'isoformat'):
                        # C'est un objet datetime
                        return dt_value.strftime('%Y-%m-%dT%H:%M')
                    else:
                        # C'est probablement une chaîne
                        if isinstance(dt_value, str):
                            # Essayer de parser et reformater
                            try:
                                parsed_dt = datetime.fromisoformat(dt_value.replace('Z', '+00:00'))
                                return parsed_dt.strftime('%Y-%m-%dT%H:%M')
                            except:
                                return str(dt_value)
                        return str(dt_value)
                except Exception as e:
                    print(f"Erreur formatting datetime: {e}")
                    return str(dt_value)
                    
            existing_maintenance = {
                'technicien_id': maintenance.technicien.id_technicien,
                'date_debut_reelle': format_datetime_for_input(maintenance.date_debut_reelle),
                'date_fin_reelle': format_datetime_for_input(maintenance.date_fin_reelle),
                'type_reel': maintenance.type_reel,
                'description_travaux': maintenance.description_travaux,
                'resultat': maintenance.resultat,
                'evaluation_qualite': maintenance.evaluation_qualite,
                'impact_production': maintenance.impact_production,
                'notes_technicien': maintenance.notes_technicien,
                'pieces_utilisees': []  # TODO: ajouter les pièces utilisées si nécessaire
            }
            
            context['existing_maintenance'] = existing_maintenance
            context['page_title'] = _('Edit Maintenance Report') + f' - {ot.numero_ot}'
            
        except Maintenance.DoesNotExist:
            context['error'] = _('Maintenance report not found')
        except Exception as e:
            context['error'] = _('Error loading maintenance report')
            
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
        techniciens = Technicien.objects.filter(actif=True).order_by('nom', 'prenom')
        
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
        # Récupérer l'OT
        ot = get_object_or_404(OrdreTravail, id_ot=ot_id)
        
        # Récupérer les techniciens (tous si problème avec actif)
        try:
            techniciens = Technicien.objects.filter(actif=True).order_by('nom', 'prenom')
            if not techniciens.exists():
                # Fallback: prendre tous les techniciens
                techniciens = Technicien.objects.all().order_by('nom', 'prenom')
        except Exception:
            # Si erreur avec le champ actif, prendre tous les techniciens
            techniciens = Technicien.objects.all().order_by('nom', 'prenom')
        
        # Récupérer les pièces disponibles (toutes si aucune en stock)
        try:
            pieces = Piece.objects.filter(
                statut='actif',  # Correction ici (minuscule)
                stock_actuel__gt=0
            ).order_by('reference')
            if not pieces.exists():
                # Fallback: prendre toutes les pièces actives (même stock 0)
                pieces = Piece.objects.filter(statut='actif').order_by('reference')
        except Exception:
            # Si erreur, prendre toutes les pièces
            pieces = Piece.objects.all().order_by('reference')
        
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
        import traceback
        print("[maintenance_form_data_api] ERREUR:", e)
        print(traceback.format_exc())
        return Response({
            'error': f'Erreur lors du chargement des données: {str(e)}',
            'details': traceback.format_exc()
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


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
                prix_unitaire = Decimal(str(piece.prix_unitaire)) if piece.prix_unitaire is not None else Decimal('0.00')
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
                import traceback
                print("=== TRACEBACK ===")
                traceback.print_exc()
                raise   
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
        import traceback
        print('ERREUR API calculate_maintenance_cost:', e)
        print(traceback.format_exc())
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
            
            # Préparer les données de maintenance
            maintenance_data = request.data.get('maintenance', {})

            # Nettoyage et validation des champs obligatoires
            type_reel = maintenance_data.get('type_reel')
            resultat = maintenance_data.get('resultat')
            
            # Liste des choix valides (doit correspondre à ceux du serializer/model)
            TYPE_CHOICES = ['Préventif', 'Correctif', 'Demande', 'Amélioration']
            RESULTAT_CHOICES = ['Réparé', 'Remplacé', 'Ajusté', 'Nettoyé', 'Lubrifié', 'Inspecté']

            errors = {}
            if not type_reel or type_reel not in TYPE_CHOICES:
                errors['type_reel'] = f"Ce champ est obligatoire et doit être parmi : {TYPE_CHOICES}"
            if not resultat or resultat not in RESULTAT_CHOICES:
                errors['resultat'] = f"Ce champ est obligatoire et doit être parmi : {RESULTAT_CHOICES}"
            if errors:
                return Response({'error': 'Champs obligatoires manquants ou invalides', 'details': errors}, status=status.HTTP_400_BAD_REQUEST)

            # Mapping des champs du formulaire vers le modèle
            model_data = {
                'ot': ot.id_ot,
                'technicien': maintenance_data.get('technicien_id'),
                'date_debut_reelle': maintenance_data.get('date_debut'),
                'date_fin_reelle': maintenance_data.get('date_fin'),
                'type_reel': type_reel,
                'description_travaux': maintenance_data.get('travaux_realises', ''),
                'resultat': resultat,
                'evaluation_qualite': maintenance_data.get('evaluation_qualite') or None,
                'impact_production': maintenance_data.get('impact_production', ''),
                'notes_technicien': maintenance_data.get('notes', ''),
                'machine': ot.machine.id_machine if ot.machine else None
            }
            
            # Créer le rapport de maintenance
            serializer = MaintenanceReportSerializer(data=model_data)
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
                
                # Calculer et mettre à jour le coût total via l'API interne
                cost_request_data = {
                    'pieces': request.data.get('pieces', []),
                    'duree_minutes': 0,  # Sera calculé automatiquement
                    'technicien_id': maintenance_data.get('technicien_id')
                }
                
                # Calculer la durée en minutes
                if model_data['date_debut_reelle'] and model_data['date_fin_reelle']:
                    from datetime import datetime
                    debut = datetime.fromisoformat(model_data['date_debut_reelle'].replace('Z', '+00:00'))
                    fin = datetime.fromisoformat(model_data['date_fin_reelle'].replace('Z', '+00:00'))
                    cost_request_data['duree_minutes'] = (fin - debut).total_seconds() / 60
                
                # Créer une requête fictive pour le calcul des coûts
                cost_request = HttpRequest()
                cost_request.method = 'POST'
                cost_request.data = cost_request_data
                
                cost_response = calculate_maintenance_cost(cost_request)
                if cost_response.status_code == 200:
                    cout_total = Decimal(str(cost_response.data['cout_total']))
                    maintenance.cout_total = cout_total
                    maintenance.save()
                
                # Mettre à jour le statut de l'OT
                ot.statut = 'REALISE'
                ot.save()
                
                return Response({
                    'success': True,
                    'maintenance_id': maintenance.id_maintenance,
                    'message': 'Rapport de maintenance créé avec succès'
                })
            else:
                print('ERREUR API create_maintenance_report serializer:', serializer.errors)
                return Response({
                    'error': 'Données invalides',
                    'details': serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        import traceback
        print('ERREUR API create_maintenance_report:', e)
        print(traceback.format_exc())
        return Response(
            {
                'error': f'Erreur lors de la création du rapport: {str(e)}',
                'traceback': traceback.format_exc()
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['PATCH', 'PUT'])
def update_maintenance_report(request, maintenance_id):
    """Met à jour un rapport de maintenance existant"""
    if request.method not in ['PATCH', 'PUT']:
        return Response({'error': 'Méthode non autorisée'}, status=status.HTTP_405_METHOD_NOT_ALLOWED)
    
    try:
        with transaction.atomic():
            # Récupérer le rapport existant
            maintenance = get_object_or_404(Maintenance, id_maintenance=maintenance_id)
            
            # Préparer les données de maintenance
            maintenance_data = request.data.get('maintenance', {})
            pieces_data = request.data.get('pieces', [])
            
            # Validation des champs obligatoires
            type_reel = maintenance_data.get('type_reel')
            resultat = maintenance_data.get('resultat')
            
            TYPE_CHOICES = ['Préventif', 'Correctif', 'Demande', 'Amélioration']
            RESULTAT_CHOICES = ['Réparé', 'Remplacé', 'Ajusté', 'Nettoyé', 'Lubrifié', 'Inspecté']
            
            if not type_reel or type_reel not in TYPE_CHOICES:
                return Response({
                    'error': 'Type de maintenance invalide',
                    'valid_types': TYPE_CHOICES
                }, status=status.HTTP_400_BAD_REQUEST)
                
            if not resultat or resultat not in RESULTAT_CHOICES:
                return Response({
                    'error': 'Résultat invalide',
                    'valid_results': RESULTAT_CHOICES
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Mettre à jour les champs du rapport
            maintenance.technicien_id = maintenance_data.get('technicien_id', maintenance.technicien_id)
            maintenance.type_reel = type_reel
            maintenance.resultat = resultat
            maintenance.description_travaux = maintenance_data.get('travaux_realises', maintenance.description_travaux)
            maintenance.notes_technicien = maintenance_data.get('notes', maintenance.notes_technicien)
            maintenance.evaluation_qualite = maintenance_data.get('evaluation_qualite', maintenance.evaluation_qualite)
            maintenance.impact_production = maintenance_data.get('impact_production', maintenance.impact_production)
            
            # Traitement des dates
            if 'date_debut' in maintenance_data:
                try:
                    maintenance.date_debut_reelle = datetime.fromisoformat(maintenance_data['date_debut'].replace('Z', '+00:00'))
                except ValueError:
                    maintenance.date_debut_reelle = datetime.strptime(maintenance_data['date_debut'], '%Y-%m-%dT%H:%M')
                    
            if 'date_fin' in maintenance_data:
                try:
                    maintenance.date_fin_reelle = datetime.fromisoformat(maintenance_data['date_fin'].replace('Z', '+00:00'))
                except ValueError:
                    maintenance.date_fin_reelle = datetime.strptime(maintenance_data['date_fin'], '%Y-%m-%dT%H:%M')
            
            # Calcul de la durée
            if maintenance.date_debut_reelle and maintenance.date_fin_reelle:
                duree = maintenance.date_fin_reelle - maintenance.date_debut_reelle
                maintenance.duree_intervention_h = duree.total_seconds() / 3600
            
            # Sauvegarder le rapport
            maintenance.save()
            
            # TODO: Gérer la mise à jour des pièces utilisées si nécessaire
            # Pour l'instant, nous nous concentrons sur la mise à jour des données principales
            
            # Recalculer les coûts
            try:
                from decimal import Decimal
                
                # Coût main d'œuvre
                technicien = maintenance.technicien
                taux_horaire = getattr(technicien, 'taux_horaire', Decimal('25.0'))
                duree = maintenance.duree_intervention_h or 0
                maintenance.cout_main_oeuvre = float(taux_horaire) * duree
                
                # Coût total (pour l'instant juste main d'œuvre)
                maintenance.cout_total = maintenance.cout_main_oeuvre
                maintenance.save()
                
            except Exception as e:
                print(f"Erreur calcul coûts: {e}")
                # Continuer même si le calcul des coûts échoue
            
            # Serializer pour la réponse
            serializer = MaintenanceReportSerializer(maintenance)
            
            return Response({
                'maintenance': serializer.data,
                'message': 'Rapport de maintenance mis à jour avec succès',
                'status': 'success'
            }, status=status.HTTP_200_OK)
            
    except Maintenance.DoesNotExist:
        return Response({
            'error': 'Rapport de maintenance introuvable'
        }, status=status.HTTP_404_NOT_FOUND)
        
    except Exception as e:
        import traceback
        print('ERREUR API update_maintenance_report:', e)
        print(traceback.format_exc())
        return Response(
            {
                'error': f'Erreur lors de la mise à jour du rapport: {str(e)}',
                'traceback': traceback.format_exc()
            },
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
