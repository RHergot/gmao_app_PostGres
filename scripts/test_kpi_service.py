#!/usr/bin/env python3
"""
Script de test pour valider le fonctionnement du KPIService.
Teste les différentes méthodes du service et affiche les résultats.

Usage:
    python scripts/test_kpi_service.py
"""

import sys
import os
import logging
from datetime import datetime, timedelta

# Ajouter la racine du projet au PYTHONPATH
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

# Ajouter aussi le dossier app pour permettre les imports depuis app/
app_path = os.path.join(project_root, 'app')
sys.path.insert(0, app_path)

# Importer APRÈS avoir modifié le path
from app.core.services.kpi_service import KPIService
from app.utils.logging_config import setup_logging

# Configurer le logging
setup_logging()
logger = logging.getLogger(__name__)

def test_kpi_machine():
    """Test des KPI par machine."""
    print("\n" + "="*50)
    print("📊 TEST KPI PAR MACHINE")
    print("="*50)
    
    try:
        kpi_service = KPIService()
        
        # Définir une période de test (6 derniers mois)
        periode_fin = datetime.now().date()
        periode_debut = periode_fin - timedelta(days=180)
        
        # Test 1: Coûts par machine
        print(f"\n1. Coûts par machine ({periode_debut} à {periode_fin}):")
        couts_machines = kpi_service.get_couts_par_machine(
            periode_debut=periode_debut,
            periode_fin=periode_fin,
            limite=5
        )
        
        if couts_machines:
            for machine in couts_machines[:5]:  # Afficher les 5 premières
                print(f"  Machine {machine.get('machine_nom', 'N/A')}: {machine.get('cout_total', 0):.2f}€ "
                      f"({machine.get('nb_interventions', 0)} interventions)")
        else:
            print("  Aucune donnée trouvée")
        
        # Test 2: Top machines coûteuses
        print("\n2. Top 5 des machines les plus coûteuses:")
        top_machines = kpi_service.get_top_machines_couteuses(limite=5)
        
        if top_machines:
            for i, machine in enumerate(top_machines, 1):
                print(f"  {i}. {machine.get('machine_nom', 'N/A')}: {machine.get('cout_total_12m', 0):.2f}€")
        else:
            print("  Aucune donnée trouvée")
        
        # Test 3: Tendances machine
        print("\n3. Tendances d'une machine (si données disponibles):")
        if couts_machines:
            machine_id = couts_machines[0].get('id_machine')
            if machine_id:
                tendances = kpi_service.get_tendances_machine(
                    machine_id=machine_id,
                    nb_periodes=6
                )
                
                if tendances:
                    print(f"  Machine ID {machine_id}:")
                    for periode in tendances[-3:]:  # 3 dernières périodes
                        print(f"    {periode.get('periode_mois', 'N/A')}: {periode.get('cout_total_periode', 0):.2f}€")
                else:
                    print("  Aucune tendance trouvée")
            else:
                print("  ID machine non disponible")
        
        print("✅ Tests KPI machine terminés")
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors des tests KPI machine: {e}")
        logger.error(f"Erreur test KPI machine: {e}")
        return False

def test_kpi_site_equipe():
    """Test des KPI par site et équipe."""
    print("\n" + "="*50)
    print("🏢 TEST KPI PAR SITE ET ÉQUIPE")
    print("="*50)
    
    try:
        kpi_service = KPIService()
        
        # Définir une période de test (6 derniers mois)
        periode_fin = datetime.now().date()
        periode_debut = periode_fin - timedelta(days=180)
        
        # Test 1: Coûts par site
        print(f"\n1. Coûts par site ({periode_debut} à {periode_fin}):")
        couts_sites = kpi_service.get_couts_par_site(
            periode_debut=periode_debut,
            periode_fin=periode_fin
        )
        
        if couts_sites:
            for site in couts_sites:
                print(f"  Site {site.get('site_nom', 'N/A')}: {site.get('cout_total', 0):.2f}€ "
                      f"({site.get('nb_interventions', 0)} interventions)")
        else:
            print("  Aucune donnée trouvée")
        
        # Test 2: Coûts par équipe
        print(f"\n2. Coûts par équipe ({periode_debut} à {periode_fin}):")
        couts_equipes = kpi_service.get_couts_par_equipe(
            periode_debut=periode_debut,
            periode_fin=periode_fin
        )
        
        if couts_equipes:
            for equipe in couts_equipes:
                print(f"  Équipe {equipe.get('equipe_nom', 'N/A')}: {equipe.get('cout_total', 0):.2f}€ "
                      f"({equipe.get('nb_interventions', 0)} interventions)")
        else:
            print("  Aucune donnée trouvée")
        
        print("✅ Tests KPI site/équipe terminés")
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors des tests KPI site/équipe: {e}")
        logger.error(f"Erreur test KPI site/équipe: {e}")
        return False

