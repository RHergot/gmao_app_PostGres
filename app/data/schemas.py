# gmao_app/app/data/schemas.py
"""
Contient les requêtes SQL pour définir le schéma de la base de données.
"""
from typing import Dict

# Clé: Nom de la table/objet, Valeur: Requête SQL CREATE
TABLES: Dict[str, str] = {

    # --- Tables de référence (créées en premier) ---
    "SITE": """
        CREATE TABLE IF NOT EXISTS SITE (
            id_site SERIAL PRIMARY KEY,
            nom TEXT NOT NULL UNIQUE,
            adresse TEXT,
            ville TEXT,
            pays TEXT,
            contact_principal TEXT
            -- created_at, updated_at ? Optionnel pour ces références simples
        );
    """,
    "FABRICANT": """
        CREATE TABLE IF NOT EXISTS FABRICANT (
            id_fabricant SERIAL PRIMARY KEY,
            nom TEXT NOT NULL UNIQUE,
            contact TEXT,
            site_web TEXT,
            support_technique TEXT
            -- created_at, updated_at ? Optionnel
        );
    """,
    "TYPE_MACHINE": """
        CREATE TABLE IF NOT EXISTS TYPE_MACHINE (
            id_type_machine SERIAL PRIMARY KEY,
            nom TEXT NOT NULL UNIQUE,
            description TEXT,
            categorie TEXT
            -- created_at, updated_at ? Optionnel
        );
    """,
    "TECHNICIEN": """
        CREATE TABLE IF NOT EXISTS TECHNICIEN (
            id_technicien SERIAL PRIMARY KEY,
            nom TEXT NOT NULL,
            prenom TEXT,
            qualification TEXT,
            contact TEXT,
            cout_horaire DOUBLE PRECISION DEFAULT 0.0,
            equipe_id INTEGER, -- Nullable
            actif INTEGER DEFAULT 1
            -- Ajouter contrainte UNIQUE(nom, prenom) ?
        );
    """,
    "EQUIPE": """
        CREATE TABLE IF NOT EXISTS EQUIPE (
            id_equipe SERIAL PRIMARY KEY,
            nom TEXT NOT NULL UNIQUE,
            domaine_expertise TEXT,
            responsable_id INTEGER -- FK vers TECHNICIEN
        );
    """,

    # --- Table Utilisateur ---
    "UTILISATEUR": """
        CREATE TABLE IF NOT EXISTS UTILISATEUR (
            id_utilisateur SERIAL PRIMARY KEY,
            login TEXT UNIQUE NOT NULL,
            mot_de_passe_hash TEXT NOT NULL,
            nom_complet TEXT,
            role TEXT NOT NULL, -- CHECK constraint recommandée
            email TEXT UNIQUE,
            actif INTEGER DEFAULT 1,
            derniere_connexion TEXT, -- ISO timestamp string
            technicien_id INTEGER, -- Nullable
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(technicien_id) REFERENCES TECHNICIEN(id_technicien) ON DELETE SET NULL
        );
    """,

    # --- Table Machine ---
    "MACHINE": """
        CREATE TABLE IF NOT EXISTS MACHINE (
            id_machine SERIAL PRIMARY KEY,
            nom TEXT NOT NULL,
            serial TEXT UNIQUE, -- Nullable?
            modele TEXT,
            date_installation TEXT, -- ISO Date YYYY-MM-DD
            localisation TEXT,
            etat TEXT DEFAULT 'Inconnu', 
            informations_techniques TEXT,
            type_machine_id INTEGER NOT NULL,
            site_id INTEGER NOT NULL,
            fabricant_id INTEGER NOT NULL,
            parent_machine_id INTEGER, -- Nullable
            criticite TEXT,  -- ex: A, B, C
            garantie_fin TEXT, -- ISO Date YYYY-MM-DD
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (type_machine_id) REFERENCES TYPE_MACHINE(id_type_machine) ON DELETE RESTRICT,
            FOREIGN KEY (site_id) REFERENCES SITE(id_site) ON DELETE RESTRICT,
            FOREIGN KEY (fabricant_id) REFERENCES FABRICANT(id_fabricant) ON DELETE RESTRICT,
            FOREIGN KEY (parent_machine_id) REFERENCES MACHINE(id_machine) ON DELETE SET NULL
        );
    """,

    # --- Table Fournisseur ---
    "FOURNISSEUR": """
        CREATE TABLE IF NOT EXISTS FOURNISSEUR (
            id_fournisseur SERIAL PRIMARY KEY,
            nom TEXT NOT NULL UNIQUE,
            contact TEXT,
            adresse TEXT,
            telephone TEXT,
            email TEXT,
            delai_livraison_moyen_j INTEGER,
            devise TEXT DEFAULT 'EUR', 
            note_qualite DOUBLE PRECISION, -- Note sur 5? Nullable
            updated_at TEXT -- Ajout pour le trigger
        );
    """,

    # --- Table Piece ---
    "PIECE": """
        CREATE TABLE IF NOT EXISTS PIECE (
            id_piece SERIAL PRIMARY KEY,
            reference TEXT NOT NULL UNIQUE,
            nom TEXT NOT NULL,
            fournisseur_pref_id INTEGER, -- Nullable
            prix_unitaire DOUBLE PRECISION DEFAULT 0.0 CHECK(prix_unitaire >= 0),
            stock_alerte INTEGER DEFAULT 0 CHECK(stock_alerte >= 0),
            stock_actuel INTEGER DEFAULT 0 CHECK(stock_actuel >= 0),
            stock_reserve INTEGER DEFAULT 0 CHECK(stock_reserve >= 0),
            unite TEXT NOT NULL, 
            categorie TEXT,
            emplacement_stockage TEXT,
            statut TEXT DEFAULT 'Actif', 
            updated_at TEXT, -- Ajout pour trigger et suivi modif stock/prix
            FOREIGN KEY (fournisseur_pref_id) REFERENCES FOURNISSEUR(id_fournisseur) ON DELETE SET NULL
            -- CONSTRAINT check_stock CHECK (stock_actuel >= stock_reserve) -- Possible? Vérifie stock >= réservé
        );
    """,

    # --- Tables Maintenance ---
    "ORDRE_TRAVAIL": """
        CREATE TABLE IF NOT EXISTS ORDRE_TRAVAIL (
            id_ot SERIAL PRIMARY KEY,
            numero_ot TEXT UNIQUE,
            machine_id INTEGER NOT NULL,
            gamme_id INTEGER, -- Sera lié à GAMME_ENTRETIEN plus tard
            type TEXT NOT NULL, 
            description TEXT NOT NULL,
            date_creation TEXT DEFAULT CURRENT_TIMESTAMP,
            date_prevue TEXT, -- ISO Timestamp string
            duree_prevue_min INTEGER,
            priorite TEXT, 
            urgence INTEGER DEFAULT 0,
            statut TEXT NOT NULL, 
            technicien_assigne_id INTEGER,
            utilisateur_createur_id INTEGER NOT NULL,
            notes_planification TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (machine_id) REFERENCES MACHINE(id_machine) ON DELETE CASCADE,
            -- FOREIGN KEY (gamme_id) REFERENCES GAMME_ENTRETIEN(id_gamme) ON DELETE SET NULL, -- Futur
            FOREIGN KEY (technicien_assigne_id) REFERENCES TECHNICIEN(id_technicien) ON DELETE SET NULL,
            FOREIGN KEY (utilisateur_createur_id) REFERENCES UTILISATEUR(id_utilisateur) ON DELETE RESTRICT
        );
    """,
    "MAINTENANCE": """
        CREATE TABLE IF NOT EXISTS MAINTENANCE (
            id_maintenance SERIAL PRIMARY KEY,
            ot_id INTEGER NOT NULL UNIQUE,
            machine_id INTEGER, -- FK MACHINE (Optionnel)
            technicien_id INTEGER NOT NULL,
            date_debut_reelle TEXT NOT NULL, -- ISO Timestamp string
            date_fin_reelle TEXT NOT NULL, -- ISO Timestamp string
            duree_intervention_h DOUBLE PRECISION,
            type_reel TEXT NOT NULL, 
            description_travaux TEXT NOT NULL,
            resultat TEXT NOT NULL, 
            cout_manuel_v1 DOUBLE PRECISION,
            -- Nouveaux champs financiers (Phase 11)
            cout_main_oeuvre DOUBLE PRECISION DEFAULT 0.0,
            cout_pieces_internes DOUBLE PRECISION DEFAULT 0.0,
            cout_pieces_externes DOUBLE PRECISION DEFAULT 0.0,
            cout_autres_frais DOUBLE PRECISION DEFAULT 0.0,
            cout_total DOUBLE PRECISION DEFAULT 0.0,
            evaluation_qualite INTEGER,
            impact_production TEXT, 
            notes_technicien TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (ot_id) REFERENCES ORDRE_TRAVAIL(id_ot) ON DELETE CASCADE,
            FOREIGN KEY (machine_id) REFERENCES MACHINE(id_machine) ON DELETE SET NULL,
            FOREIGN KEY (technicien_id) REFERENCES TECHNICIEN(id_technicien) ON DELETE RESTRICT
        );
    """,
    "INTERVENTION_PIECE": """
        CREATE TABLE IF NOT EXISTS INTERVENTION_PIECE (
            id SERIAL PRIMARY KEY,
            maintenance_id INTEGER NOT NULL,
            piece_id INTEGER NOT NULL,
            quantite INTEGER NOT NULL CHECK(quantite > 0),
            lot TEXT,
            FOREIGN KEY (maintenance_id) REFERENCES MAINTENANCE(id_maintenance) ON DELETE CASCADE,
            FOREIGN KEY (piece_id) REFERENCES PIECE(id_piece) ON DELETE RESTRICT
        );
    """,
    # --- Table Mouvement Stock ---
    "MOUVEMENT_STOCK": """
        CREATE TABLE IF NOT EXISTS MOUVEMENT_STOCK (
            id SERIAL PRIMARY KEY,
            piece_id INTEGER NOT NULL,
            type_mouvement_id INTEGER NOT NULL,
            quantite INTEGER NOT NULL, -- Peut être négatif pour les sorties/ajustements
            emplacement_source_id INTEGER,
            emplacement_destination_id INTEGER,
            utilisateur_id INTEGER,
            date_mouvement TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            reference_document TEXT,
            commentaire TEXT,
            cout_unitaire DECIMAL(10,2),
            cout_total DECIMAL(10,2),
            stock_avant INTEGER,
            stock_apres INTEGER,
            valide BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            statut_mouvement TEXT DEFAULT 'CONFIRME',
            FOREIGN KEY (piece_id) REFERENCES PIECE(id_piece) ON DELETE RESTRICT,
            FOREIGN KEY (utilisateur_id) REFERENCES UTILISATEUR(id_utilisateur) ON DELETE SET NULL
        );
    """,

    # --- Tables Gammes (Phase 6) ---
    "GAMME_PIECE_TYPE": '''
        CREATE TABLE IF NOT EXISTS GAMME_PIECE_TYPE (
            id SERIAL PRIMARY KEY,
            gamme_id INTEGER NOT NULL,
            piece_id INTEGER NOT NULL,
            quantite_theorique INTEGER NOT NULL CHECK(quantite_theorique > 0),
            FOREIGN KEY (gamme_id) REFERENCES GAMME_ENTRETIEN(id_gamme) ON DELETE CASCADE,
            FOREIGN KEY (piece_id) REFERENCES PIECE(id_piece) ON DELETE RESTRICT
        );
    ''',
    "GAMME_ENTRETIEN": """
        CREATE TABLE IF NOT EXISTS GAMME_ENTRETIEN (
            id_gamme SERIAL PRIMARY KEY,
            description TEXT NOT NULL UNIQUE, -- Nom/Code de la gamme
            type_entretien TEXT, 
            periodicite_valeur INTEGER,
            periodicite_unite TEXT,  -- Jours, Semaines, Mois, Heures...
            instructions TEXT,
            date_derniere_realisation TEXT, -- ISO Date YYYY-MM-DD
            prochaine_date_calculee TEXT, -- ISO Date YYYY-MM-DD (non normé, mais pratique)
            active INTEGER DEFAULT 1,
            type_machine_id INTEGER, -- Peut être lié à un type de machine
            createur_id INTEGER, -- FK Utilisateur
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
            duree_estimee_min INTEGER, -- Durée totale estimée gamme
            qualification_requise TEXT, -- Compétence nécessaire
            priorite TEXT, -- Priorité par défaut pour OT générés? CHECK recommandée
            FOREIGN KEY (type_machine_id) REFERENCES TYPE_MACHINE(id_type_machine) ON DELETE SET NULL,
            FOREIGN KEY (createur_id) REFERENCES UTILISATEUR(id_utilisateur) ON DELETE SET NULL
        );
    """,
    "GAMME_ETAPE": """
        CREATE TABLE IF NOT EXISTS GAMME_ETAPE (
            id_etape SERIAL PRIMARY KEY,
            gamme_id INTEGER NOT NULL,
            description TEXT NOT NULL,
            ordre INTEGER NOT NULL, -- Ordre d'exécution de l'étape
            instructions_detaillees TEXT,
            duree_estimee_min INTEGER,
            FOREIGN KEY (gamme_id) REFERENCES GAMME_ENTRETIEN(id_gamme) ON DELETE CASCADE -- Si gamme supprimée, supprime étapes
            -- UNIQUE (gamme_id, ordre) -- Assurer ordre unique par gamme
        );
    """,
    "GAMME_PIECE_TYPE": """
        CREATE TABLE IF NOT EXISTS GAMME_PIECE_TYPE (
            id SERIAL PRIMARY KEY,
            gamme_id INTEGER NOT NULL,
            piece_id INTEGER NOT NULL,
            quantite_theorique INTEGER DEFAULT 1 CHECK(quantite_theorique >= 0),
            FOREIGN KEY (gamme_id) REFERENCES GAMME_ENTRETIEN(id_gamme) ON DELETE CASCADE,
            FOREIGN KEY (piece_id) REFERENCES PIECE(id_piece) ON DELETE CASCADE, -- Si pièce supprimée, retirer des gammes? CASCADE ou RESTRICT? Discutable. CASCADE ici.
            UNIQUE (gamme_id, piece_id) -- Ne pas lister deux fois la même pièce pour une gamme
        );
    """,


     # --- NOUVELLES TABLES (Phase 7: Achats) ---
    "COMMANDE": """
        CREATE TABLE IF NOT EXISTS COMMANDE (
            id_commande SERIAL PRIMARY KEY,
            numero_commande TEXT UNIQUE, -- Numéro unique interne ou fournisseur
            fournisseur_id INTEGER NOT NULL,
            createur_id INTEGER NOT NULL, -- Utilisateur qui a créé la commande
            date_commande TEXT NOT NULL, -- ISO Date YYYY-MM-DD
            date_livraison_prevue TEXT, -- ISO Date YYYY-MM-DD
            date_livraison_reelle TEXT, -- ISO Date YYYY-MM-DD (Dernière livraison?)
            statut TEXT NOT NULL CHECK(statut IN ('Brouillon', 'Validee', 'Envoyee', 'Partielle', 'Livree', 'Annulee')) DEFAULT 'Brouillon',
            total_ht DOUBLE PRECISION DEFAULT 0.0, -- Calculé ou saisi? Mieux si calculé par trigger/service?
            frais_port DOUBLE PRECISION DEFAULT 0.0,
            -- total_ttc DOUBLE PRECISION, -- Si besoin TVA
            reference_fournisseur TEXT, -- Réf commande chez le fournisseur
            mode_paiement TEXT,
            notes_commande TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (fournisseur_id) REFERENCES FOURNISSEUR(id_fournisseur) ON DELETE RESTRICT,
            FOREIGN KEY (createur_id) REFERENCES UTILISATEUR(id_utilisateur) ON DELETE RESTRICT
        );
    """,
    "LIGNE_COMMANDE": """
        CREATE TABLE IF NOT EXISTS LIGNE_COMMANDE (
            id_ligne SERIAL PRIMARY KEY,
            commande_id INTEGER NOT NULL,
            piece_id INTEGER NOT NULL,
            description_libre TEXT, -- Si pièce non cataloguée
            quantite_commandee INTEGER NOT NULL CHECK(quantite_commandee > 0),
            prix_unitaire_ht DOUBLE PRECISION NOT NULL CHECK(prix_unitaire_ht >= 0),
            quantite_recue INTEGER DEFAULT 0 CHECK(quantite_recue >= 0),
            date_reception TEXT, -- ISO Date YYYY-MM-DD (Dernière réception pour cette ligne)
            statut_ligne TEXT NOT NULL CHECK(statut_ligne IN ('Attente', 'Partielle', 'Recue')) DEFAULT 'Attente',
            FOREIGN KEY (commande_id) REFERENCES COMMANDE(id_commande) ON DELETE CASCADE, -- Si on supprime la commande, on supprime les lignes
            FOREIGN KEY (piece_id) REFERENCES PIECE(id_piece) ON DELETE RESTRICT -- On ne peut pas supprimer une pièce si elle est dans une ligne de commande
            -- UNIQUE (commande_id, piece_id) -- Pour éviter d'avoir deux fois la même pièce sur une commande? Discutable.
        );
    """,

    "COMPTEUR": """
        CREATE TABLE IF NOT EXISTS COMPTEUR (
            id_compteur SERIAL PRIMARY KEY,
            machine_id INTEGER NOT NULL,
            nom TEXT NOT NULL,
            unite TEXT NOT NULL,
            valeur_actuelle DOUBLE PRECISION DEFAULT 0.0,
            date_dernier_releve TEXT, -- ISO Date YYYY-MM-DD
            seuil_alerte DOUBLE PRECISION, -- Nullable
            seuil_prev_ot DOUBLE PRECISION, -- Nullable
            -- actif INTEGER DEFAULT 1, -- Optionnel si vous l'ajoutez au modèle/DB
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (machine_id) REFERENCES MACHINE(id_machine) ON DELETE CASCADE, -- Supprimer compteurs si machine supprimée
            UNIQUE (machine_id, nom) -- Une machine ne peut avoir qu'un seul compteur du même nom/type
        );
    """,
    "HISTORIQUE_COMPTEUR": """
        CREATE TABLE IF NOT EXISTS HISTORIQUE_COMPTEUR (
            id_historique SERIAL PRIMARY KEY,
            compteur_id INTEGER NOT NULL,
            date_releve TEXT DEFAULT CURRENT_TIMESTAMP, -- ISO Timestamp YYYY-MM-DD HH:MM:SS.sss
            valeur DOUBLE PRECISION NOT NULL,
            utilisateur_id INTEGER, -- Nullable: qui a fait le relevé manuel?
            maintenance_id INTEGER, -- Nullable: si relevé fait pendant maintenance (lien facultatif)
            FOREIGN KEY (compteur_id) REFERENCES COMPTEUR(id_compteur) ON DELETE CASCADE, -- Supprimer historiques si compteur supprimé
            FOREIGN KEY (utilisateur_id) REFERENCES UTILISATEUR(id_utilisateur) ON DELETE SET NULL,
            FOREIGN KEY (maintenance_id) REFERENCES MAINTENANCE(id_maintenance) ON DELETE SET NULL
        );
    """,

    # --- NOUVELLES TABLES (Phase 11: Gestion Financière) ---
    "MAINTENANCE_INTERVENANT": """
        CREATE TABLE IF NOT EXISTS MAINTENANCE_INTERVENANT (
            id_intervenant SERIAL PRIMARY KEY,
            maintenance_id INTEGER NOT NULL,
            technicien_id INTEGER, -- NULL si intervenant externe
            nom_intervenant_externe TEXT, -- NULL si technicien_id n'est pas NULL
            heures_travaillees DOUBLE PRECISION NOT NULL CHECK(heures_travaillees > 0),
            cout_horaire DOUBLE PRECISION NOT NULL CHECK(cout_horaire >= 0),
            notes TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (maintenance_id) REFERENCES MAINTENANCE(id_maintenance) ON DELETE CASCADE,
            FOREIGN KEY (technicien_id) REFERENCES TECHNICIEN(id_technicien) ON DELETE RESTRICT,
            -- Soit technicien_id soit nom_intervenant_externe doit être non NULL
            CHECK ((technicien_id IS NOT NULL) OR (nom_intervenant_externe IS NOT NULL))
        );
    """,
    "MAINTENANCE_FRAIS_EXTERNE": """
        CREATE TABLE IF NOT EXISTS MAINTENANCE_FRAIS_EXTERNE (
            id_frais SERIAL PRIMARY KEY,
            maintenance_id INTEGER NOT NULL,
            type_frais TEXT NOT NULL CHECK(type_frais IN ('PIECE_EXTERNE', 'DEPLACEMENT', 'SOUS_TRAITANCE', 'AUTRE')),
            description TEXT NOT NULL,
            montant DOUBLE PRECISION NOT NULL CHECK(montant >= 0),
            quantite INTEGER DEFAULT 1 CHECK(quantite > 0),
            reference_piece TEXT, -- Pour les pièces externes
            fournisseur TEXT, -- Pour les pièces/services externes
            facture_reference TEXT, -- Pour référence comptable
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (maintenance_id) REFERENCES MAINTENANCE(id_maintenance) ON DELETE CASCADE
        );
    """,

    # --- Index pour Phase 6 ---
    "IDX_GAMME_TYPE_MACHINE": """
        CREATE INDEX IF NOT EXISTS idx_gamme_type_machine ON GAMME_ENTRETIEN(type_machine_id);
    """,
    "IDX_GAMME_ETAPE_GAMME": """
        CREATE INDEX IF NOT EXISTS idx_gamme_etape_gamme ON GAMME_ETAPE(gamme_id);
    """,
    "IDX_GAMME_PIECE_GAMME": """
        CREATE INDEX IF NOT EXISTS idx_gamme_piece_gamme ON GAMME_PIECE_TYPE(gamme_id);
    """,
    "IDX_GAMME_PIECE_PIECE": """
        CREATE INDEX IF NOT EXISTS idx_gamme_piece_piece ON GAMME_PIECE_TYPE(piece_id);
    """,

    # --- Index généraux déjà définis ---
    "IDX_INTERVENTION_PIECE_MAINT": """
        CREATE INDEX IF NOT EXISTS idx_intervention_piece_maint ON INTERVENTION_PIECE(maintenance_id);
    """,
    "IDX_INTERVENTION_PIECE_PIECE": """
        CREATE INDEX IF NOT EXISTS idx_intervention_piece_piece ON INTERVENTION_PIECE(piece_id);
    """,

    # --- NOUVEAUX INDEX (Phase 8) ---
    "IDX_COMPTEUR_MACHINE": """
        CREATE INDEX IF NOT EXISTS idx_compteur_machine ON COMPTEUR(machine_id);
    """,
    "IDX_HISTORIQUE_COMPTEUR": """
        CREATE INDEX IF NOT EXISTS idx_historique_compteur ON HISTORIQUE_COMPTEUR(compteur_id);
    """,
    "IDX_HISTORIQUE_UTILISATEUR": """
        CREATE INDEX IF NOT EXISTS idx_historique_utilisateur ON HISTORIQUE_COMPTEUR(utilisateur_id);
    """,
    "IDX_HISTORIQUE_MAINTENANCE": """
        CREATE INDEX IF NOT EXISTS idx_historique_maintenance ON HISTORIQUE_COMPTEUR(maintenance_id);
    """,
    "IDX_MAINTENANCE_INTERVENANT_MAINT": """
        CREATE INDEX IF NOT EXISTS idx_maintenance_intervenant_maint ON MAINTENANCE_INTERVENANT(maintenance_id);
    """,
    "IDX_MAINTENANCE_INTERVENANT_TECH": """
        CREATE INDEX IF NOT EXISTS idx_maintenance_intervenant_tech ON MAINTENANCE_INTERVENANT(technicien_id);
    """,
    "IDX_MAINTENANCE_FRAIS_MAINT": """
        CREATE INDEX IF NOT EXISTS idx_maintenance_frais_maint ON MAINTENANCE_FRAIS_EXTERNE(maintenance_id);
    """,
    "IDX_MAINTENANCE_FRAIS_TYPE": """
        CREATE INDEX IF NOT EXISTS idx_maintenance_frais_type ON MAINTENANCE_FRAIS_EXTERNE(type_frais);
    """,
}

