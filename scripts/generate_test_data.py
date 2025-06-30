#!/usr/bin/env python3
"""
Script de génération de données de test pour la GMAO
Génère des données cohérentes et facilement contrôlables pour tester les KPI
"""

import sys
import os
import random
from datetime import datetime, date, timedelta
from decimal import Decimal

# Ajouter le chemin du projet
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from app.data.database import get_connection, execute_query, fetch_all, fetch_one

class TestDataGenerator:
    """Générateur de données de test pour la GMAO"""
    
    def __init__(self):
        self.sites = []
        self.types_machines = []
        self.machines = []
        self.equipes = []
        self.techniciens = []
        self.fournisseurs = []
        
    def generate_all_test_data(self):
        """Génère un jeu complet de données de test"""
        print("🚀 Génération des données de test GMAO...")
        
        try:
            self.create_sites()
            self.create_types_machines()
            self.create_machines()
            self.create_equipes()
            self.create_techniciens()
            self.create_fournisseurs()
            self.create_pieces()
            self.create_maintenances()
            
            print("✅ Génération terminée avec succès!")
            self.print_summary()
            
        except Exception as e:
            print(f"❌ Erreur lors de la génération: {e}")
            raise
    
    def create_sites(self):
        """Crée les sites de test"""
        sites_data = [
            ("Site Production Nord", "Lille", "France", "Zone industrielle Nord", "59000"),
            ("Site Production Sud", "Marseille", "France", "Zone industrielle Sud", "13000"),
            ("Site Logistique Est", "Strasbourg", "France", "Zone logistique", "67000"),
            ("Site R&D Central", "Lyon", "France", "Technopole", "69000"),
            ("Site Maintenance", "Toulouse", "France", "Zone technique", "31000")
        ]
        
        print("📍 Création des sites...")
        for nom, ville, pays, adresse, code_postal in sites_data:
            query = """
            INSERT INTO SITE (nom, ville, pays, adresse, code_postal, actif)
            VALUES (%s, %s, %s, %s, %s, true)
            RETURNING id_site
            """
            result = fetch_one(query, [nom, ville, pays, adresse, code_postal])
            self.sites.append({
                'id': result['id_site'],
                'nom': nom,
                'ville': ville
            })
            print(f"  ✓ Site créé: {nom} ({ville})")
    
    def create_types_machines(self):
        """Crée les types de machines"""
        types_data = [
            ("Presse hydraulique", "Production", "Machines de production haute cadence"),
            ("Tour CNC", "Production", "Machines d'usinage de précision"),
            ("Convoyeur", "Logistique", "Systèmes de transport interne"),
            ("Compresseur", "Utilités", "Équipements de production d'air comprimé"),
            ("Groupe électrogène", "Utilités", "Équipements de secours électrique"),
            ("Robot soudage", "Production", "Robots industriels de soudage"),
            ("Pont roulant", "Manutention", "Équipements de levage lourd")
        ]
        
        print("🏭 Création des types de machines...")
        for nom, categorie, description in types_data:
            query = """
            INSERT INTO TYPE_MACHINE (nom, categorie, description)
            VALUES (%s, %s, %s)
            RETURNING id_type_machine
            """
            result = fetch_one(query, [nom, categorie, description])
            self.types_machines.append({
                'id': result['id_type_machine'],
                'nom': nom,
                'categorie': categorie
            })
            print(f"  ✓ Type créé: {nom} ({categorie})")
    
    def create_machines(self):
        """Crée les machines de test"""
        print("🤖 Création des machines...")
        
        # Répartition par site et type
        machines_config = [
            # Site Production Nord - machines coûteuses
            {"site_idx": 0, "type_idx": 0, "prefix": "PRESS", "count": 3, "criticite": "Critique"},
            {"site_idx": 0, "type_idx": 1, "prefix": "TOUR", "count": 2, "criticite": "Important"},
            {"site_idx": 0, "type_idx": 5, "prefix": "ROBOT", "count": 2, "criticite": "Critique"},
            
            # Site Production Sud - machines moyennes
            {"site_idx": 1, "type_idx": 0, "prefix": "PRESS", "count": 2, "criticite": "Important"},
            {"site_idx": 1, "type_idx": 1, "prefix": "TOUR", "count": 3, "criticite": "Important"},
            {"site_idx": 1, "type_idx": 2, "prefix": "CONV", "count": 4, "criticite": "Normal"},
            
            # Site Logistique Est - équipements logistiques
            {"site_idx": 2, "type_idx": 2, "prefix": "CONV", "count": 6, "criticite": "Normal"},
            {"site_idx": 2, "type_idx": 6, "prefix": "PONT", "count": 2, "criticite": "Important"},
            
            # Site R&D Central - équipements spécialisés
            {"site_idx": 3, "type_idx": 1, "prefix": "TOUR", "count": 2, "criticite": "Important"},
            {"site_idx": 3, "type_idx": 5, "prefix": "ROBOT", "count": 1, "criticite": "Critique"},
            
            # Site Maintenance - utilités
            {"site_idx": 4, "type_idx": 3, "prefix": "COMP", "count": 3, "criticite": "Critique"},
            {"site_idx": 4, "type_idx": 4, "prefix": "GENE", "count": 2, "criticite": "Critique"}
        ]
        
        machine_counter = 1
        for config in machines_config:
            site = self.sites[config["site_idx"]]
            type_machine = self.types_machines[config["type_idx"]]
            
            for i in range(config["count"]):
                serial = f"{config['prefix']}-{site['ville'][:3].upper()}-{machine_counter:03d}"
                nom = f"{type_machine['nom']} {config['prefix']}{i+1:02d}"
                
                # Date de mise en service aléatoire (1-5 ans)
                mise_en_service = datetime.now() - timedelta(days=random.randint(365, 1825))
                
                query = """
                INSERT INTO MACHINE (
                    nom, numero_serie, site_id, type_machine_id, 
                    date_mise_en_service, criticite, actif
                ) VALUES (%s, %s, %s, %s, %s, %s, true)
                RETURNING id_machine
                """
                
                result = fetch_one(query, [
                    nom, serial, site['id'], type_machine['id'],
                    mise_en_service.date(), config['criticite']
                ])
                
                self.machines.append({
                    'id': result['id_machine'],
                    'nom': nom,
                    'serial': serial,
                    'site_id': site['id'],
                    'site_nom': site['nom'],
                    'type_id': type_machine['id'],
                    'type_nom': type_machine['nom'],
                    'criticite': config['criticite']
                })
                
                machine_counter += 1
                print(f"  ✓ Machine créée: {nom} ({serial})")
    
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
        for nom, domaine, description in equipes_data:
            query = """
            INSERT INTO EQUIPE (nom, domaine, description, actif)
            VALUES (%s, %s, %s, true)
            RETURNING id_equipe
            """
            result = fetch_one(query, [nom, domaine, description])
            self.equipes.append({
                'id': result['id_equipe'],
                'nom': nom,
                'domaine': domaine
            })
            print(f"  ✓ Équipe créée: {nom} ({domaine})")
    
    def create_techniciens(self):
        """Crée les techniciens"""
        # Noms de techniciens variés
        prenoms = ["Pierre", "Marie", "Jean", "Sophie", "Michel", "Isabelle", "David", "Catherine", 
                  "Philippe", "Nathalie", "Christophe", "Sylvie", "Laurent", "Françoise", "Thierry"]
        noms = ["Martin", "Dubois", "Moreau", "Simon", "Laurent", "Lefebvre", "Garcia", "Roux",
               "Fournier", "Girard", "Bonnet", "Dupont", "Lambert", "Fontaine", "Rousseau"]
        
        print("🔧 Création des techniciens...")
        for equipe in self.equipes:
            # 3-5 techniciens par équipe
            nb_techniciens = random.randint(3, 5)
            
            for i in range(nb_techniciens):
                prenom = random.choice(prenoms)
                nom = random.choice(noms)
                nom_complet = f"{prenom} {nom}"
                
                # Taux horaire selon l'expérience (25-45€/h)
                taux_horaire = round(random.uniform(25, 45), 2)
                
                query = """
                INSERT INTO TECHNICIEN (nom, equipe_id, taux_horaire, actif)
                VALUES (%s, %s, %s, true)
                RETURNING id_technicien
                """
                result = fetch_one(query, [nom_complet, equipe['id'], taux_horaire])
                
                self.techniciens.append({
                    'id': result['id_technicien'],
                    'nom': nom_complet,
                    'equipe_id': equipe['id'],
                    'taux_horaire': taux_horaire
                })
                
                print(f"  ✓ Technicien créé: {nom_complet} ({equipe['nom']}, {taux_horaire}€/h)")
    
    def create_fournisseurs(self):
        """Crée les fournisseurs"""
        fournisseurs_data = [
            ("Pièces Industrielles SAS", "Fournisseur principal de pièces mécaniques"),
            ("Électro Maintenance SARL", "Spécialiste composants électriques"),
            ("Hydraulique Express", "Fournisseur systèmes hydrauliques"),
            ("Roulements & Paliers", "Spécialiste roulements et paliers"),
            ("Automation Services", "Maintenance robotique et automation"),
            ("Compresseurs Pro", "Maintenance compresseurs industriels"),
            ("Énergie Secours", "Maintenance groupes électrogènes")
        ]
        
        print("🏢 Création des fournisseurs...")
        for nom, description in fournisseurs_data:
            query = """
            INSERT INTO FOURNISSEUR (nom, description, actif)
            VALUES (%s, %s, true)
            RETURNING id_fournisseur
            """
            result = fetch_one(query, [nom, description])
            self.fournisseurs.append({
                'id': result['id_fournisseur'],
                'nom': nom
            })
            print(f"  ✓ Fournisseur créé: {nom}")
    
    def create_pieces(self):
        """Crée les pièces de rechange"""
        pieces_categories = {
            "Mécanique": [
                ("Roulement 6308", 45.50, "Roulement à billes standard"),
                ("Joint torique 50x5", 8.20, "Joint d'étanchéité"),
                ("Courroie trapézoïdale A50", 25.80, "Courroie de transmission"),
                ("Palier UCF208", 120.00, "Palier auto-aligneur"),
                ("Vis CHC M12x50", 2.50, "Vis à tête cylindrique hexagonale")
            ],
            "Hydraulique": [
                ("Vérin hydraulique 100/50", 450.00, "Vérin double effet"),
                ("Pompe hydraulique 15L", 890.00, "Pompe à engrenages"),
                ("Filtre hydraulique HF35", 65.00, "Filtre retour"),
                ("Distributeur 4/3", 320.00, "Distributeur hydraulique"),
                ("Flexible HP 1/2", 85.00, "Flexible haute pression")
            ],
            "Électrique": [
                ("Contacteur 25A", 95.00, "Contacteur triphasé"),
                ("Moteur 2.2kW", 680.00, "Moteur asynchrone triphasé"),
                ("Variateur 2.2kW", 420.00, "Variateur de fréquence"),
                ("Capteur inductif M18", 45.00, "Capteur de proximité"),
                ("Relais temporisé", 28.50, "Relais temporisé multifonction")
            ]
        }
        
        print("🔩 Création des pièces...")
        for categorie, pieces in pieces_categories.items():
            for nom, prix, description in pieces:
                # Stock aléatoire
                stock_actuel = random.randint(5, 50)
                stock_mini = max(1, stock_actuel // 4)
                
                query = """
                INSERT INTO PIECE (
                    nom, description, prix_unitaire, stock_actuel, 
                    stock_mini, categorie, actif
                ) VALUES (%s, %s, %s, %s, %s, %s, true)
                RETURNING id_piece
                """
                
                fetch_one(query, [nom, description, prix, stock_actuel, stock_mini, categorie])
                print(f"  ✓ Pièce créée: {nom} ({prix}€, stock: {stock_actuel})")
    
    def create_maintenances(self):
        """Crée les interventions de maintenance sur 12 mois"""
        print("🔧 Création des interventions de maintenance...")
        
        # Types d'intervention avec probabilités
        types_maintenance = [
            ("Preventif", 0.4),  # 40% préventif
            ("Correctif", 0.5),  # 50% correctif
            ("Urgence", 0.1)     # 10% urgence
        ]
        
        # Période de 12 mois
        date_fin = datetime.now().date()
        date_debut = date_fin - timedelta(days=365)
        
        intervention_id = 1
        
        # Génération pour chaque machine
        for machine in self.machines:
            # Nombre d'interventions selon criticité
            nb_interventions_base = {
                "Critique": 8,    # Machines critiques: plus d'interventions
                "Important": 5,   # Machines importantes: interventions moyennes
                "Normal": 3       # Machines normales: peu d'interventions
            }
            
            nb_interventions = nb_interventions_base.get(machine['criticite'], 3)
            nb_interventions += random.randint(-1, 3)  # Variation aléatoire
            
            for i in range(max(1, nb_interventions)):
                # Date d'intervention aléatoire
                jours_depuis_debut = random.randint(0, 365)
                date_intervention = date_debut + timedelta(days=jours_depuis_debut)
                
                # Type d'intervention selon probabilités
                rand = random.random()
                cumul = 0
                type_choisi = "Correctif"
                for type_maintenance, prob in types_maintenance:
                    cumul += prob
                    if rand <= cumul:
                        type_choisi = type_maintenance
                        break
                
                # Équipe selon le type de machine et localisation
                equipe = self._choisir_equipe_pour_machine(machine)
                
                # Durée selon type et criticité
                duree_base = {
                    "Preventif": (2, 6),    # 2-6h pour préventif
                    "Correctif": (3, 12),   # 3-12h pour correctif
                    "Urgence": (1, 8)       # 1-8h pour urgence (plus variable)
                }
                
                duree_min, duree_max = duree_base[type_choisi]
                if machine['criticite'] == "Critique":
                    duree_max += 4  # Machines critiques prennent plus de temps
                
                duree = round(random.uniform(duree_min, duree_max), 1)
                
                # Coût de main d'œuvre (1-3 techniciens)
                nb_techniciens = random.randint(1, 3)
                taux_moyen = 35.0  # Taux horaire moyen
                cout_mod = round(duree * nb_techniciens * taux_moyen, 2)
                
                # Coût des pièces (variable selon type)
                cout_pieces = self._generer_cout_pieces(type_choisi, machine['criticite'])
                
                # Coût frais externes (occasionnel)
                cout_frais_externes = 0
                if random.random() < 0.15:  # 15% de chance
                    cout_frais_externes = round(random.uniform(100, 800), 2)
                
                cout_total = cout_mod + cout_pieces + cout_frais_externes
                
                # Description
                descriptions = {
                    "Preventif": [
                        "Maintenance préventive programmée",
                        "Révision générale préventive",
                        "Contrôle et entretien préventif",
                        "Maintenance systématique"
                    ],
                    "Correctif": [
                        "Réparation suite à dysfonctionnement",
                        "Remplacement pièce défaillante",
                        "Correction anomalie détectée",
                        "Remise en état de fonctionnement"
                    ],
                    "Urgence": [
                        "Intervention d'urgence - arrêt production",
                        "Réparation urgente - panne critique",
                        "Dépannage urgent - sécurité",
                        "Intervention d'urgence - dysfonctionnement majeur"
                    ]
                }
                
                description = random.choice(descriptions[type_choisi])
                
                # Insérer l'intervention
                query = """
                INSERT INTO MAINTENANCE (
                    machine_id, equipe_id, type_reel, description,
                    date_debut, date_fin_prevue, date_fin_reelle,
                    duree_intervention_h, cout_main_oeuvre, cout_pieces_internes,
                    cout_pieces_externes, cout_autres_frais, cout_total,
                    statut
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id_maintenance
                """
                
                date_fin_intervention = date_intervention + timedelta(hours=int(duree))
                
                result = fetch_one(query, [
                    machine['id'], equipe['id'], type_choisi, description,
                    date_intervention, date_fin_intervention, date_fin_intervention,
                    duree, cout_mod, cout_pieces, 0, cout_frais_externes, cout_total,
                    "Terminé"
                ])
                
                if intervention_id % 20 == 0:
                    print(f"  ✓ {intervention_id} interventions créées...")
                
                intervention_id += 1
        
        print(f"  ✅ {intervention_id-1} interventions créées au total")
    
    def _choisir_equipe_pour_machine(self, machine):
        """Choisit l'équipe appropriée pour une machine"""
        # Logique simple de répartition géographique/technique
        if "Nord" in machine['site_nom']:
            equipes_site = [e for e in self.equipes if "Nord" in e['nom']]
        elif "Sud" in machine['site_nom']:
            equipes_site = [e for e in self.equipes if "Sud" in e['nom']]
        elif "Est" in machine['site_nom']:
            equipes_site = [e for e in self.equipes if "Est" in e['nom']]
        elif "R&D" in machine['site_nom']:
            equipes_site = [e for e in self.equipes if "R&D" in e['nom']]
        else:
            equipes_site = [e for e in self.equipes if "Utilités" in e['nom']]
        
        if not equipes_site:
            equipes_site = self.equipes
        
        return random.choice(equipes_site)
    
    def _generer_cout_pieces(self, type_maintenance, criticite):
        """Génère un coût de pièces réaliste"""
        # Coûts de base selon le type
        couts_base = {
            "Preventif": (50, 200),    # Préventif: consommables
            "Correctif": (100, 600),   # Correctif: pièces moyennes
            "Urgence": (150, 1200)     # Urgence: pièces coûteuses possibles
        }
        
        cout_min, cout_max = couts_base[type_maintenance]
        
        # Ajustement selon criticité
        if criticite == "Critique":
            cout_max *= 1.5
        elif criticite == "Normal":
            cout_max *= 0.7
        
        # 30% de chance de pas de pièces (maintenance simple)
        if random.random() < 0.3:
            return 0
        
        return round(random.uniform(cout_min, cout_max), 2)
    
    def print_summary(self):
        """Affiche un résumé des données créées"""
        print("\n📊 RÉSUMÉ DES DONNÉES GÉNÉRÉES:")
        print(f"  • Sites: {len(self.sites)}")
        print(f"  • Types de machines: {len(self.types_machines)}")
        print(f"  • Machines: {len(self.machines)}")
        print(f"  • Équipes: {len(self.equipes)}")
        print(f"  • Techniciens: {len(self.techniciens)}")
        print(f"  • Fournisseurs: {len(self.fournisseurs)}")
        
        # Compter les interventions
        nb_interventions = fetch_one("SELECT COUNT(*) as total FROM MAINTENANCE")
        print(f"  • Interventions: {nb_interventions['total']}")
        
        # Répartition par type
        repartition = fetch_all("""
        SELECT type_reel, COUNT(*) as nb, 
               ROUND(AVG(cout_total), 2) as cout_moyen
        FROM MAINTENANCE 
        GROUP BY type_reel 
        ORDER BY type_reel
        """)
        
        print("\n📈 RÉPARTITION DES INTERVENTIONS:")
        for row in repartition:
            print(f"  • {row['type_reel']}: {row['nb']} interventions (coût moyen: {row['cout_moyen']}€)")


def main():
    """Fonction principale"""
    print("🎯 Générateur de données de test GMAO")
    print("=" * 50)
    
    # Vérifier la connexion à la base
    try:
        result = fetch_one("SELECT version()")
        print(f"✅ Connexion DB OK: {result['version'][:50]}...")
    except Exception as e:
        print(f"❌ Erreur connexion DB: {e}")
        return
    
    # Demander confirmation
    response = input("\n⚠️  Voulez-vous générer les données de test ? (oui/non): ")
    if response.lower() not in ['oui', 'o', 'yes', 'y']:
        print("Génération annulée.")
        return
    
    # Générer les données
    generator = TestDataGenerator()
    generator.generate_all_test_data()
    
    print("\n✅ Données de test générées avec succès!")
    print("Vous pouvez maintenant tester les KPI avec des données cohérentes.")


if __name__ == "__main__":
    main()
