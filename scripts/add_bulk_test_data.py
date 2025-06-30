#!/usr/bin/env python3
"""
Script pour ajouter plus de machines et de données de test
Avec des criticités standardisées et plus d'interventions
"""

import psycopg2
import psycopg2.extras
import random
import os
from datetime import datetime, date, timedelta
from dotenv import load_dotenv

load_dotenv()

def get_db_connection():
    return psycopg2.connect(
        dbname=os.getenv('POSTGRES_DB', 'gmao_db'),
        user=os.getenv('POSTGRES_USER', 'postgres'),
        password=os.getenv('POSTGRES_PASSWORD', 'postgres'),
        host=os.getenv('POSTGRES_HOST', 'localhost'),
        port=os.getenv('POSTGRES_PORT', '5432'),
        cursor_factory=psycopg2.extras.RealDictCursor
    )

def add_more_machines_and_data():
    """Ajoute plus de machines et données pour les tests"""
    print("🚀 Ajout de machines et données supplémentaires pour les tests KPI...")
    
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                
                # Récupérer les données existantes
                cur.execute("SELECT id_site, nom FROM SITE LIMIT 1")
                site = cur.fetchone()
                
                cur.execute("SELECT id_fabricant FROM FABRICANT LIMIT 1")
                fabricant = cur.fetchone()
                
                cur.execute("SELECT id_type_machine, nom FROM TYPE_MACHINE")
                types_machines = cur.fetchall()
                
                cur.execute("SELECT id_technicien FROM TECHNICIEN")
                techniciens = cur.fetchall()
                
                cur.execute("SELECT id_utilisateur FROM UTILISATEUR WHERE role = 'Admin' LIMIT 1")
                admin_user = cur.fetchone()
                
                if not all([site, fabricant, types_machines, techniciens, admin_user]):
                    print("❌ Données de base insuffisantes")
                    return
                
                # Ajouter 10 nouvelles machines avec criticités standardisées
                criticites = ["Normal", "Important", "Critique"]
                machine_counter = 100  # Commencer à 100 pour éviter les conflits
                nouvelles_machines = []
                
                print("🤖 Création de machines supplémentaires...")
                for i in range(10):
                    type_machine = random.choice(types_machines)
                    criticite = random.choice(criticites)
                    
                    nom = f"MACHINE-TEST-{machine_counter:03d}"
                    serial = f"SNTEST{machine_counter:06d}"
                    
                    installation = date.today() - timedelta(days=random.randint(365, 1825))
                    garantie_fin = installation + timedelta(days=random.randint(365, 1095))
                    
                    cur.execute("""
                        INSERT INTO MACHINE (
                            nom, serial, modele, date_installation, localisation, etat,
                            informations_techniques, type_machine_id, site_id, fabricant_id,
                            criticite, garantie_fin
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        RETURNING id_machine
                    """, [
                        nom, serial, f"Modèle-TEST-{i+1}", 
                        installation.isoformat(), f"Zone TEST {i+1}", "En Service",
                        f"Machine de test {nom}", type_machine['id_type_machine'], 
                        site['id_site'], fabricant['id_fabricant'], criticite, garantie_fin.isoformat()
                    ])
                    
                    result = cur.fetchone()
                    nouvelles_machines.append({
                        'id': result['id_machine'],
                        'nom': nom,
                        'criticite': criticite,
                        'type_nom': type_machine['nom']
                    })
                    
                    machine_counter += 1
                    print(f"  ✓ Machine créée: {nom} - Criticité: {criticite}")
                
                # Créer des interventions pour les nouvelles machines
                print("\n🔧 Génération d'interventions pour les nouvelles machines...")
                
                types_maintenance = ["Preventif", "Correctif", "Urgence"]
                couts_standard = {
                    "Preventif": {"mod": 400, "pieces_int": 250, "pieces_ext": 0, "autres": 0},        # 650 € total
                    "Correctif": {"mod": 800, "pieces_int": 450, "pieces_ext": 0, "autres": 0},        # 1250 € total  
                    "Urgence": {"mod": 1200, "pieces_int": 700, "pieces_ext": 100, "autres": 350}      # 2350 € total
                }
                
                ot_counter = 2000  # Commencer à 2000
                total_interventions = 0
                
                # Période : 12 derniers mois
                date_fin = date.today()
                date_debut = date_fin - timedelta(days=365)
                
                for machine in nouvelles_machines:
                    # Plus d'interventions selon la criticité
                    nb_interventions = {
                        "Normal": random.randint(6, 10),
                        "Important": random.randint(8, 14), 
                        "Critique": random.randint(12, 20)
                    }[machine['criticite']]
                    
                    for i in range(nb_interventions):
                        # Type d'intervention selon la criticité
                        if machine['criticite'] == "Critique":
                            type_choisi = random.choices(types_maintenance, weights=[25, 50, 25])[0]
                        elif machine['criticite'] == "Important":
                            type_choisi = random.choices(types_maintenance, weights=[45, 45, 10])[0]
                        else:
                            type_choisi = random.choices(types_maintenance, weights=[65, 30, 5])[0]
                        
                        # Dates réparties sur l'année
                        days_offset = random.randint(0, 365)
                        date_intervention = date_debut + timedelta(days=days_offset)
                        date_creation = date_intervention - timedelta(days=random.randint(1, 20))
                        
                        technicien = random.choice(techniciens)
                        
                        # Créer l'ordre de travail
                        numero_ot = f"OT-BULK-{ot_counter}"
                        description_ot = f"Maintenance {type_choisi.lower()} - {machine['nom']}"
                        
                        try:
                            cur.execute("""
                                INSERT INTO ORDRE_TRAVAIL (
                                    numero_ot, machine_id, type, description, date_creation,
                                    date_prevue, duree_prevue_min, priorite, urgence, statut,
                                    technicien_assigne_id, utilisateur_createur_id
                                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                                RETURNING id_ot
                            """, [
                                numero_ot, machine['id'], type_choisi, description_ot,
                                date_creation.isoformat(), date_intervention.isoformat(),
                                random.randint(120, 600), "Normale", 
                                1 if type_choisi == "Urgence" else 0, "Terminé",
                                technicien['id_technicien'], admin_user['id_utilisateur']
                            ])
                            
                            ot_result = cur.fetchone()
                            ot_id = ot_result['id_ot']
                            
                            # Coûts avec variation
                            couts = couts_standard[type_choisi]
                            variation = random.uniform(0.8, 1.2)  # ±20% de variation
                            
                            cout_mod = round(couts["mod"] * variation, 2)
                            cout_pieces_int = round(couts["pieces_int"] * variation, 2)
                            cout_pieces_ext = round(couts["pieces_ext"] * variation, 2)
                            cout_autres = round(couts["autres"] * variation, 2)
                            cout_total = cout_mod + cout_pieces_int + cout_pieces_ext + cout_autres
                            
                            # Durée selon type et criticité
                            durees_base = {"Preventif": 5.0, "Correctif": 9.0, "Urgence": 7.0}
                            duree = durees_base[type_choisi] * random.uniform(0.7, 1.3)
                            if machine['criticite'] == "Critique":
                                duree *= 1.2  # Machines critiques prennent plus de temps
                            duree = round(duree, 1)
                            
                            # Date de fin
                            date_fin_reelle = date_intervention + timedelta(hours=int(duree))
                            
                            # Créer l'intervention de maintenance
                            cur.execute("""
                                INSERT INTO MAINTENANCE (
                                    ot_id, machine_id, technicien_id, date_debut_reelle, date_fin_reelle,
                                    duree_intervention_h, type_reel, description_travaux, resultat,
                                    cout_main_oeuvre, cout_pieces_internes, cout_pieces_externes,
                                    cout_autres_frais, cout_total, evaluation_qualite, impact_production
                                ) VALUES (
                                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                                ) RETURNING id_maintenance
                            """, [
                                ot_id, machine['id'], technicien['id_technicien'], 
                                date_intervention.isoformat(), date_fin_reelle.isoformat(),
                                duree, type_choisi, 
                                f"Maintenance {type_choisi.lower()} sur {machine['nom']}", 
                                f"Intervention {type_choisi.lower()} réalisée avec succès",
                                cout_mod, cout_pieces_int, cout_pieces_ext, cout_autres, cout_total, 
                                random.randint(3, 5), f"Impact {type_choisi.lower()}"
                            ])
                            
                            ot_counter += 1
                            total_interventions += 1
                            
                        except Exception as e:
                            print(f"  ⚠️ Erreur création maintenance: {e}")
                            continue
                
                conn.commit()
                
                print(f"\n✅ Ajout terminé avec succès!")
                print(f"📊 Nouvelles machines créées: {len(nouvelles_machines)}")
                print(f"🔧 Nouvelles interventions: {total_interventions}")
                
                # Résumé par criticité
                print(f"\n📈 Répartition des nouvelles machines:")
                criticites_count = {}
                for machine in nouvelles_machines:
                    crit = machine['criticite']
                    criticites_count[crit] = criticites_count.get(crit, 0) + 1
                
                for crit, count in criticites_count.items():
                    print(f"  • {crit}: {count} machines")
                
                print(f"\n💰 NOUVEAUX COÛTS STANDARDISÉS:")
                print(f"  • Préventif: ~650€ (MOD: 400€, Pièces internes: 250€)")
                print(f"  • Correctif: ~1250€ (MOD: 800€, Pièces internes: 450€)")
                print(f"  • Urgence: ~2350€ (MOD: 1200€, Pièces: 700€+100€, Autres: 350€)")
                print(f"  • Variation: ±20% sur les coûts de base")
                
                print(f"\n🎯 Vous avez maintenant un panel de données substantiel pour tester les KPI!")
                
    except Exception as e:
        print(f"❌ Erreur: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    add_more_machines_and_data()
