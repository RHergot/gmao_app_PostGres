#!/usr/bin/env python
"""
Script pour vérifier les statuts des ordres de travail
"""
import os
import django

# Configuration Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "gmao_api.settings")
django.setup()

from mobile_api.models import OrdreTravail


def check_work_order_statuses():
    """Vérifier les statuts des ordres de travail"""
    print("=== VÉRIFICATION DES STATUTS D'ORDRES DE TRAVAIL ===")

    # Compter tous les OT
    total_ot = OrdreTravail.objects.count()
    print(f"Total d'ordres de travail: {total_ot}")

    # Afficher les statuts uniques
    statuts = OrdreTravail.objects.values_list("statut", flat=True).distinct()
    print(f"\nStatuts disponibles: {list(statuts)}")

    # Compter par statut
    print("\nRépartition par statut:")
    for statut in statuts:
        count = OrdreTravail.objects.filter(statut=statut).count()
        print(f"  - {statut}: {count} OT")

    # Afficher quelques exemples d'OT
    print(f"\nExemples d'ordres de travail (premiers 10):")
    for ot in OrdreTravail.objects.all()[:10]:
        print(
            f"  - OT {ot.numero_ot}: {ot.statut} | {ot.description[:50] if ot.description else 'Pas de description'}..."
        )

    # Vérifier spécifiquement les OT "EnCours"
    encours_count = OrdreTravail.objects.filter(statut="EnCours").count()
    print(f"\nOrdres de travail 'EnCours': {encours_count}")

    if encours_count > 0:
        print("Détails des OT 'EnCours':")
        for ot in OrdreTravail.objects.filter(statut="EnCours")[:5]:
            machine_nom = ot.machine.nom if ot.machine else "Machine inconnue"
            site_nom = (
                ot.machine.site.nom
                if ot.machine and ot.machine.site
                else "Site inconnu"
            )
            print(
                f"  - {ot.numero_ot}: {machine_nom} @ {site_nom} | Priorité: {ot.priorite}"
            )


if __name__ == "__main__":
    check_work_order_statuses()
