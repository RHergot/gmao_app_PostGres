#!/usr/bin/env python3
"""
Script simplifié de génération de données de test pour la GMAO
Génère des données cohérentes et facilement contrôlables pour tester les KPI
"""

import psycopg2
import psycopg2.extras
import random
import os
from datetime import datetime, date, timedelta
from decimal import Decimal
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()

def get_db_connection():
    """Connexion directe à la base de données"""
    return psycopg2.connect(
        dbname=os.getenv('POSTGRES_DB', 'gmao_db'),
        user=os.getenv('POSTGRES_USER', 'postgres'),
        password=os.getenv('POSTGRES_PASSWORD', ''),
        host=os.getenv('POSTGRES_HOST', 'localhost'),
        port=os.getenv('POSTGRES_PORT', '5432'),
        cursor_factory=psycopg2.extras.RealDictCursor
    )

class SimpleTestDataGenerator:
    """Générateur simplifié de données de test pour la GMAO"""
    
    def __init__(self):
        self.sites = []
        self.types_machines = []
        self.machines = []
        self.equipes = []
        self.techniciens = []
        self.maintenances_created = 0
        
    def generate_all_test_data(self):
        """Génère un jeu complet de données de test"""
        print("🚀 Génération des données de test GMAO (version simplifiée)...")
        
        try:
            with get_db_connection() as conn:
                self.conn = conn
                
                # Nettoyer les données existantes (optionnel)
                self.clean_test_data()
                
                # Créer les données de base
                self.create_sites()
                self.create_types_machines()
                self.create_machines()
                self.create_equipes()
                self.create_techniciens()
                self.create_maintenances()
                
                conn.commit()
                
            print("✅ Génération terminée avec succès!")
            self.print_summary()
            
        except Exception as e:
            print(f"❌ Erreur lors de la génération: {e}")
            raise
    
    def clean_test_data(self):
        """Nettoie les données de test existantes"""
        print("🧹 Nettoyage des données existantes...")
        
        with self.conn.cursor() as cur:
            # Ordre important à cause des contraintes de clés étrangères
            tables_to_clean = [
                'MAINTENANCE_PIECES',
                'MAINTENANCE_DETAIL', 
                'MAINTENANCE',
                'MACHINE',
                'TYPE_MACHINE',
                'EQUIPE',
                'SITE'
            ]
            
            for table in tables_to_clean:
                try:
                    cur.execute(f"DELETE FROM {table} WHERE 1=1")
                    rows_deleted = cur.rowcount
                    print(f"  ✓ Table {table}: {rows_deleted} lignes supprimées")
                except Exception as e:
                    print(f"  ⚠️ Erreur nettoyage {table}: {e}")
    
    def create_sites(self):
        """Crée les sites de test"""
        sites_data = [
            ("Site Production Nord", "Lille", "France"),
            ("Site Production Sud", "Marseille", "France"),
            ("Site Logistique Est", "Strasbourg", "France"),
            ("Site R&D Central", "Lyon", "France"),
            ("Site Maintenance", "Toulouse", "France")
        ]
        
        print("📍 Création des sites...")
        with self.conn.cursor() as cur:
            for nom, ville, pays in sites_data:
                cur.execute("""
                    INSERT INTO SITE (nom, ville, pays, adresse, code_postal, actif)
                    VALUES (%s, %s, %s, %s, %s, true)
                    RETURNING id_site
                """, [nom, ville, pays, f"Zone industrielle {ville}", "00000"])
                
                result = cur.fetchone()
                self.sites.append({
                    'id': result['id_site'],
                    'nom': nom,
                    'ville': ville
                })
                print(f"  ✓ Site créé: {nom} (ID: {result['id_site']})")
    
    def create_types_machines(self):
        """Crée les types de machines"""
        types_data = [
            ("Presse hydraulique", "Production"),
            ("Tour CNC", "Production"), 
            ("Convoyeur", "Logistique"),
            ("Compresseur", "Utilités"),
            ("Robot soudage", "Production")
        ]
        
        print("🏭 Création des types de machines...")
        with self.conn.cursor() as cur:
            for nom, categorie in types_data:
                cur.execute("""
                    INSERT INTO TYPE_MACHINE (nom, categorie, description)
                    VALUES (%s, %s, %s)
                    RETURNING id_type_machine
                """, [nom, categorie, f"Type de machine: {nom}"])
                
                result = cur.fetchone()
                self.types_machines.append({
                    'id': result['id_type_machine'],
                    'nom': nom,
                    'categorie': categorie
                })
                print(f"  ✓ Type créé: {nom} (ID: {result['id_type_machine']})")
    
    def create_machines(self):
        """Crée les machines de test"""
        print("🤖 Création des machines...")
        
        criticites = ["Normal", "Important", "Critique"]
        machine_counter = 1
        
        with self.conn.cursor() as cur:
            for site in self.sites:
                for type_machine in self.types_machines:
                    # 2-3 machines par type par site
                    nb_machines = random.randint(2, 3)
                    
                    for i in range(nb_machines):
                        nom = f"{type_machine['nom']}-{site['ville']}-{machine_counter:03d}"
                        serial = f"SN{machine_counter:06d}"
                        criticite = random.choice(criticites)
                        mise_en_service = date.today() - timedelta(days=random.randint(365, 3650))
                        
                        cur.execute("""
                            INSERT INTO MACHINE (nom, numero_serie, id_site, id_type_machine, 
                                               date_mise_en_service, criticite, actif)
                            VALUES (%s, %s, %s, %s, %s, %s, true)
                            RETURNING id_machine
                        """, [nom, serial, site['id'], type_machine['id'], mise_en_service, criticite])
                        
                        result = cur.fetchone()
                        self.machines.append({
                            'id': result['id_machine'],
                            'nom': nom,
                            'serial': serial,
                            'site_id': site['id'],
                            'site_nom': site['nom'],
                            'type_id': type_machine['id'],
                            'type_nom': type_machine['nom'],
                            'criticite': criticite
                        })
                        
                        machine_counter += 1
                        print(f"  ✓ Machine créée: {nom} (ID: {result['id_machine']})")
    
    def create_equipes(self):
        """Crée les équipes de maintenance"""
        equipes_data = [
            ("Équipe Mécanique Nord", "Mécanique"),
            ("Équipe Électrique Nord", "Électricité"),
            ("Équipe Mécanique Sud", "Mécanique"),
            ("Équipe Polyvalente Est", "Polyvalente"),
            ("Équipe Spécialisée R&D", "Spécialisée")
        ]
        
        print("👥 Création des équipes...")
        with self.conn.cursor() as cur:
            for nom, domaine in equipes_data:
                cur.execute("""
                    INSERT INTO EQUIPE (nom, domaine, description, actif)
                    VALUES (%s, %s, %s, true)
                    RETURNING id_equipe
                """, [nom, domaine, f"Équipe de maintenance: {domaine}"])
                
                result = cur.fetchone()
                self.equipes.append({
                    'id': result['id_equipe'],
                    'nom': nom,
                    'domaine': domaine
                })
                print(f"  ✓ Équipe créée: {nom} (ID: {result['id_equipe']})")
    
    def create_techniciens(self):
        """Crée des techniciens de test"""
        print("👨‍🔧 Création des techniciens...")
        
        prenoms = ["Pierre", "Marie", "Jean", "Sophie", "Michel", "David", "Catherine", "Philippe"]
        noms = ["Martin", "Dubois", "Moreau", "Lambert", "Rousseau", "Garcia", "Roux", "Fournier"]
        
        with self.conn.cursor() as cur:
            tech_counter = 1
            for equipe in self.equipes:
                # 2-4 techniciens par équipe
                nb_techs = random.randint(2, 4)
                
                for i in range(nb_techs):
                    prenom = random.choice(prenoms)
                    nom = random.choice(noms)
                    nom_complet = f"{prenom} {nom}"
                    
                    cur.execute("""
                        INSERT INTO TECHNICIEN (nom, prenom, id_equipe, actif)
                        VALUES (%s, %s, %s, true)
                        RETURNING id_technicien
                    """, [nom, prenom, equipe['id']])
                    
                    result = cur.fetchone()
                    self.techniciens.append({
                        'id': result['id_technicien'],
                        'nom_complet': nom_complet,
                        'equipe_id': equipe['id'],
                        'equipe_nom': equipe['nom']
                    })
                    
                    tech_counter += 1
                    print(f"  ✓ Technicien créé: {nom_complet} (ID: {result['id_technicien']})")
    
    def create_maintenances(self):
        """Crée des interventions de maintenance avec des valeurs facilement contrôlables"""
        print("🔧 Génération des interventions de maintenance...")
        
        # Période de génération : 12 derniers mois
        date_fin = date.today()
        date_debut = date_fin - timedelta(days=365)
        
        types_maintenance = ["Preventif", "Correctif", "Urgence"]
        
        # Coûts standardisés pour faciliter les tests
        couts_standard = {
            "Preventif": {"mod": 280, "pieces": 150, "externes": 0},      # 430 € total
            "Correctif": {"mod": 560, "pieces": 300, "externes": 0},      # 860 € total  
            "Urgence": {"mod": 840, "pieces": 500, "externes": 200}       # 1540 € total
        }
        
        maintenances_count = 0
        
        with self.conn.cursor() as cur:
            # Générer des maintenances pour chaque machine
            for machine in self.machines:
                
                # Nombre d'interventions selon la criticité
                nb_interventions = {
                    "Normal": random.randint(3, 6),
                    "Important": random.randint(5, 8), 
                    "Critique": random.randint(7, 12)
                }[machine['criticite']]
                
                for i in range(nb_interventions):
                    # Type d'intervention selon la criticité
                    if machine['criticite'] == "Critique":
                        type_choisi = random.choices(
                            types_maintenance, 
                            weights=[30, 50, 20]  # Plus d'urgences pour les machines critiques
                        )[0]
                    elif machine['criticite'] == "Important":
                        type_choisi = random.choices(
                            types_maintenance,
                            weights=[50, 40, 10]
                        )[0]
                    else:
                        type_choisi = random.choices(
                            types_maintenance,
                            weights=[60, 35, 5]   # Principalement préventif pour les machines normales
                        )[0]
                    
                    # Date d'intervention
                    days_offset = random.randint(0, 365)
                    date_intervention = date_debut + timedelta(days=days_offset)
                    
                    # Utiliser les coûts standardisés
                    couts = couts_standard[type_choisi]
                    
                    # Petite variation aléatoire (±10%)
                    variation = random.uniform(0.9, 1.1)
                    cout_mod = round(couts["mod"] * variation, 2)
                    cout_pieces = round(couts["pieces"] * variation, 2)
                    cout_frais_externes = round(couts["externes"] * variation, 2)
                    cout_total = cout_mod + cout_pieces + cout_frais_externes
                    
                    # Durée selon type
                    durees_standard = {"Preventif": 4, "Correctif": 8, "Urgence": 6}
                    duree = durees_standard[type_choisi] + random.uniform(-1, 1)
                    duree = round(duree, 1)
                    
                    # Choisir un technicien et une équipe
                    technicien = random.choice(self.techniciens)
                    
                    # Description
                    descriptions = {
                        "Preventif": "Maintenance préventive programmée",
                        "Correctif": "Réparation suite à dysfonctionnement", 
                        "Urgence": "Intervention d'urgence"
                    }
                    
                    # Créer l'intervention
                    cur.execute("""
                        INSERT INTO MAINTENANCE (
                            id_machine, type_reel, date_realisation, 
                            description, duree_intervention_h,
                            cout_main_oeuvre, cout_pieces, cout_frais_externes, cout_total,
                            id_technicien_principal, id_equipe, statut
                        ) VALUES (
                            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 'Terminé'
                        ) RETURNING id_maintenance
                    """, [
                        machine['id'], type_choisi, date_intervention,
                        descriptions[type_choisi], duree,
                        cout_mod, cout_pieces, cout_frais_externes, cout_total,
                        technicien['id'], technicien['equipe_id']
                    ])
                    
                    result = cur.fetchone()
                    maintenances_count += 1
                    
                    if maintenances_count % 20 == 0:
                        print(f"  ✓ {maintenances_count} interventions créées...")
        
        self.maintenances_created = maintenances_count
        print(f"  ✅ Total: {maintenances_count} interventions de maintenance créées")
    
    def print_summary(self):
        """Affiche un résumé des données générées"""
        print("\n" + "="*50)
        print("📊 RÉSUMÉ DES DONNÉES GÉNÉRÉES")
        print("="*50)
        print(f"Sites: {len(self.sites)}")
        print(f"Types de machines: {len(self.types_machines)}")
        print(f"Machines: {len(self.machines)}")
        print(f"Équipes: {len(self.equipes)}")
        print(f"Techniciens: {len(self.techniciens)}")
        print(f"Interventions de maintenance: {self.maintenances_created}")
        
        print(f"\n💰 COÛTS STANDARDISÉS POUR TESTS:")
        print(f"  • Préventif: ~430€ (MOD: 280€, Pièces: 150€)")
        print(f"  • Correctif: ~860€ (MOD: 560€, Pièces: 300€)")
        print(f"  • Urgence: ~1540€ (MOD: 840€, Pièces: 500€, Externes: 200€)")
        
        print(f"\n🎯 Ces données sont maintenant prêtes pour tester les KPI!")

def main():
    """Fonction principale"""
    print("🎯 Générateur simplifié de données de test GMAO")
    print("=" * 50)
    
    # Demander confirmation
    response = input("⚠️  Voulez-vous générer les données de test ? (oui/non): ")
    if response.lower() not in ['oui', 'o', 'yes', 'y']:
        print("Génération annulée.")
        return
    
    # Générer les données
    try:
        generator = SimpleTestDataGenerator()
        generator.generate_all_test_data()
        
        print("\n✅ Données de test générées avec succès!")
        print("Vous pouvez maintenant tester les KPI avec des données cohérentes.")
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return 1

if __name__ == "__main__":
    main()
