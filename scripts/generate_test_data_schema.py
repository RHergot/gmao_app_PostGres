#!/usr/bin/env python3
"""
Script de génération de données de test pour la GMAO
Adapté à la structure exacte de la base de données (schemas.py)
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

class TestDataGenerator:
    """Générateur de données de test pour la GMAO"""
    
    def __init__(self):
        self.sites = []
        self.fabricants = []
        self.types_machines = []
        self.machines = []
        self.equipes = []
        self.techniciens = []
        self.utilisateurs = []
        self.fournisseurs = []
        self.pieces = []
        self.ordres_travail = []
        self.maintenances_created = 0
        
    def generate_all_test_data(self):
        """Génère un jeu complet de données de test"""
        print("🚀 Génération des données de test GMAO...")
        print("📋 Basé sur la structure exacte de schemas.py")
        
        try:
            with get_db_connection() as conn:
                self.conn = conn
                
                # Nettoyer les données existantes (optionnel)
                if input("🧹 Nettoyer les données existantes ? (oui/non): ").lower() in ['oui', 'o', 'yes', 'y']:
                    self.clean_test_data()
                
                # Créer les données de base dans l'ordre des dépendances
                self.create_sites()
                self.create_fabricants()
                self.create_types_machines()
                self.create_equipes()
                self.create_techniciens()
                self.create_utilisateurs()
                self.create_machines()
                self.create_fournisseurs()
                self.create_pieces()
                self.create_ordres_travail_et_maintenances()
                
                conn.commit()
                
            print("✅ Génération terminée avec succès!")
            self.print_summary()
            
        except Exception as e:
            print(f"❌ Erreur lors de la génération: {e}")
            if hasattr(self, 'conn'):
                self.conn.rollback()
            raise
    
    def clean_test_data(self):
        """Nettoie les données de test existantes"""
        print("🧹 Nettoyage des données existantes...")
        
        with self.conn.cursor() as cur:
            # Ordre important à cause des contraintes de clés étrangères
            tables_to_clean = [
                'MAINTENANCE_FRAIS_EXTERNE',
                'MAINTENANCE_INTERVENANT', 
                'INTERVENTION_PIECE',
                'MAINTENANCE',
                'ORDRE_TRAVAIL',
                'LIGNE_COMMANDE',
                'COMMANDE',
                'HISTORIQUE_COMPTEUR',
                'COMPTEUR',
                'GAMME_PIECE_TYPE',
                'GAMME_ETAPE',
                'GAMME_ENTRETIEN',
                'MOUVEMENT_STOCK',
                'PIECE',
                'MACHINE',
                'UTILISATEUR',
                'TECHNICIEN',
                'EQUIPE',
                'TYPE_MACHINE',
                'FABRICANT',
                'FOURNISSEUR',
                'SITE'
            ]
            
            for table in tables_to_clean:
                try:
                    cur.execute(f"DELETE FROM {table} WHERE 1=1")
                    rows_deleted = cur.rowcount
                    if rows_deleted > 0:
                        print(f"  ✓ Table {table}: {rows_deleted} lignes supprimées")
                except Exception as e:
                    print(f"  ⚠️ Table {table}: {e}")
    
    def create_sites(self):
        """Crée les sites de test"""
        sites_data = [
            ("Site Production Nord", "Zone industrielle Nord", "Lille", "France", "Pierre Martin"),
            ("Site Production Sud", "Zone industrielle Sud", "Marseille", "France", "Marie Dubois"),
            ("Site Logistique Est", "Zone logistique", "Strasbourg", "France", "Jean Moreau"),
            ("Site R&D Central", "Technopole", "Lyon", "France", "Sophie Lambert"),
            ("Site Maintenance", "Zone technique", "Toulouse", "France", "Michel Rousseau")
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
            ("ABB", "contact@abb.fr", "https://abb.fr", "technical@abb.fr"),
            ("Bosch Rexroth", "info@boschrexroth.fr", "https://boschrexroth.fr", "support@boschrexroth.fr"),
            ("Fanuc", "contact@fanuc.fr", "https://fanuc.fr", "service@fanuc.fr")
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
            ("Compresseur", "Équipements de production d'air comprimé", "Utilités"),
            ("Robot soudage", "Robots industriels de soudage", "Production"),
            ("Pont roulant", "Équipements de levage lourd", "Manutention"),
            ("Groupe électrogène", "Équipements de secours électrique", "Utilités")
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
            ("Équipe Mécanique Nord", "Mécanique", "Maintenance mécanique site Nord"),
            ("Équipe Électrique Nord", "Électricité", "Maintenance électrique site Nord"),
            ("Équipe Mécanique Sud", "Mécanique", "Maintenance mécanique site Sud"),
            ("Équipe Polyvalente Est", "Polyvalente", "Maintenance générale site Est"),
            ("Équipe Spécialisée R&D", "Spécialisée", "Maintenance équipements R&D"),
            ("Équipe Utilités", "Utilités", "Maintenance des utilités générales")
        ]
        
        print("👥 Création des équipes...")
        with self.conn.cursor() as cur:
            for nom, domaine, description in equipes_data:
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
        
        prenoms = ["Pierre", "Marie", "Jean", "Sophie", "Michel", "Isabelle", "David", "Catherine", "Philippe", "Nathalie"]
        noms = ["Martin", "Dubois", "Moreau", "Lambert", "Rousseau", "Garcia", "Roux", "Fournier", "Leroy", "Simon"]
        qualifications = ["Mécanicien", "Électricien", "Automaticien", "Polyvalent", "Spécialisé"]
        
        with self.conn.cursor() as cur:
            for equipe in self.equipes:
                # 2-4 techniciens par équipe
                nb_techs = random.randint(2, 4)
                
                for i in range(nb_techs):
                    prenom = random.choice(prenoms)
                    nom = random.choice(noms)
                    qualification = random.choice(qualifications)
                    cout_horaire = round(random.uniform(30.0, 50.0), 2)
                    
                    cur.execute("""
                        INSERT INTO TECHNICIEN (nom, prenom, qualification, contact, cout_horaire, equipe_id, actif)
                        VALUES (%s, %s, %s, %s, %s, %s, 1)
                        RETURNING id_technicien
                    """, [nom, prenom, qualification, f"{prenom.lower()}.{nom.lower()}@gmao.fr", cout_horaire, equipe['id']])
                    
                    result = cur.fetchone()
                    self.techniciens.append({
                        'id': result['id_technicien'],
                        'nom_complet': f"{prenom} {nom}",
                        'equipe_id': equipe['id'],
                        'equipe_nom': equipe['nom'],
                        'cout_horaire': cout_horaire
                    })
                    
                    print(f"  ✓ Technicien créé: {prenom} {nom} (ID: {result['id_technicien']})")
    
    def create_utilisateurs(self):
        """Crée les utilisateurs du système"""
        print("👤 Création des utilisateurs...")
        
        # Utilisateur admin
        with self.conn.cursor() as cur:
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
            
            # Utilisateurs pour chaque technicien
            for tech in self.techniciens:
                login = f"tech{tech['id']}"
                cur.execute("""
                    INSERT INTO UTILISATEUR (login, mot_de_passe_hash, nom_complet, role, email, actif, technicien_id)
                    VALUES (%s, %s, %s, %s, %s, 1, %s)
                    RETURNING id_utilisateur
                """, [login, "tech_hash", tech['nom_complet'], "Technicien", 
                     f"{login}@gmao.fr", tech['id']])
                
                result = cur.fetchone()
                self.utilisateurs.append({
                    'id': result['id_utilisateur'],
                    'login': login,
                    'role': "Technicien",
                    'technicien_id': tech['id']
                })
    
    def create_machines(self):
        """Crée les machines de test"""
        print("🤖 Création des machines...")
        
        criticites = ["Normal", "Important", "Critique"]
        etats = ["En Service", "En Panne", "En Maintenance", "Arrêtée"]
        machine_counter = 1
        
        with self.conn.cursor() as cur:
            for site in self.sites:
                for type_machine in self.types_machines:
                    # 2-3 machines par type par site
                    nb_machines = random.randint(2, 3)
                    
                    for i in range(nb_machines):
                        nom = f"{type_machine['nom']}-{site['ville']}-{machine_counter:03d}"
                        serial = f"SN{machine_counter:06d}"
                        modele = f"Modèle-{random.randint(100, 999)}"
                        criticite = random.choice(criticites)
                        etat = random.choice(etats)
                        fabricant = random.choice(self.fabricants)
                        
                        # Dates
                        installation = date.today() - timedelta(days=random.randint(365, 3650))
                        garantie_fin = installation + timedelta(days=random.randint(365, 1825))
                        
                        cur.execute("""
                            INSERT INTO MACHINE (
                                nom, serial, modele, date_installation, localisation, etat,
                                informations_techniques, type_machine_id, site_id, fabricant_id,
                                criticite, garantie_fin
                            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                            RETURNING id_machine
                        """, [
                            nom, serial, modele, installation.isoformat(), f"Zone {i+1}", etat,
                            f"Machine {nom} - Spécifications techniques", type_machine['id'],
                            site['id'], fabricant['id'], criticite, garantie_fin.isoformat()
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
    
    def create_fournisseurs(self):
        """Crée les fournisseurs de test"""
        fournisseurs_data = [
            ("Fournisseur Pièces Nord", "contact@fpn.fr", "123 Rue Industrie, Lille", "03.20.xx.xx.xx", "fpn@email.fr", 5, "EUR", 4.2),
            ("Fournitures Méca Sud", "info@fms.fr", "456 Av Production, Marseille", "04.91.xx.xx.xx", "fms@email.fr", 7, "EUR", 3.8),
            ("Électro Composants", "vente@electro.fr", "789 Bd Électronique, Lyon", "04.72.xx.xx.xx", "electro@email.fr", 3, "EUR", 4.5),
            ("Hydraulique Toulouse", "commercial@hydrau.fr", "321 Rue Hydraulique, Toulouse", "05.61.xx.xx.xx", "hydrau@email.fr", 4, "EUR", 4.0),
            ("Automatismes Est", "contact@auto-est.fr", "654 Av Automatique, Strasbourg", "03.88.xx.xx.xx", "auto@email.fr", 6, "EUR", 3.9)
        ]
        
        print("🏪 Création des fournisseurs...")
        with self.conn.cursor() as cur:
            for nom, contact, adresse, tel, email, delai, devise, note in fournisseurs_data:
                cur.execute("""
                    INSERT INTO FOURNISSEUR (
                        nom, contact, adresse, telephone, email, 
                        delai_livraison_moyen_j, devise, note_qualite
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING id_fournisseur
                """, [nom, contact, adresse, tel, email, delai, devise, note])
                
                result = cur.fetchone()
                self.fournisseurs.append({
                    'id': result['id_fournisseur'],
                    'nom': nom
                })
                print(f"  ✓ Fournisseur créé: {nom} (ID: {result['id_fournisseur']})")
    
    def create_pieces(self):
        """Crée les pièces de test"""
        print("🔧 Création des pièces...")
        
        pieces_data = [
            ("ROUL-001", "Roulement à billes 6205", "Roulement", "pièce", 15.50, 10, 50),
            ("COUR-001", "Courroie trapézoïdale A50", "Courroie", "pièce", 8.75, 5, 25),
            ("HUILE-001", "Huile hydraulique HV46", "Huile", "litre", 12.30, 20, 100),
            ("FILTRE-001", "Filtre à air industriel", "Filtre", "pièce", 25.80, 8, 30),
            ("CONTACT-001", "Contacteur électrique 3P", "Électrique", "pièce", 45.90, 12, 40),
            ("JOINT-001", "Joint torique NBR", "Joint", "pièce", 3.20, 15, 100),
            ("VIS-001", "Vis CHC M8x20", "Visserie", "pièce", 0.85, 50, 500),
            ("CABLE-001", "Câble électrique 3x2.5mm", "Électrique", "mètre", 2.15, 100, 1000)
        ]
        
        with self.conn.cursor() as cur:
            for ref, nom, categorie, unite, prix, seuil, stock in pieces_data:
                fournisseur = random.choice(self.fournisseurs)
                
                cur.execute("""
                    INSERT INTO PIECE (
                        reference, nom, fournisseur_pref_id, prix_unitaire,
                        stock_alerte, stock_actuel, stock_reserve, unite, categorie,
                        emplacement_stockage, statut
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING id_piece
                """, [
                    ref, nom, fournisseur['id'], prix, seuil, stock,
                    random.randint(0, stock//4), unite, categorie,
                    f"Magasin-Zone-{random.randint(1,5)}", "Actif"
                ])
                
                result = cur.fetchone()
                self.pieces.append({
                    'id': result['id_piece'],
                    'reference': ref,
                    'nom': nom,
                    'prix_unitaire': prix
                })
                print(f"  ✓ Pièce créée: {ref} - {nom} (ID: {result['id_piece']})")
    
    def create_ordres_travail_et_maintenances(self):
        """Crée les ordres de travail et maintenances avec des valeurs facilement contrôlables"""
        print("📋 Génération des ordres de travail et maintenances...")
        
        # Période de génération : 12 derniers mois
        date_fin = date.today()
        date_debut = date_fin - timedelta(days=365)
        
        types_maintenance = ["Preventif", "Correctif", "Urgence"]
        statuts_ot = ["Planifié", "En Cours", "Terminé"]
        priorites = ["Normale", "Élevée", "Critique"]
        
        # Coûts standardisés pour faciliter les tests
        couts_standard = {
            "Preventif": {"mod_base": 280, "pieces_base": 150, "externes_base": 0},      # 430 € total
            "Correctif": {"mod_base": 560, "pieces_base": 300, "externes_base": 0},      # 860 € total  
            "Urgence": {"mod_base": 840, "pieces_base": 500, "externes_base": 200}       # 1540 € total
        }
        
        ot_counter = 1
        maintenances_count = 0
        
        with self.conn.cursor() as cur:
            # Générer des maintenances pour chaque machine
            for machine in self.machines:
                
                # Nombre d'interventions selon la criticité
                nb_interventions = {
                    "Normal": random.randint(4, 7),
                    "Important": random.randint(6, 10), 
                    "Critique": random.randint(8, 15)
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
                    
                    # Dates
                    days_offset = random.randint(0, 365)
                    date_intervention = date_debut + timedelta(days=days_offset)
                    date_creation = date_intervention - timedelta(days=random.randint(1, 30))
                    
                    # Choisir un technicien et utilisateur
                    technicien = random.choice(self.techniciens)
                    utilisateur = random.choice([u for u in self.utilisateurs if u['role'] in ['Admin', 'Technicien']])
                    
                    # Priorité selon type
                    priorite = {
                        "Preventif": "Normale",
                        "Correctif": random.choice(["Normale", "Élevée"]),
                        "Urgence": random.choice(["Élevée", "Critique"])
                    }[type_choisi]
                    
                    # Créer l'ordre de travail
                    numero_ot = f"OT-{ot_counter:06d}"
                    description_ot = f"Maintenance {type_choisi.lower()} - {machine['nom']}"
                    
                    cur.execute("""
                        INSERT INTO ORDRE_TRAVAIL (
                            numero_ot, machine_id, type, description, date_creation,
                            date_prevue, duree_prevue_min, priorite, urgence, statut,
                            technicien_assigne_id, utilisateur_createur_id, notes_planification
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        RETURNING id_ot
                    """, [
                        numero_ot, machine['id'], type_choisi, description_ot,
                        date_creation.isoformat(), date_intervention.isoformat(),
                        random.randint(120, 480), priorite, 1 if type_choisi == "Urgence" else 0,
                        "Terminé", technicien['id'], utilisateur['id'],
                        f"Planification {type_choisi.lower()}"
                    ])
                    
                    ot_result = cur.fetchone()
                    ot_id = ot_result['id_ot']
                    
                    # Utiliser les coûts standardisés avec petite variation
                    couts = couts_standard[type_choisi]
                    variation = random.uniform(0.85, 1.15)  # ±15% de variation
                    
                    cout_mod = round(couts["mod_base"] * variation, 2)
                    cout_pieces_int = round(couts["pieces_base"] * variation, 2)
                    cout_pieces_ext = 0
                    cout_frais_autres = round(couts["externes_base"] * variation, 2)
                    cout_total = cout_mod + cout_pieces_int + cout_pieces_ext + cout_frais_autres
                    
                    # Durée selon type
                    durees_standard = {"Preventif": 4.0, "Correctif": 8.0, "Urgence": 6.0}
                    duree = durees_standard[type_choisi] * random.uniform(0.8, 1.2)
                    duree = round(duree, 1)
                    
                    # Date de fin
                    date_fin_reelle = date_intervention + timedelta(hours=int(duree))
                    
                    # Descriptions
                    descriptions = {
                        "Preventif": "Maintenance préventive programmée selon planning",
                        "Correctif": "Réparation suite à dysfonctionnement détecté", 
                        "Urgence": "Intervention d'urgence - arrêt production"
                    }
                    
                    resultats = {
                        "Preventif": "Maintenance préventive réalisée avec succès",
                        "Correctif": "Dysfonctionnement corrigé - machine remise en service",
                        "Urgence": "Problème urgent résolu - production redémarrée"
                    }
                    
                    # Créer l'intervention de maintenance
                    cur.execute("""
                        INSERT INTO MAINTENANCE (
                            ot_id, machine_id, technicien_id, date_debut_reelle, date_fin_reelle,
                            duree_intervention_h, type_reel, description_travaux, resultat,
                            cout_main_oeuvre, cout_pieces_internes, cout_pieces_externes,
                            cout_autres_frais, cout_total, evaluation_qualite, impact_production,
                            notes_technicien
                        ) VALUES (
                            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                        ) RETURNING id_maintenance
                    """, [
                        ot_id, machine['id'], technicien['id'], 
                        date_intervention.isoformat(), date_fin_reelle.isoformat(),
                        duree, type_choisi, descriptions[type_choisi], resultats[type_choisi],
                        cout_mod, cout_pieces_int, cout_pieces_ext, cout_frais_autres, cout_total,
                        random.randint(3, 5), f"Impact {type_choisi.lower()}", 
                        f"Notes technicien - Intervention {type_choisi.lower()}"
                    ])
                    
                    maintenance_result = cur.fetchone()
                    
                    # Ajouter quelques pièces utilisées (optionnel)
                    if random.random() < 0.7:  # 70% de chance d'utiliser des pièces
                        nb_pieces = random.randint(1, 3)
                        pieces_utilisees = random.sample(self.pieces, min(nb_pieces, len(self.pieces)))
                        
                        for piece in pieces_utilisees:
                            quantite = random.randint(1, 5)
                            cur.execute("""
                                INSERT INTO INTERVENTION_PIECE (maintenance_id, piece_id, quantite, lot)
                                VALUES (%s, %s, %s, %s)
                            """, [maintenance_result['id_maintenance'], piece['id'], quantite, f"LOT-{random.randint(1000, 9999)}"])
                    
                    ot_counter += 1
                    maintenances_count += 1
                    
                    if maintenances_count % 25 == 0:
                        print(f"  ✓ {maintenances_count} interventions créées...")
        
        self.maintenances_created = maintenances_count
        print(f"  ✅ Total: {maintenances_count} interventions de maintenance créées")
    
    def print_summary(self):
        """Affiche un résumé des données générées"""
        print("\n" + "="*60)
        print("📊 RÉSUMÉ DES DONNÉES GÉNÉRÉES")
        print("="*60)
        print(f"Sites: {len(self.sites)}")
        print(f"Fabricants: {len(self.fabricants)}")
        print(f"Types de machines: {len(self.types_machines)}")
        print(f"Machines: {len(self.machines)}")
        print(f"Équipes: {len(self.equipes)}")
        print(f"Techniciens: {len(self.techniciens)}")
        print(f"Utilisateurs: {len(self.utilisateurs)}")
        print(f"Fournisseurs: {len(self.fournisseurs)}")
        print(f"Pièces: {len(self.pieces)}")
        print(f"Interventions de maintenance: {self.maintenances_created}")
        
        print(f"\n💰 COÛTS STANDARDISÉS POUR TESTS:")
        print(f"  • Préventif: ~430€ (MOD: 280€, Pièces: 150€)")
        print(f"  • Correctif: ~860€ (MOD: 560€, Pièces: 300€)")
        print(f"  • Urgence: ~1540€ (MOD: 840€, Pièces: 500€, Externes: 200€)")
        print(f"  • Variation aléatoire: ±15% sur les coûts de base")
        
        print(f"\n🎯 Répartition par criticité:")
        criticites = {}
        for machine in self.machines:
            crit = machine['criticite']
            criticites[crit] = criticites.get(crit, 0) + 1
        for crit, count in criticites.items():
            print(f"  • {crit}: {count} machines")
        
        print(f"\n✅ Ces données sont maintenant prêtes pour tester les KPI!")

def main():
    """Fonction principale"""
    print("🎯 Générateur de données de test GMAO")
    print("📋 Adapté à la structure exacte de schemas.py")
    print("=" * 60)
    
    # Demander confirmation
    response = input("⚠️  Voulez-vous générer les données de test ? (oui/non): ")
    if response.lower() not in ['oui', 'o', 'yes', 'y']:
        print("Génération annulée.")
        return
    
    # Générer les données
    try:
        generator = TestDataGenerator()
        generator.generate_all_test_data()
        
        print("\n✅ Données de test générées avec succès!")
        print("Vous pouvez maintenant tester les KPI avec des données cohérentes et contrôlables.")
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    main()
