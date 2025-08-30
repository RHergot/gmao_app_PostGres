Pour tous les fichiers .py du répertoire /app/ui/dialogs et du répertoire app/ui/views :
tu ouvre les fichier .py 
tu inscrits self.tr( ) pour tous les textes que l'utilisateur pourra voir et tu sauvegardes les modifications. Attention il faut parfois utiliser format() pour les textes avec des variables.
tu appliques pyside6-lupdate app/ui/views/fichier.py -ts en_translations/fichier.ts
tu ouvres le fichier .ts et tu traduis tous les textes français en anglais
Attendre une confimation
tu refermes le fichier et tu exécutes : pyside6-lrelease en_translations/fichier.ts -qm en_translations/fichier.qm
tu inscris le fichier .qm dans main.py


