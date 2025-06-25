#!/usr/bin/env python3
"""
Script pour corriger automatiquement les vestiges SQLite dans les modèles.
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
    
    # Remplacer l'import sqlite3
    content = re.sub(r'import sqlite3\n', '', content)
    
    # Ajouter Union et Dict dans les imports typing si pas déjà présent
    if 'from typing import' in content and 'Union' not in content:
        content = re.sub(
            r'from typing import ([^)]+)',
            r'from typing import \1, Union, Dict, Any',
            content
        )
    
    # Remplacer les signatures from_db_row
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
    
    # Remplacer les vérifications isinstance(row, sqlite3.Row)
    content = re.sub(
        r'isinstance\(row, sqlite3\.Row\)',
        r'hasattr(row, "keys")',
        content
    )
    
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
    models_dir = Path("app/core/models")
    
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
