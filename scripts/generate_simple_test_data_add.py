#!/usr/bin/env python3
"""
Script simplifié de génération de données de test pour la GMAO
Ajoute des données sans nettoyer l'existant pour éviter les conflits de contraintes
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
        password=os.getenv('POSTGRES_PASSWORD', 'postgres'),
        host=os.getenv('POSTGRES_HOST', 'localhost'),
        port=os.getenv('POSTGRES_PORT', '5432'),
        cursor_factory=psycopg2.extras.RealDictCursor
    )

class SimpleTestDataGenerator:
    """Générateur simplifié de données de test pour la GMAO"""
    
    def __init__(self):
        self.sites = []
        self.fabricants = []
        self.types_machines = []
        self.machines = []
        self.equipes = []
        self.techniciens = []
        self.utilisateurs = []
        self.maintenances_created = 0
        
    def generate_test_data(self):
        """Génère un jeu de données de test"""
        print("🚀 Génération de données de test GMAO (mode ajout)...")
        
        try:
            with get_db_connection() as conn:
                self.conn = conn
                
                # Récupérer les données existantes
                self.load_existing_data()
                
                # Créer des données si nécessaire
                if len(self.sites) == 0:
                    self.create_sites()
                if len(self.fabricants) == 0:
                    self.create_fabricants()
                if len(self.types_machines) == 0:
                    self.create_types_machines()
                if len(self.equipes) == 0:
                    self.create_equipes()
                if len(self.techniciens) == 0:
                    self.create_techniciens()
                if len(self.utilisateurs) == 0:
                    self.create_utilisateurs()
                if len(self.machines) == 0:
                    self.create_machines()
                
                # Toujours créer des nouvelles maintenances
                self.create_maintenances()
                
                conn.commit()
                
            print("✅ Génération terminée avec succès!")
            self.print_summary()
            
        except Exception as e:
            print(f"❌ Erreur lors de la génération: {e}")
            if hasattr(self, 'conn'):
                self.conn.rollback()
            raise
    
    def load_existing_data(self):
        """Charge les données existantes de la base"""
        print("📋 Chargement des données existantes...")
        
        with self.conn.cursor() as cur:
            # Sites
            cur.execute("SELECT id_site, nom, ville FROM SITE")
            self.sites = [dict(row) for row in cur.fetchall()]
            print(f"  ✓ Sites existants: {len(self.sites)}")
            
            # Fabricants
            cur.execute("SELECT id_fabricant, nom FROM FABRICANT")
            self.fabricants = [dict(row) for row in cur.fetchall()]
            print(f"  ✓ Fabricants existants: {len(self.fabricants)}")
            
            # Types machines
            cur.execute("SELECT id_type_machine, nom, categorie FROM TYPE_MACHINE")
            self.types_machines = [dict(row) for row in cur.fetchall()]
            print(f"  ✓ Types machines existants: {len(self.types_machines)}")
            
            # Équipes
            cur.execute("SELECT id_equipe, nom, domaine_expertise FROM EQUIPE")
            for row in cur.fetchall():
                self.equipes.append({
                    'id': row['id_equipe'],
                    'nom': row['nom'],
                    'domaine': row['domaine_expertise']
                })
            print(f"  ✓ Équipes existantes: {len(self.equipes)}")
            
            # Techniciens
            cur.execute("SELECT id_technicien, nom, prenom, equipe_id, cout_horaire FROM TECHNICIEN")
            for row in cur.fetchall():
                self.techniciens.append({
                    'id': row['id_technicien'],
                    'nom_complet': f"{row['prenom']} {row['nom']}",
                    'equipe_id': row['equipe_id'],
                    'cout_horaire': row['cout_horaire'] or 35.0
                })
            print(f"  ✓ Techniciens existants: {len(self.techniciens)}")
            
            # Utilisateurs
            cur.execute("SELECT id_utilisateur, login, role, technicien_id FROM UTILISATEUR")
            for row in cur.fetchall():
                self.utilisateurs.append({
                    'id': row['id_utilisateur'],
                    'login': row['login'],
                    'role': row['role'],
                    'technicien_id': row['technicien_id']
                })
            print(f"  ✓ Utilisateurs existants: {len(self.utilisateurs)}")
            
            # Machines
            cur.execute("""
                SELECT m.id_machine, m.nom, m.serial, m.site_id, s.nom as site_nom,
                       m.type_machine_id, tm.nom as type_nom, m.criticite, m.fabricant_id
                FROM MACHINE m
                JOIN SITE s ON m.site_id = s.id_site
                JOIN TYPE_MACHINE tm ON m.type_machine_id = tm.id_type_machine
            """)
            for row in cur.fetchall():
                self.machines.append({
                    'id': row['id_machine'],
                    'nom': row['nom'],
                    'serial': row['serial'],
                    'site_id': row['site_id'],
                    'site_nom': row['site_nom'],
                    'type_id': row['type_machine_id'],
                    'type_nom': row['type_nom'],
                    'criticite': row['criticite'],
                    'fabricant_id': row['fabricant_id']
                })
            print(f"  ✓ Machines existantes: {len(self.machines)}")
    
    def create_sites(self):
        """Crée les sites de test"""
        sites_data = [
            ("Site Production Nord", "Zone industrielle Nord", "Lille", "France", "Pierre Martin"),
            ("Site Production Sud", "Zone industrielle Sud", "Marseille", "France", "Marie Dubois"),
            ("Site Logistique Est", "Zone logistique", "Strasbourg", "France", "Jean Moreau"),
            ("Site R&D Central", "Technopole", "Lyon", "France", "Sophie Lambert")
        ]
        
        print("📍 Création des sites...")
        with self.conn.cursor() as cur:
            for nom, adresse, ville, pays, contact in sites_data:
                cur.execute("""
                    INSERT INTO SITE (nom, adresse, ville, pays, contact_principal)
                    VALUES (%s, %s, %s, %s, %s)
                    RETURNING id_site
                """, [nom, adresse, ville, pays, contact])
                
                result = cur.fetchone()
                self.sites.append({
                    'id': result['id_site'],
                    'nom': nom,
                    'ville': ville
                })
                print(f"  ✓ Site créé: {nom} (ID: {result['id_site']})")
    
    def create_fabricants(self):
        """Crée les fabricants de test"""
        fabricants_data = [
            ("Siemens", "contact@siemens.fr", "https://siemens.fr", "support-tech@siemens.fr"),
            ("Schneider Electric", "info@schneider.fr", "https://schneider-electric.fr", "support@schneider.fr"),
            ("ABB", "contact@abb.fr", "https://abb.fr", "technical@abb.fr")
        ]
        
        print("🏭 Création des fabricants...")
        with self.conn.cursor() as cur:
            for nom, contact, site_web, support in fabricants_data:
                cur.execute("""
                    INSERT INTO FABRICANT (nom, contact, site_web, support_technique)
                    VALUES (%s, %s, %s, %s)
                    RETURNING id_fabricant
                """, [nom, contact, site_web, support])
                
                result = cur.fetchone()
                self.fabricants.append({
                    'id': result['id_fabricant'],
                    'nom': nom
                })
                print(f"  ✓ Fabricant créé: {nom} (ID: {result['id_fabricant']})")
    
    def create_types_machines(self):
        """Crée les types de machines"""
        types_data = [
            ("Presse hydraulique", "Machines de production haute cadence", "Production"),
            ("Tour CNC", "Machines d'usinage de précision", "Production"),
            ("Convoyeur", "Systèmes de transport interne", "Logistique"),
            ("Compresseur", "Équipements de production d'air comprimé", "Utilités")
        ]
        
        print("🤖 Création des types de machines...")
        with self.conn.cursor() as cur:
            for nom, description, categorie in types_data:
                cur.execute("""
                    INSERT INTO TYPE_MACHINE (nom, description, categorie)
                    VALUES (%s, %s, %s)
                    RETURNING id_type_machine
                """, [nom, description, categorie])
                
                result = cur.fetchone()
                self.types_machines.append({
                    'id': result['id_type_machine'],
                    'nom': nom,
                    'categorie': categorie
                })
                print(f"  ✓ Type créé: {nom} (ID: {result['id_type_machine']})")
    
    def create_equipes(self):
        """Crée les équipes de maintenance"""
        equipes_data = [
            ("Équipe Mécanique", "Mécanique"),
            ("Équipe Électrique", "Électricité"),
            ("Équipe Polyvalente", "Polyvalente")
        ]
        
        print("👥 Création des équipes...")
        with self.conn.cursor() as cur:
            for nom, domaine in equipes_data:
                cur.execute("""
                    INSERT INTO EQUIPE (nom, domaine_expertise)
                    VALUES (%s, %s)
                    RETURNING id_equipe
                """, [nom, domaine])
                
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
        
        techniciens_data = [
            ("Martin", "Pierre", "Mécanicien", 35.0),
            ("Dubois", "Marie", "Électricienne", 38.0),
            ("Moreau", "Jean", "Polyvalent", 33.0),
            ("Lambert", "Sophie", "Automaticienne", 42.0)
        ]
        
        with self.conn.cursor() as cur:
            for i, (nom, prenom, qualification, cout) in enumerate(techniciens_data):
                equipe = self.equipes[i % len(self.equipes)]
                
                cur.execute("""
                    INSERT INTO TECHNICIEN (nom, prenom, qualification, contact, cout_horaire, equipe_id, actif)
                    VALUES (%s, %s, %s, %s, %s, %s, 1)
                    RETURNING id_technicien
                """, [nom, prenom, qualification, f"{prenom.lower()}.{nom.lower()}@gmao.fr", cout, equipe['id']])
                
                result = cur.fetchone()
                self.techniciens.append({
                    'id': result['id_technicien'],
                    'nom_complet': f"{prenom} {nom}",
                    'equipe_id': equipe['id'],
                    'cout_horaire': cout
                })
                print(f"  ✓ Technicien créé: {prenom} {nom} (ID: {result['id_technicien']})")
    
    def create_utilisateurs(self):
        """Crée les utilisateurs du système"""
        print("👤 Création des utilisateurs...")
        
        with self.conn.cursor() as cur:
            # Utilisateur admin
            cur.execute("""
                INSERT INTO UTILISATEUR (login, mot_de_passe_hash, nom_complet, role, email, actif)
                VALUES (%s, %s, %s, %s, %s, 1)
                RETURNING id_utilisateur
            """, ["admin", "admin_hash", "Administrateur Système", "Admin", "admin@gmao.fr"])
            
            result = cur.fetchone()
            self.utilisateurs.append({
                'id': result['id_utilisateur'],
                'login': "admin",
                'role': "Admin"
            })
            print(f"  ✓ Utilisateur admin créé (ID: {result['id_utilisateur']})")
    
    def create_machines(self):
        """Crée les machines de test"""
        print("🤖 Création des machines...")
        
        criticites = ["Normal", "Important", "Critique"]
        machine_counter = 1
        
        with self.conn.cursor() as cur:
            for site in self.sites:
                for type_machine in self.types_machines:
                    # 2 machines par type par site
                    for i in range(2):
                        nom = f"{type_machine['nom']}-{site['ville']}-{machine_counter:03d}"
                        serial = f"SN{machine_counter:06d}"
                        criticite = random.choice(criticites)
                        fabricant = random.choice(self.fabricants)
                        
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
                            nom, serial, f"Modèle-{random.randint(100, 999)}", 
                            installation.isoformat(), f"Zone {i+1}", "En Service",
                            f"Machine {nom}", type_machine['id'], site['id'], 
                            fabricant['id'], criticite, garantie_fin.isoformat()
                        ])
                        
                        result = cur.fetchone()
                        self.machines.append({
                            'id': result['id_machine'],
                            'nom': nom,
                            'serial': serial,
                            'site_id': site['id'],
                            'site_nom': site['nom'],
                            'type_id': type_machine['id'],
                            'type_nom': type_machine['nom'],
                            'criticite': criticite,
                            'fabricant_id': fabricant['id']
                        })
                        
                        machine_counter += 1
                        print(f"  ✓ Machine créée: {nom} (ID: {result['id_machine']})")
    
    def create_maintenances(self):
        """Crée des interventions de maintenance avec des valeurs facilement contrôlables"""
        print("🔧 Génération des interventions de maintenance...")
        
        if not self.machines or not self.techniciens or not self.utilisateurs:
            print("  ⚠️ Pas assez de données de base pour créer les maintenances")
            return
        
        # Période de génération : 6 derniers mois
        date_fin = date.today()
        date_debut = date_fin - timedelta(days=180)
        
        types_maintenance = ["Preventif", "Correctif", "Urgence"]
        
        # Coûts standardisés pour faciliter les tests
        couts_standard = {
            "Preventif": {"mod": 350, "pieces_int": 200, "pieces_ext": 0, "autres": 0},        # 550 € total
            "Correctif": {"mod": 700, "pieces_int": 400, "pieces_ext": 0, "autres": 0},        # 1100 € total  
            "Urgence": {"mod": 1050, "pieces_int": 600, "pieces_ext": 0, "autres": 300}        # 1950 € total
        }
        
        ot_counter = 1000  # Commencer à 1000 pour éviter les conflits
        maintenances_count = 0
        
        with self.conn.cursor() as cur:
            for machine in self.machines:
                # Nombre d'interventions selon la criticité (sur 6 mois)
                criticite = machine['criticite']
                if criticite in ['Normal', 'Important', 'Critique']:
                    nb_interventions = {
                        "Normal": random.randint(2, 4),
                        "Important": random.randint(3, 6), 
                        "Critique": random.randint(4, 8)
                    }[criticite]
                else:
                    # Valeur par défaut si criticité inconnue
                    nb_interventions = random.randint(3, 5)
                    print(f"  ⚠️ Criticité inconnue '{criticite}' pour machine {machine['nom']}, utilisation valeur par défaut")
                
                for i in range(nb_interventions):
                    # Type d'intervention selon la criticité
                    if criticite == "Critique":
                        type_choisi = random.choices(types_maintenance, weights=[30, 50, 20])[0]
                    elif criticite == "Important":
                        type_choisi = random.choices(types_maintenance, weights=[50, 40, 10])[0]
                    else:
                        type_choisi = random.choices(types_maintenance, weights=[60, 35, 5])[0]
                    
                    # Dates
                    days_offset = random.randint(0, 180)
                    date_intervention = date_debut + timedelta(days=days_offset)
                    date_creation = date_intervention - timedelta(days=random.randint(1, 15))
                    
                    # Choisir un technicien et utilisateur
                    technicien = random.choice(self.techniciens)
                    utilisateur = self.utilisateurs[0]  # Prendre le premier utilisateur (admin)
                    
                    # Créer l'ordre de travail
                    numero_ot = f"OT-TEST-{ot_counter}"
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
                            random.randint(120, 480), "Normale", 0, "Terminé",
                            technicien['id'], utilisateur['id']
                        ])
                        
                        ot_result = cur.fetchone()
                        ot_id = ot_result['id_ot']
                        
                        # Utiliser les coûts standardisés avec petite variation
                        couts = couts_standard[type_choisi]
                        variation = random.uniform(0.9, 1.1)  # ±10% de variation
                        
                        cout_mod = round(couts["mod"] * variation, 2)
                        cout_pieces_int = round(couts["pieces_int"] * variation, 2)
                        cout_pieces_ext = round(couts["pieces_ext"] * variation, 2)
                        cout_autres = round(couts["autres"] * variation, 2)
                        cout_total = cout_mod + cout_pieces_int + cout_pieces_ext + cout_autres
                        
                        # Durée selon type
                        durees_standard = {"Preventif": 4.0, "Correctif": 8.0, "Urgence": 6.0}
                        duree = durees_standard[type_choisi] * random.uniform(0.8, 1.2)
                        duree = round(duree, 1)
                        
                        # Date de fin
                        date_fin_reelle = date_intervention + timedelta(hours=int(duree))
                        
                        # Créer l'intervention de maintenance
                        cur.execute("""
                            INSERT INTO MAINTENANCE (
                                ot_id, machine_id, technicien_id, date_debut_reelle, date_fin_reelle,
                                duree_intervention_h, type_reel, description_travaux, resultat,
                                cout_main_oeuvre, cout_pieces_internes, cout_pieces_externes,
                                cout_autres_frais, cout_total, evaluation_qualite
                            ) VALUES (
                                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                            ) RETURNING id_maintenance
                        """, [
                            ot_id, machine['id'], technicien['id'], 
                            date_intervention.isoformat(), date_fin_reelle.isoformat(),
                            duree, type_choisi, f"Maintenance {type_choisi.lower()}", 
                            f"Intervention {type_choisi.lower()} réalisée",
                            cout_mod, cout_pieces_int, cout_pieces_ext, cout_autres, cout_total, 4
                        ])
                        
                        ot_counter += 1
                        maintenances_count += 1
                        
                        if maintenances_count % 10 == 0:
                            print(f"  ✓ {maintenances_count} interventions créées...")
                            
                    except Exception as e:
                        print(f"  ⚠️ Erreur création maintenance pour {machine['nom']}: {e}")
                        continue
        
        self.maintenances_created = maintenances_count
        print(f"  ✅ Total: {maintenances_count} interventions de maintenance créées")
    
    def print_summary(self):
        """Affiche un résumé des données générées"""
        print("\n" + "="*60)
        print("📊 RÉSUMÉ DES DONNÉES DANS LA BASE")
        print("="*60)
        print(f"Sites: {len(self.sites)}")
        print(f"Fabricants: {len(self.fabricants)}")
        print(f"Types de machines: {len(self.types_machines)}")
        print(f"Machines: {len(self.machines)}")
        print(f"Équipes: {len(self.equipes)}")
        print(f"Techniciens: {len(self.techniciens)}")
        print(f"Utilisateurs: {len(self.utilisateurs)}")
        print(f"Nouvelles interventions: {self.maintenances_created}")
        
        print(f"\n💰 COÛTS STANDARDISÉS:")
        print(f"  • Préventif: ~550€ (MOD: 350€, Pièces internes: 200€)")
        print(f"  • Correctif: ~1100€ (MOD: 700€, Pièces internes: 400€)")
        print(f"  • Urgence: ~1950€ (MOD: 1050€, Pièces internes: 600€, Autres: 300€)")
        print(f"  • Variation aléatoire: ±10% sur les coûts de base")
        
        print(f"\n🎯 Ces données sont maintenant prêtes pour tester les KPI!")

def main():
    """Fonction principale"""
    print("🎯 Générateur simplifié de données de test GMAO")
    print("📋 Mode ajout - ne supprime pas les données existantes")
    print("=" * 60)
    
    # Demander confirmation
    response = input("⚠️  Voulez-vous ajouter des données de test ? (oui/non): ")
    if response.lower() not in ['oui', 'o', 'yes', 'y']:
        print("Génération annulée.")
        return
    
    # Générer les données
    try:
        generator = SimpleTestDataGenerator()
        generator.generate_test_data()
        
        print("\n✅ Données de test ajoutées avec succès!")
        print("🚀 Vous pouvez maintenant tester les KPI avec des données cohérentes.")
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    main()
