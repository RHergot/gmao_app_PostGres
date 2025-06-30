#!/usr/bin/env python
"""
Script de test pour vérifier les données nécessaires au formulaire de maintenance
"""
import os
import sys
import django

# Configuration Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "gmao_api.settings")
django.setup()

from mobile_api.models import OrdreTravail, Technicien, Piece


def test_data():
    print("=== Test des données pour le formulaire de maintenance ===")

    # Test des OT
    ots = OrdreTravail.objects.all()[:5]
    print(f"\nOrdres de travail disponibles: {ots.count()}")
    for ot in ots:
        print(f"  - OT {ot.id_ot}: {ot.numero_ot} ({ot.statut})")
    # Test des techniciens
    print("\nTest des techniciens...")
    try:
        techniciens_bool = Technicien.objects.filter(actif=True)
        print(f"Techniciens actifs (True): {techniciens_bool.count()}")
    except Exception as e:
        print(f"Erreur avec actif=True: {e}")
        try:
            techniciens_int = Technicien.objects.filter(actif=1)
            print(f"Techniciens actifs (1): {techniciens_int.count()}")
            techniciens = techniciens_int
        except Exception as e2:
            print(f"Erreur avec actif=1: {e2}")
            techniciens = Technicien.objects.all()
            print(f"Tous les techniciens: {techniciens.count()}")

    for tech in techniciens[:3]:
        print(f"  - {tech.nom_complet} (ID: {tech.id_technicien}, actif: {tech.actif})")

    # Test des pièces
    pieces = Piece.objects.filter(statut="ACTIF", stock_actuel__gt=0)
    print(f"\nPièces disponibles (stock > 0): {pieces.count()}")
    for piece in pieces[:3]:
        print(f"  - {piece.reference}: {piece.nom} (Stock: {piece.stock_actuel})")

    # Test d'un OT spécifique
    if ots.exists():
        test_ot = ots.first()
        print(f"\n=== Test OT spécifique: {test_ot.id_ot} ===")
        print(f"Numéro: {test_ot.numero_ot}")
        print(f"Description: {test_ot.description}")
        print(f"Machine: {test_ot.machine.nom if test_ot.machine else 'N/A'}")
        print(
            f"Site: {test_ot.machine.site.nom if test_ot.machine and test_ot.machine.site else 'N/A'}"
        )

        return test_ot.id_ot
    else:
        print("⚠️ Aucun OT trouvé dans la base de données!")
        return None


if __name__ == "__main__":
    test_ot_id = test_data()
    if test_ot_id:
        print(f"\n✅ Test réussi! Vous pouvez tester avec l'OT ID: {test_ot_id}")
    else:
        print("\n❌ Pas de données de test disponibles")
