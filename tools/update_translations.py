#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script pour mettre à jour et compiler les fichiers de traduction.
Utilise pyside6-lupdate pour extraire les chaînes à traduire et pyside6-lrelease pour compiler les traductions.
"""
import os
import subprocess
import argparse
import logging
from pathlib import Path

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("update_translations")

def get_ts_files(translations_dir):
    """Récupère tous les fichiers .ts dans le répertoire des traductions."""
    ts_files = list(Path(translations_dir).glob("*.ts"))
    return ts_files

def extract_translations(source_dirs, translations_dir, specific_files=None):
    """
    Extrait les chaînes à traduire des fichiers source.
    
    Args:
        source_dirs (list): Liste des répertoires contenant les fichiers source
        translations_dir (str): Répertoire où stocker les fichiers de traduction
        specific_files (list, optional): Liste spécifique de fichiers .ts à mettre à jour
    """
    # Créer le répertoire de traductions s'il n'existe pas
    os.makedirs(translations_dir, exist_ok=True)
    
    # Si des fichiers spécifiques sont fournis, les mettre à jour
    if specific_files:
        for ts_file in specific_files:
            ts_path = os.path.join(translations_dir, f"{ts_file}.ts")
            if not os.path.exists(ts_path):
                logger.warning(f"Le fichier {ts_path} n'existe pas, il sera créé.")
            
            cmd = ["pyside6-lupdate"]
            for src_dir in source_dirs:
                cmd.append(src_dir)
            cmd.extend(["-ts", ts_path])
            
            logger.info(f"Extraction des chaînes pour {ts_file}.ts...")
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                logger.error(f"Erreur lors de l'extraction pour {ts_file}.ts: {result.stderr}")
            else:
                logger.info(f"Extraction réussie pour {ts_file}.ts")
    else:
        # Mettre à jour tous les fichiers .ts existants
        ts_files = get_ts_files(translations_dir)
        
        # S'il n'y a pas de fichiers .ts, créer au moins fr.ts et en.ts
        if not ts_files:
            logger.info("Aucun fichier .ts trouvé, création des fichiers fr.ts et en.ts")
            ts_files = [
                Path(translations_dir) / "fr.ts",
                Path(translations_dir) / "en.ts"
            ]
        
        for ts_file in ts_files:
            cmd = ["pyside6-lupdate"]
            for src_dir in source_dirs:
                cmd.append(src_dir)
            cmd.extend(["-ts", str(ts_file)])
            
            logger.info(f"Extraction des chaînes pour {ts_file.name}...")
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                logger.error(f"Erreur lors de l'extraction pour {ts_file.name}: {result.stderr}")
            else:
                logger.info(f"Extraction réussie pour {ts_file.name}")

def compile_translations(translations_dir, specific_files=None):
    """
    Compile les fichiers de traduction .ts en fichiers .qm.
    
    Args:
        translations_dir (str): Répertoire contenant les fichiers de traduction
        specific_files (list, optional): Liste spécifique de fichiers .ts à compiler
    """
    if specific_files:
        for ts_file in specific_files:
            ts_path = os.path.join(translations_dir, f"{ts_file}.ts")
            if not os.path.exists(ts_path):
                logger.warning(f"Le fichier {ts_path} n'existe pas, impossible de compiler.")
                continue
            
            cmd = ["pyside6-lrelease", ts_path]
            logger.info(f"Compilation de {ts_file}.ts...")
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                logger.error(f"Erreur lors de la compilation de {ts_file}.ts: {result.stderr}")
            else:
                logger.info(f"Compilation réussie pour {ts_file}.ts")
    else:
        # Compiler tous les fichiers .ts
        ts_files = get_ts_files(translations_dir)
        if not ts_files:
            logger.warning(f"Aucun fichier .ts trouvé dans {translations_dir}")
            return
        
        cmd = ["pyside6-lrelease"]
        cmd.extend([str(f) for f in ts_files])
        
        logger.info(f"Compilation de tous les fichiers .ts...")
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            logger.error(f"Erreur lors de la compilation: {result.stderr}")
        else:
            logger.info(f"Compilation réussie pour tous les fichiers")

def main():
    parser = argparse.ArgumentParser(description="Met à jour et compile les fichiers de traduction")
    parser.add_argument("--extract", action="store_true", help="Extraire les chaînes à traduire")
    parser.add_argument("--compile", action="store_true", help="Compiler les traductions")
    parser.add_argument("--all", action="store_true", help="Extraire et compiler")
    parser.add_argument("--source", nargs="+", default=["app", "main.py"], help="Répertoires/fichiers source")
    parser.add_argument("--translations", default="translations", help="Répertoire des traductions")
    parser.add_argument("--files", nargs="+", help="Fichiers spécifiques à traiter (sans extension .ts)")
    
    args = parser.parse_args()
    
    # Si aucune option n'est spécifiée, faire les deux
    if not (args.extract or args.compile):
        args.all = True
    
    if args.extract or args.all:
        extract_translations(args.source, args.translations, args.files)
    
    if args.compile or args.all:
        compile_translations(args.translations, args.files)
    
    logger.info("Traitement des traductions terminé.")

if __name__ == "__main__":
    main()
