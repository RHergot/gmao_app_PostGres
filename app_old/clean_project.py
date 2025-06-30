import os
import shutil

def clean_project(project_root=None):
    """Supprime tous les fichiers .pyc et dossiers __pycache__ du projet."""
    if project_root is None:
        project_root = os.path.dirname(os.path.abspath(__file__))
    pyc_count = 0
    pycache_count = 0
    for dirpath, dirnames, filenames in os.walk(project_root):
        # Remove .pyc files
        for filename in filenames:
            if filename.endswith('.pyc'):
                file_path = os.path.join(dirpath, filename)
                try:
                    os.remove(file_path)
                    pyc_count += 1
                except Exception as e:
                    print(f"Erreur suppression {file_path}: {e}")
        # Remove __pycache__ directories
        for dirname in dirnames:
            if dirname == '__pycache__':
                pycache_path = os.path.join(dirpath, dirname)
                try:
                    shutil.rmtree(pycache_path)
                    pycache_count += 1
                except Exception as e:
                    print(f"Erreur suppression {pycache_path}: {e}")
    print(f"Suppression terminée : {pyc_count} fichiers .pyc et {pycache_count} dossiers __pycache__ supprimés.")

if __name__ == "__main__":
    clean_project()