def test_kpi_types():
    """Test des KPI par types (machine et intervention)."""
    print("\n" + "="*50)
    print("🔧 TEST KPI PAR TYPES")
    print("="*50)
    
    try:
        kpi_service = KPIService()
        
        # Définir une période de test (6 derniers mois)
        periode_fin = datetime.now().date()
        periode_debut = periode_fin - timedelta(days=180)
        
        # Test 1: Ratio préventif/curatif
        print(f"\n1. Ratio préventif/curatif ({periode_debut} à {periode_fin}):")
        ratio = kpi_service.get_ratio_preventif_curatif(
            periode_debut=periode_debut,
            periode_fin=periode_fin
        )
        
        if ratio:
            print(f"  Préventif: {ratio.get('cout_preventif', 0):.2f}€ "
                  f"({ratio.get('nb_preventif', 0)} interventions)")
            print(f"  Curatif: {ratio.get('cout_curatif', 0):.2f}€ "
                  f"({ratio.get('nb_curatif', 0)} interventions)")
            cout_total = ratio.get('cout_total', 0)
            if cout_total > 0:
                pct_preventif = (ratio.get('cout_preventif', 0) / cout_total) * 100
                print(f"  Ratio préventif: {pct_preventif:.1f}%")
        else:
            print("  Aucune donnée trouvée")
        
        print("✅ Tests KPI types terminés")
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors des tests KPI types: {e}")
        logger.error(f"Erreur test KPI types: {e}")
        return False

def test_kpi_resume():
    """Test du résumé global des KPI."""
    print("\n" + "="*50)
    print("📈 TEST RÉSUMÉ GLOBAL KPI")
    print("="*50)
    
    try:
        kpi_service = KPIService()
        
        # Définir une période de test (6 derniers mois)
        periode_fin = datetime.now().date()
        periode_debut = periode_fin - timedelta(days=180)
        
        print(f"\nRésumé global ({periode_debut} à {periode_fin}):")
        resume = kpi_service.get_resume_global(
            periode_debut=periode_debut,
            periode_fin=periode_fin
        )
        
        if resume:
            print(f"  Coût total: {resume.get('cout_total', 0):.2f}€")
            print(f"  Nombre d'interventions: {resume.get('nb_interventions', 0)}")
            print(f"  Coût moyen par intervention: {resume.get('cout_moyen_intervention', 0):.2f}€")
            print(f"  Nombre de machines concernées: {resume.get('nb_machines', 0)}")
            nb_machines = resume.get('nb_machines', 0)
            if nb_machines > 0:
                cout_moyen_machine = resume.get('cout_total', 0) / nb_machines
                print(f"  Coût moyen par machine: {cout_moyen_machine:.2f}€")
        else:
            print("  Aucune donnée trouvée")
        
        print("✅ Test résumé global terminé")
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors du test résumé global: {e}")
        logger.error(f"Erreur test résumé global: {e}")
        return False

def test_database_views():
    """Test de l'existence des vues dans la base de données."""
    print("\n" + "="*50)
    print("🗄️  TEST VUES BASE DE DONNÉES")
    print("="*50)
    
    try:
        from app.data.database import get_connection, close_connection
        
        conn = get_connection()
        cursor = conn.cursor()
        
        # Vérifier l'existence des vues principales
        views_to_check = [
            'v_maintenance_couts_detaille',
            'v_kpi_machine_mensuel',
            'v_kpi_site_mensuel', 
            'v_kpi_equipe_mensuel',
            'v_kpi_type_machine_mensuel',
            'v_kpi_preventif_curatif',
            'v_top_machines_couteuses'
        ]
        
        print("\nVérification des vues:")
        for view_name in views_to_check:
            cursor.execute("""
                SELECT EXISTS (
                    SELECT 1 
                    FROM information_schema.views 
                    WHERE table_name = %s
                )
            """, (view_name,))
            
            result = cursor.fetchone()
            exists = result[0] if isinstance(result, tuple) else result['exists']
            status = "✅" if exists else "❌"
            print(f"  {status} {view_name}")
        
        close_connection()
        print("✅ Test des vues terminé")
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors du test des vues: {e}")
        logger.error(f"Erreur test vues: {e}")
        return False

def main():
    """Fonction principale du script de test."""
    print("🧪 DÉMARRAGE DES TESTS DU KPI SERVICE")
    print("=" * 60)
    
    # Résultats des tests
    results = {
        'database_views': False,
        'kpi_machine': False,
        'kpi_site_equipe': False,
        'kpi_types': False,
        'kpi_resume': False
    }
    
    try:
        # Test 1: Vérifier les vues de base de données
        results['database_views'] = test_database_views()
        
        # Si les vues existent, tester le service
        if results['database_views']:
            results['kpi_machine'] = test_kpi_machine()
            results['kpi_site_equipe'] = test_kpi_site_equipe()
            results['kpi_types'] = test_kpi_types()
            results['kpi_resume'] = test_kpi_resume()
        else:
            print("\n⚠️  Les vues KPI n'existent pas. Exécutez d'abord:")
            print("   python scripts/init_kpi_views.py")
        
        # Afficher le résumé final
        print("\n" + "="*60)
        print("📋 RÉSUMÉ DES TESTS")
        print("="*60)
        
        for test_name, success in results.items():
            status = "✅ SUCCÈS" if success else "❌ ÉCHEC"
            print(f"  {test_name.replace('_', ' ').title()}: {status}")
        
        # Calculer le score global
        total_tests = len(results)
        successful_tests = sum(results.values())
        score = (successful_tests / total_tests) * 100
        
        print(f"\n🎯 Score global: {successful_tests}/{total_tests} ({score:.1f}%)")
        
        if score == 100:
            print("🎉 Tous les tests sont passés avec succès!")
            return 0
        elif score >= 50:
            print("⚠️  Certains tests ont échoué, mais le système fonctionne partiellement")
            return 1
        else:
            print("❌ La majorité des tests ont échoué")
            return 2
            
    except KeyboardInterrupt:
        print("\n⏹️  Tests interrompus par l'utilisateur")
        return 1
    except Exception as e:
        print(f"\n💥 Erreur fatale lors des tests: {e}")
        logger.critical(f"Erreur fatale tests: {e}")
        return 2

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