# Requêtes ALTER TABLE pour ajouter les clés étrangères après la création des tables (évite les dépendances circulaires)
ALTER_TABLES = [
    "ALTER TABLE TECHNICIEN ADD CONSTRAINT fk_technicien_equipe FOREIGN KEY (equipe_id) REFERENCES EQUIPE(id_equipe) ON DELETE SET NULL;",
    "ALTER TABLE EQUIPE ADD CONSTRAINT fk_equipe_responsable FOREIGN KEY (responsable_id) REFERENCES TECHNICIEN(id_technicien) ON DELETE SET NULL;"
]

# --- Triggers ---
TRIGGERS: Dict[str, str] = {
    "UTILISATEUR_update_trigger": """
        CREATE OR REPLACE FUNCTION utilisateur_updated_at()
        RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER utilisateur_updated_at
AFTER UPDATE ON UTILISATEUR
FOR EACH ROW EXECUTE FUNCTION utilisateur_updated_at();
    """,
    "MACHINE_update_trigger": """
        CREATE OR REPLACE FUNCTION machine_updated_at()
        RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER machine_updated_at
AFTER UPDATE ON MACHINE
FOR EACH ROW EXECUTE FUNCTION machine_updated_at();
    """,
    "ORDRE_TRAVAIL_update_trigger": """
        CREATE OR REPLACE FUNCTION ot_updated_at()
        RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER ot_updated_at
AFTER UPDATE ON ORDRE_TRAVAIL
FOR EACH ROW EXECUTE FUNCTION ot_updated_at();
    """,
    "FOURNISSEUR_update_trigger": """
        CREATE OR REPLACE FUNCTION fournisseur_updated_at()
        RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER fournisseur_updated_at
AFTER UPDATE ON FOURNISSEUR
FOR EACH ROW EXECUTE FUNCTION fournisseur_updated_at();
    """, # Assure-toi que la colonne updated_at est bien dans la table FOURNISSEUR
    "PIECE_update_trigger": """
        CREATE OR REPLACE FUNCTION piece_updated_at()
        RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER piece_updated_at
AFTER UPDATE ON PIECE
FOR EACH ROW EXECUTE FUNCTION piece_updated_at();
    """,
    # Trigger pour GAMME_ENTRETIEN
    "GAMME_ENTRETIEN_update_trigger": """
        CREATE OR REPLACE FUNCTION gamme_entretien_updated_at()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = CURRENT_TIMESTAMP;
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
        
        CREATE TRIGGER gamme_entretien_updated_at
        AFTER UPDATE ON GAMME_ENTRETIEN
        FOR EACH ROW EXECUTE FUNCTION gamme_entretien_updated_at();
    """,


     # --- NOUVEAU TRIGGER (Phase 7) ---
    "COMMANDE_update_trigger": """
        CREATE OR REPLACE FUNCTION commande_updated_at()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = CURRENT_TIMESTAMP;
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
        
        CREATE TRIGGER commande_updated_at
        AFTER UPDATE ON COMMANDE
        FOR EACH ROW EXECUTE FUNCTION commande_updated_at();
    """,
    # Pas de trigger pour MOUVEMENT_STOCK, GAMME_ETAPE, GAMME_PIECE_TYPE a priori

     # --- NOUVEAUX TRIGGERS (Phase 8) ---
     "COMPTEUR_update_trigger": """
        CREATE OR REPLACE FUNCTION compteur_updated_at()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = CURRENT_TIMESTAMP;
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
        
        CREATE TRIGGER compteur_updated_at
        AFTER UPDATE ON COMPTEUR
        FOR EACH ROW EXECUTE FUNCTION compteur_updated_at();
    """,
    # Pas de trigger pour HISTORIQUE_COMPTEUR, c'est un log de faits passés.

    # --- NOUVEAUX TRIGGERS (Phase 11) ---
    # Pas de triggers nécessaires pour les tables MAINTENANCE_INTERVENANT et MAINTENANCE_FRAIS_EXTERNE car elles ne sont modifiées que lors de leur création
}