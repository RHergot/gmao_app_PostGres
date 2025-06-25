#!/usr/bin/env python3
"""
Script amélioré pour corriger automatiquement les vestiges SQLite dans les modèles.
"""

import os
import re
from pathlib import Path

def fix_model_file(file_path):
    """Corrige un fichier de modèle pour remplacer les références SQLite."""
    print(f"Correction de {file_path}")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original_content = content
    
    # Ajouter les imports nécessaires
    if 'from typing import ' in content:
        # Vérifiez si les types ne sont pas déjà importés
        needed_types = []
        for type_name in ['Union', 'Dict', 'Any']:
            if type_name not in content:
                needed_types.append(type_name)
            
        if needed_types:
            # Trouver la ligne d'importation existante
            import_match = re.search(r'from typing import ([^\n]+)', content)
            if import_match:
                old_import = import_match.group(0)
                # Si la ligne d'importation se termine par une virgule, il pourrait y avoir une ligne de continuation
                if old_import.strip().endswith(','):
                    # Ajouter juste les types manquants après la virgule
                    new_import = old_import + ' ' + ', '.join(needed_types)
                else:
                    # Sinon, ajouter une virgule et les types manquants
                    new_import = old_import + ', ' + ', '.join(needed_types)
                content = content.replace(old_import, new_import)
    
    # Remplacer les signatures from_db_row avec le mauvais format de paramètres
    content = re.sub(
        r'def from_db_row\(cls, row: Optional\[sqlite3\.Row\], Union, Dict, Any\)',
        r'def from_db_row(cls, row: Optional[Union[Dict[str, Any], Any]])',
        content
    )
    
    # Remplacer les signatures from_db_row qui utilisent encore sqlite3.Row
    content = re.sub(
        r'def from_db_row\(cls, row: Optional\[sqlite3\.Row\]\)',
        r'def from_db_row(cls, row: Optional[Union[Dict[str, Any], Any]])',
        content
    )
    
    # Remplacer les commentaires faisant référence à sqlite3.Row
    content = re.sub(
        r'à partir d\'une ligne sqlite3\.Row',
        r'à partir d\'une ligne de base de données',
        content
    )
    
    content = re.sub(
        r'depuis une ligne sqlite3\.Row',
        r'depuis une ligne de base de données',
        content
    )
    
    content = re.sub(
        r'\(sqlite3\.Row\)',
        r'(base de données)',
        content
    )
    
    # Remplacer les vérifications isinstance(row, sqlite3.Row)
    content = re.sub(
        r'isinstance\(row, sqlite3\.Row\)',
        r'hasattr(row, "keys")',
        content
    )
    
    # Supprimer l'import de sqlite3
    content = re.sub(r'import sqlite3.*\n', '', content)
    
    # Sauvegarder si des changements ont été effectués
    if content != original_content:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"  ✓ {file_path} corrigé")
        return True
    else:
        print(f"  - {file_path} aucun changement nécessaire")
        return False

def main():
    """Fonction principale."""
    root_dir = Path(".")
    models_dir = root_dir / "app" / "core" / "models"
    
    if not models_dir.exists():
        print(f"Répertoire {models_dir} introuvable")
        return
    
    fixed_count = 0
    for py_file in models_dir.glob("*.py"):
        if py_file.name != "__init__.py":
            if fix_model_file(py_file):
                fixed_count += 1
    
    print(f"\n✓ {fixed_count} fichiers corrigés")

if __name__ == "__main__":
    main()
