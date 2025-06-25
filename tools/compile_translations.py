import os
import sys
from PySide6.linguist import lrelease

def compile_translations():
    translations_dir = os.path.join(os.path.dirname(__file__), 'translations')
    
    # Create translations directory if it doesn't exist
    os.makedirs(translations_dir, exist_ok=True)
    
    # Compile .ts files to .qm
    for filename in os.listdir(translations_dir):
        if filename.endswith('.ts'):
            ts_path = os.path.join(translations_dir, filename)
            qm_path = os.path.splitext(ts_path)[0] + '.qm'
            print(f"Compiling {filename}...")
            success = lrelease(ts_path, qm_path)
            if success:
                print(f"Successfully compiled {filename}")
            else:
                print(f"Failed to compile {filename}")

if __name__ == "__main__":
    compile_translations()
