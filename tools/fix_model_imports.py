#!/usr/bin/env python3
"""
Script pour vérifier et corriger les imports dans tous les fichiers modèles.
"""

import os
import sys
from pathlib import Path

def check_and_fix_imports(file_path):
    """Vérifie et corrige les imports dans un fichier modèle."""
    print(f"Traitement de {file_path}")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original_content = content
    modified = False
    
    # Vérifier si le fichier utilise Union, Dict ou Any sans les importer
    if ('Union[' in content or 'Dict[' in content or ', Any' in content or ': Any' in content) and not all(type_name in content for type_name in ['from typing import', 'Union', 'Dict', 'Any']):
        # Le fichier utilise ces types mais ne les importe pas tous
        print(f"  - Manque d'import pour typing dans {file_path}")
        
        # Trouver la ligne d'importation de typing existante
        if 'from typing import' in content:
            # Ajouter les imports manquants
            if 'Union' not in content:
                content = content.replace('from typing import', 'from typing import Union, ')
                modified = True
            if 'Dict' not in content:
                content = content.replace('from typing import', 'from typing import Dict, ')
                modified = True
            if 'Any' not in content:
                content = content.replace('from typing import', 'from typing import Any, ')
                modified = True
            
            # Nettoyer les virgules en trop
            content = content.replace(', ,', ',')
        else:
            # Ajouter la ligne d'importation de typing complète
            print(f"  - Ajout d'imports typing complets dans {file_path}")
            old_import = 'from typing import Optional'
            new_import = 'from typing import Optional, Union, Dict, Any'
            if old_import in content:
                content = content.replace(old_import, new_import)
            else:
                # Ajouter après les autres imports de typing
                lines = content.split('\n')
                last_import_idx = -1
                for i, line in enumerate(lines):
                    if line.startswith('import ') or line.startswith('from '):
                        last_import_idx = i
                
                if last_import_idx >= 0:
                    lines.insert(last_import_idx + 1, 'from typing import Optional, Union, Dict, Any')
                else:
                    # Ajouter au début du fichier
                    lines.insert(0, 'from typing import Optional, Union, Dict, Any')
                
                content = '\n'.join(lines)
            modified = True
    
    # Vérifier s'il y a des problèmes d'indentation après @dataclass
    if '@dataclass\nclass' in content and ':\n    ' not in content:
        print(f"  - Problème d'indentation dans {file_path}")
        content = content.replace('@dataclass\nclass', '@dataclass\nclass').replace(':    ', ':\n    ')
        modified = True
    
    # Sauvegarder les modifications
    if modified:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"  ✓ Fichier {file_path} corrigé")
        return True
    else:
        print(f"  - Aucune correction nécessaire pour {file_path}")
        return False

def main():
    """Fonction principale."""
    if len(sys.argv) > 1 and sys.argv[1] == '--help':
        print("Usage: python script.py [--force]")
        print("  --force: Corriger tous les fichiers, même s'ils ne semblent pas avoir besoin de corrections")
        return
    
    force = len(sys.argv) > 1 and sys.argv[1] == '--force'
    
    models_dir = Path("app/core/models")
    if not models_dir.exists():
        print(f"Répertoire {models_dir} introuvable")
        return
    
    fixed_count = 0
    checked_count = 0
    
    for py_file in models_dir.glob("*.py"):
        if py_file.name != "__init__.py":
            checked_count += 1
            if check_and_fix_imports(py_file) or force:
                fixed_count += 1
    
    print(f"\n✓ {fixed_count} fichiers corrigés sur {checked_count} vérifiés")

if __name__ == "__main__":
    main()
