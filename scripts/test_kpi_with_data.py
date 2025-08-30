#!/usr/bin/env python3
"""
Test rapide du KPI Service avec les nouvelles données
"""

import sys
import os
from datetime import datetime, date, timedelta

# Ajouter le chemin du projet
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

try:
    from app.core.services.kpi_service import KPIService
    
    def test_kpi_service():
        """Test rapide des KPI avec les nouvelles données"""
        print("🧪 Test du KPI Service avec les nouvelles données...")
        
        kpi_service = KPIService()
        
        # Période de test : 12 derniers mois
        date_fin = date.today()
        date_debut = date_fin - timedelta(days=365)
        
        print(f"📅 Période d'analyse: {date_debut} à {date_fin}")
        
        try:
            # Test KPI machines
            print("\n🤖 Test KPI par machine...")
            machines = kpi_service.get_couts_par_machine(date_debut, date_fin, limite=5)
            print(f"  ✓ {len(machines)} machines récupérées")
            if machines:
                top_machine = machines[0]
                print(f"  💰 Machine la plus coûteuse: {top_machine.get('machine_nom', 'N/A')} - {top_machine.get('cout_total', 0):.2f}€")
            
            # Test KPI sites
            print("\n📍 Test KPI par site...")
            sites = kpi_service.get_couts_par_site(date_debut, date_fin)
            print(f"  ✓ {len(sites)} sites récupérés")
            if sites:
                top_site = sites[0]
                print(f"  💰 Site le plus coûteux: {top_site.get('site_nom', 'N/A')} - {top_site.get('cout_total', 0):.2f}€")
            
            # Test KPI équipes
            print("\n👥 Test KPI par équipe...")
            equipes = kpi_service.get_couts_par_equipe(date_debut, date_fin)
            print(f"  ✓ {len(equipes)} équipes récupérées")
            if equipes:
                top_equipe = equipes[0]
                print(f"  💰 Équipe la plus coûteuse: {top_equipe.get('equipe_nom', 'N/A')} - {top_equipe.get('cout_total', 0):.2f}€")
            
            # Test préventif vs curatif
            print("\n🔧 Test analyse préventif vs curatif...")
            preventif_curatif = kpi_service.get_preventif_vs_curatif(date_debut, date_fin)
            total_interventions = preventif_curatif.get('total', {}).get('nb_interventions', 0)
            total_cout = preventif_curatif.get('total', {}).get('cout_total', 0)
            print(f"  ✓ Total interventions: {total_interventions}")
            print(f"  ✓ Coût total: {total_cout:.2f}€")
            
            if 'ratios' in preventif_curatif:
                ratios = preventif_curatif['ratios']
                print(f"  📊 Préventif: {ratios.get('nb_preventif_pct', 0):.1f}% des interventions, {ratios.get('cout_preventif_pct', 0):.1f}% des coûts")
                print(f"  📊 Curatif: {ratios.get('nb_curatif_pct', 0):.1f}% des interventions, {ratios.get('cout_curatif_pct', 0):.1f}% des coûts")
            
            # Test résumé global
            print("\n📊 Test résumé global...")
            summary = kpi_service.get_kpi_summary_global(date_debut, date_fin)
            if 'totaux' in summary:
                totaux = summary['totaux']
                print(f"  ✓ Machines analysées: {totaux.get('nb_machines', 0)}")
                print(f"  ✓ Sites analysés: {totaux.get('nb_sites', 0)}")
                print(f"  ✓ Équipes analysées: {totaux.get('nb_equipes', 0)}")
                print(f"  ✓ Total interventions: {totaux.get('nb_interventions', 0)}")
                print(f"  ✓ Coût total: {totaux.get('cout_total', 0):.2f}€")
                print(f"  ✓ Coût moyen/intervention: {totaux.get('cout_moyen_intervention', 0):.2f}€")
            
            print("\n✅ Tests KPI Service réussis!")
            print("🎯 Les données sont prêtes pour les dashboards!")
            
        except Exception as e:
            print(f"❌ Erreur dans les tests KPI: {e}")
            import traceback
            traceback.print_exc()
    
    if __name__ == "__main__":
        test_kpi_service()
        
except ImportError as e:
    print(f"❌ Erreur d'import: {e}")
    print("Vérifiez que le module KPIService est accessible")
