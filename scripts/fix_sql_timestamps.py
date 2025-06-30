#!/usr/bin/env python3
"""
Script pour corriger les vues KPI en gérant le cast des dates depuis TEXT vers TIMESTAMP.
"""

import sys
import os
import re

def fix_sql_timestamp_casts(file_path):
    """
    Corrige les comparaisons de date dans le fichier SQL en ajoutant les casts nécessaires.
    """
    
    print(f"Correction du fichier SQL: {file_path}")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Pattern pour détecter les comparaisons de date_fin_reelle sans cast
    patterns_to_fix = [
        # date_fin_reelle >= CURRENT_DATE
        (r'date_fin_reelle\s*>=\s*CURRENT_DATE', r'date_fin_reelle::timestamp >= CURRENT_DATE'),
        # date_fin_reelle < CURRENT_DATE  
        (r'date_fin_reelle\s*<\s*CURRENT_DATE', r'date_fin_reelle::timestamp < CURRENT_DATE'),
        # date_fin_reelle <= CURRENT_DATE
        (r'date_fin_reelle\s*<=\s*CURRENT_DATE', r'date_fin_reelle::timestamp <= CURRENT_DATE'),
        # date_fin_reelle > CURRENT_DATE
        (r'date_fin_reelle\s*>\s*CURRENT_DATE', r'date_fin_reelle::timestamp > CURRENT_DATE'),
        # date_debut_reelle (même problème potentiel)
        (r'date_debut_reelle\s*>=\s*CURRENT_DATE', r'date_debut_reelle::timestamp >= CURRENT_DATE'),
        (r'date_debut_reelle\s*<\s*CURRENT_DATE', r'date_debut_reelle::timestamp < CURRENT_DATE'),
        (r'date_debut_reelle\s*<=\s*CURRENT_DATE', r'date_debut_reelle::timestamp <= CURRENT_DATE'),
        (r'date_debut_reelle\s*>\s*CURRENT_DATE', r'date_debut_reelle::timestamp > CURRENT_DATE'),
    ]
    
    original_content = content
    corrections_made = 0
    
    for pattern, replacement in patterns_to_fix:
        new_content = re.sub(pattern, replacement, content)
        if new_content != content:
            matches = len(re.findall(pattern, content))
            print(f"  Corrigé {matches} occurrence(s) de: {pattern}")
            corrections_made += matches
            content = new_content
    
    # Écrire le fichier corrigé
    if content != original_content:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"✅ Fichier corrigé avec {corrections_made} modifications")
    else:
        print("ℹ️  Aucune correction nécessaire")
    
    return corrections_made > 0

if __name__ == "__main__":
    # Chemin vers le fichier SQL
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.join(script_dir, '..')
    sql_file = os.path.join(project_root, 'app', 'sql_vues_kpi_financiers.sql')
    
    if os.path.exists(sql_file):
        fixed = fix_sql_timestamp_casts(sql_file)
        if fixed:
            print("\n🔧 Fichier SQL corrigé. Vous pouvez maintenant relancer:")
            print("   python scripts/init_kpi_views.py")
        else:
            print("\n✅ Le fichier SQL était déjà correct")
    else:
        print(f"❌ Fichier non trouvé: {sql_file}")
