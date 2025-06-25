from PySide6.linguist import lrelease

# Chemin du fichier source et de destination
ts_file = "translations/site_dialog_fr_FR.ts"
qm_file = "translations/site_dialog_fr_FR.qm"

# Compilation du fichier
result = lrelease(ts_file, qm_file)
print(f"Compilation {'réussie' if result else 'échouée'}")