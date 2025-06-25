Copy-Item -Recurse -Force "c:\Users\Richa\.vscode\Projets_Windsurf\gmao_app_PostGres" "c:\Users\Richa\vscode\Projets_Windsurf\gmao_app_PostGres_backup_20240524"

Copy-Item -Recurse -Force "c:\Users\Richa\.vscode\Projets_Windsurf\gmao_app_PostGres" "c:\Users\Richa\.vscode\Projets_Windsurf\gmao_app_PostGres_backup_20240524"

Traduction


PySide6-lupdate app/ui/views/welcome_view.py -ts translations/welcome_view.ts
PySide6-lrelease translations/welcome_view.ts -qm translations/welcome_view.qm



Ton fichier installation.md est maintenant restructuré pour suivre un ordre logique, du serveur jusqu’à l’application, avec une table des matières claire et des étapes bien numérotées :

1. Prérequis & Préparation du système
Mise à jour, reboot, ressources recommandées, astuces sur Snap/Flatpak/pip.
2. Accès distant (RDP, SSH)
Installation et activation XRDP.
Activation et sécurisation SSH.
Configuration du pare-feu UFW (avec avertissement critique sur SSH).
3. Dépendances système (Qt, environnement graphique, outils réseau)
Installation Mate/Mate et librairies Qt nécessaires.
Configuration de la session graphique.
4. Installation et configuration PostgreSQL
Installation, activation, création de la base et de l’utilisateur.
5. Installation Python, venv et dépendances
Création de l’environnement virtuel, installation des requirements.
6. Déploiement et lancement de l’application
Emplacement du code, lancement manuel, automatisation au login.
7. Mode kiosque & multi-utilisateur
Configuration d’un utilisateur en mode kiosque.
Procédure multi-utilisateur (1 session graphique par user).
Basculer un utilisateur existant en mode kiosque.
8. Astuces, sécurité et dépannage
Déblocage SSH via RDP.
Vérification des services après reboot.
Logs utiles.
Retour en mode bureau complet.
Suppression d’utilisateur.
Les points critiques (UFW/SSH, droits, XRDP) sont bien mis en avant.
Ce guide est prêt pour toute réinstallation ou migration, et facile à compléter au fil des évolutions du projet.



# Guide d'installation et de configuration du serveur GMAO

## Table des matières
1. Prérequis & Préparation du système
2. Accès distant (RDP, SSH)
3. Dépendances système (bibliothèques Qt, outils réseau)
4. Installation et configuration PostgreSQL
5. Installation Python, venv et dépendances
6. Déploiement et lancement de l'application
7. Mode kiosque & multi-utilisateur
8. Astuces, sécurité et dépannage

---

## 1. Prérequis & Préparation du système
- Distribution Linux (Ubuntu, Mint, Debian, ...)
- Accès root ou sudo
- Ressources recommandées : 4 vCPU, 12 Go RAM, 70 Go SSD (KVM)

**Mise à jour système :**
```bash
sudo apt update && sudo apt upgrade -y
```
- Redémarre après une grosse mise à jour :
```bash
sudo reboot
```

**À mettre à jour séparément :**
- Snap : `sudo snap refresh`
- Flatpak : `flatpak update`
- Pip (venv) : `pip install --upgrade <nom_paquet>`

---

## 2. Accès distant (RDP, SSH)

### XRDP (RDP)
```bash
sudo apt install xrdp
sudo systemctl enable --now xrdp
```
- Vérifie le statut : `sudo systemctl status xrdp`

### SSH
- Toujours autoriser SSH avant d’activer UFW :
```bash
sudo ufw allow 22/tcp
sudo ufw status verbose
sudo systemctl enable --now ssh
```

### Pare-feu UFW
```bash
sudo ufw allow 3389/tcp
sudo ufw enable
sudo systemctl enable ufw
sudo ufw status verbose
```

> ⚠️ **ATTENTION UFW & SSH :** Toujours autoriser SSH (22) avant d’activer UFW, sinon tu risques de perdre l’accès distant !

---

## 3. Dépendances système (Qt, outils réseau)

Pour Mate/Mate :
```bash
sudo apt install mate-desktop-environment libxcb-xinerama0 libxcb-cursor0 libxkbcommon-x11-0 libglu1-mesa
```
- Pour Mate : `sudo apt install mate-desktop-environment`
- Vérifie l’environnement graphique dans `~/.xsession` :
  - Mate : `echo "startmate-desktop-environment" > ~/.xsession`
  - Mate : `echo "mate-session" > ~/.xsession`

---

## 4. Installation et configuration PostgreSQL

```bash
sudo apt install postgresql postgresql-contrib
sudo systemctl enable --now postgresql
```
- Crée la base et l’utilisateur selon tes besoins (voir doc projet).

---

## 5. Installation Python, venv et dépendances

Dans le dossier du projet :
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

---

## 6. Déploiement et lancement de l’application

- Place le code dans `/opt/Projets/gmao_app_PostGres/` (ou dans le home utilisateur pour tests).
- Pour lancer :
```bash
venv/bin/python main.py
```

- Pour automatiser le lancement à l’ouverture de session graphique, ajoute un `.desktop` dans `~/.config/autostart/` ou modifie `~/.xsession`.

---

## 7. Mode kiosque & multi-utilisateur

### a) Mode kiosque (mono-app)
- Mets dans `~/.xsession` :
```bash
#!/bin/bash
/opt/Projets/gmao_app_PostGres/venv/bin/python /opt/Projets/gmao_app_PostGres/main.py
```
- Droits :
```bash
chmod 755 ~/.xsession
chown <user>:<user> ~/.xsession
```

### b) Multi-utilisateur
- 1 session graphique active par utilisateur XRDP/Xorg.
- Crée un utilisateur :
```bash
sudo adduser nouveluser
```
- Copie le projet dans le home, crée un venv, installe les dépendances, configure `.xsession` comme ci-dessus.

### c) Basculer un utilisateur existant en mode kiosque
- Modifie son `.xsession` et ses droits.

---

## 8. Astuces, sécurité et dépannage

- **Déblocage SSH via RDP** :
  - Si SSH est bloqué mais RDP fonctionne, ouvre un terminal graphique et :
    ```bash
    sudo ufw allow 22/tcp
    sudo ufw reload
    sudo systemctl restart ssh
    sudo ufw status verbose
    ```
- **Vérifie toujours les services après reboot** :
  - `systemctl status xrdp ssh ufw postgresql`
- **Logs utiles** :
  - `/var/log/xrdp-sesman.log`, `/var/log/xrdp.log`, `/var/log/auth.log`
- **Mode bureau complet :**
  - Pour revenir à Mate : `echo "startmate-desktop-environment" > ~/.xsession`
  - Pour Mate : `echo "mate-session" > ~/.xsession`
- **Suppression d’utilisateur :**
```bash
sudo deluser --remove-home nouveluser
```

---

**Ce guide est à compléter à chaque évolution du projet.**

---

## 9. Accès VPN WireGuard (administration sécurisée)

### Cas d’un serveur derrière une box/modem (NAT, IP publique fixe)

Si ton serveur reçoit une IP interne (ex : 192.168.1.x) via DHCP derrière une box/modem avec IP publique fixe, suis ces étapes :

1. **Attribue une IP fixe à ton serveur sur le réseau local**
   - Soit via réservation DHCP dans l’interface du modem, soit en configurant le serveur (netplan, interfaces).
2. **Ouvre et redirige le port UDP 51820**
   - Dans l’interface du modem/routeur, crée une règle NAT/port forwarding :
     - Port externe : 51820/UDP
     - IP interne : celle du serveur (ex : 192.168.1.50)
     - Port interne : 51820/UDP
3. **Installe et configure WireGuard** (voir ci-dessous)
4. **Côté client WireGuard**
   - Dans la conf, mets l’IP publique de la box/modem :
     ```
     Endpoint = <IP_PUBLIQUE_BOX>:51820
     ```

**Schéma** :
```
[Internet] --(IP publique:51820)--> [Modem/Routeur]
   |                                 |
   |--(NAT/Port Forwarding:51820)----> [Serveur Linux:192.168.1.50:51820]
```

**Conseils sécurité** :
- N’ouvre que le port UDP 51820.
- Désactive l’admin à distance de la box.
- Change le mot de passe admin de la box.
- Teste la connexion WireGuard depuis l’extérieur.


### Installation côté serveur (Linux)
```bash
sudo apt install wireguard
cd /etc/wireguard
umask 077
wg genkey | tee privatekey | wg pubkey > publickey
# Note les clés privée/publique pour la conf
```

### Installation côté client (Windows)
- Télécharge WireGuard depuis https://www.wireguard.com/install/
- Crée une nouvelle connexion, importe la clé privée et la clé publique du serveur.

### Exemple de configuration serveur `/etc/wireguard/wg0.conf`
```
[Interface]
PrivateKey = <clé_privée_du_serveur>
Address = 10.8.0.1/24
ListenPort = 51820

[Peer]
PublicKey = <clé_publique_client>
AllowedIPs = 10.8.0.2/32
```

### Exemple de configuration client (Windows)
```
[Interface]
PrivateKey = <clé_privée_client>
Address = 10.8.0.2/24
DNS = 1.1.1.1

[Peer]
PublicKey = <clé_publique_serveur>
Endpoint = <IP_publique_serveur>:51820
AllowedIPs = 10.8.0.1/32, 10.8.0.0/24
PersistentKeepalive = 25
```

### Ouverture du port VPN
```bash
sudo ufw allow 51820/udp
```

### Démarrage automatique
```bash
sudo systemctl enable --now wg-quick@wg0
```

### Conseils de sécurité
- Restreindre l’accès SSH, VNC, XRDP, PostgreSQL… à l’interface VPN (`10.8.0.0/24`) via UFW.
- Tester la connexion VPN avant de fermer l’accès SSH public.
- Garder un accès d’urgence (console, RDP, VNC).

---

## 10. Accès VNC d’administration (console graphique de secours)

### Installation (exemple avec TigerVNC)
```bash
sudo apt install tigervnc-standalone-server
sudo -u richie vncpasswd  # Définit le mot de passe VNC pour richie
sudo -u richie vncserver :1  # Lance le serveur VNC sur le display :1 (port 5901)
```

### Connexion depuis un client VNC
- Utilise MobaXterm, Remmina, RealVNC, etc.
- Adresse : `<IP_serveur>:5901` (ou via tunnel SSH recommandé)

### Sécurisation
- Par défaut, VNC n’est **pas chiffré**. Toujours privilégier un tunnel SSH :
  ```bash
  ssh -L 5901:localhost:5901 richie@IP_serveur
  ```
- N’autoriser le port 5901 qu’en interne ou via VPN.
- N’ouvre jamais le port 5901 sur Internet sans tunnel.

### Utilisation
- VNC sert de console graphique de secours pour l’admin richie (si XRDP/SSH ne répondent plus).
- Peut être démarré/stoppé à la demande :
  ```bash
  sudo -u richie vncserver -kill :1
  sudo -u richie vncserver :1
  ```

---



## Prérequis
- Distribution Linux (ex : Linux Mint, Ubuntu, Debian)
- Accès root ou sudo

---

## 1. Mise à jour du système
```bash
sudo apt update
sudo apt upgrade -y
```

### Mettre à jour toutes les applications (console et graphiques)
- Les commandes ci-dessus mettent à jour toutes les applications installées via les dépôts APT, qu'elles soient en mode console ou graphiques (Firefox, Mousepad, Gedit, Filezilla, Remmina, etc.).
- Les utilitaires et logiciels installés avec `apt install ...` seront aussi mis à jour.

#### Ce qui n'est PAS mis à jour automatiquement :
- Les applications installées via Snap ou Flatpak :
  - Snap : `sudo snap refresh`
  - Flatpak : `flatpak update`
- Les paquets Python installés via `pip` dans un environnement virtuel (venv) :
  - `pip install --upgrade <nom_paquet>`

#### Astuce :
Après une grosse mise à jour (notamment du noyau), il est conseillé de redémarrer le serveur :
```bash
sudo reboot
```

## 2. Installation de XRDP (serveur RDP)
```bash
sudo apt install xrdp
```

## 3. (Facultatif) Installation de Mate (environnement graphique léger pour RDP)
```bash
sudo apt install mate-desktop-environment
```

## 4. Configuration de la session distante
Pour utiliser Mate lors des connexions RDP, crée ou modifie le fichier `~/.xsession` :
```bash
echo "startmate-desktop-environment" > ~/.xsession
```

(Si tu veux tester Mate, remplace par `echo "cinnamon-session" > ~/.xsession`)

## 5. Redémarrage du service XRDP
```bash
sudo systemctl restart xrdp
```

## 6. Ouverture du port 3389 (RDP) dans le pare-feu
```bash
sudo ufw allow 3389/tcp
```

## 7. Vérification de l'adresse IP de la machine
```bash
ip a
# ou plus simplement
hostname -I
```

## 8. Vérification du service XRDP
```bash
sudo systemctl status xrdp
```

## 9. Test de la connexion RDP depuis Windows
- Ouvre le client Bureau à distance (`mstsc`)
- Saisis l'adresse IP trouvée précédemment
- Connecte-toi avec ton utilisateur Linux

---

## 10. Installation de l'environnement Python (venv)
```bash
python3 -m venv venv
source venv/bin/activate
```

## 11. Installation des dépendances Python
Exemple pour PySide6, python-dotenv, etc. :
```bash
pip install PySide6 python-dotenv python-dateutil bcrypt jinja2 pdfkit --break-system-packages
```

## 12. Lancement de l'application graphique
```bash
venv/bin/python main.py
```

---

**Remarque :**

- Pour automatiser le lancement de l'application à l'ouverture de session RDP/Mate, tu peux ajouter un fichier `.desktop` dans `~/.config/autostart/`.
- Pour la migration vers PostgreSQL et Admin4, voir la suite du guide.

---

## 13. Mode kiosque (mono-application) avec XRDP


Pour que seule l'application se lance à l'ouverture de session RDP (sans bureau Mate derrière), et que la session se ferme automatiquement à la fermeture de l'application :

1. Modifie le fichier `~/.xsession` pour qu'il contienne uniquement :
   ```bash
   #!/bin/bash
   /opt/Projets/gmao_app_PostGres/venv/bin/python /opt/Projets/gmao_app_PostGres/main.py
   ```

   Pour l'appliquer à un utilisateur donné (par exemple jules), connecte-toi en tant qu'admin et exécute :
   ```bash
   echo -e '#!/bin/bash\n/opt/Projets/gmao_app_PostGres/venv/bin/python /opt/Projets/gmao_app_PostGres/main.py' | sudo tee /home/jules/.xsession
   sudo chmod 755 /home/jules/.xsession
   sudo chown jules:jules /home/jules/.xsession
   ```

   (Adapte le nom d'utilisateur au besoin)

---

## 14. Librairies système Qt/PySide indispensables sous Mate

Sur un serveur Ubuntu/Debian avec Mate, certaines librairies Qt ne sont **pas installées par défaut** (contrairement à Gnome, Mate, Wayland, etc.).

Pour garantir le bon fonctionnement des applications Qt/PySide (éviter les erreurs du type « Could not load the Qt platform plugin 'xcb' »), installe les librairies suivantes :

```bash
sudo apt install libxcb-xinerama0 libxcb-cursor0 libxkbcommon-x11-0 libglu1-mesa
```

Sans ces librairies, les applications Qt/PySide ne démarrent pas ou plantent au lancement.
   ```
2. Supprime le fichier d'autostart s'il existe :
   ```bash
   rm ~/.config/autostart/gmao_app.desktop
   ```

**Résultat :**
- À la connexion RDP, seule l'application s'affiche (pas de bureau ni de barre Mate).
- Quand l'application est fermée, la session RDP se termine automatiquement.

### Revenir au mode bureau complet (Mate)

Pour repasser en mode bureau classique :
1. Modifie `~/.xsession` pour y remettre :   startmate-desktop-environment
2. (Optionnel) Remets le fichier `.desktop` dans `~/.config/autostart/` si tu veux relancer automatiquement l'application dans le bureau Mate.

---

**À compléter au fur et à mesure des prochaines étapes !**

---

## 14. Ajouter un nouvel utilisateur Linux pour le mode kiosque (multi-utilisateurs indépendants)

### Rappel important
- **XRDP/Xorg ne permet qu'une seule session graphique active par utilisateur à la fois.**
- Pour avoir plusieurs sessions simultanées, il faut utiliser des comptes utilisateurs différents (user1, user2, user3, ...).

### Procédure pour ajouter un nouvel utilisateur prêt à lancer l'application GMAO en mode kiosque

1. **Créer le nouvel utilisateur**
```bash
sudo adduser nouveluser
```

2. **Se connecter avec le nouvel utilisateur (localement ou via RDP)**

3. **Créer l'environnement Python et installer le projet**
```bash
mkdir -p ~/Documents/gmao_app_windsurf
# Copier le projet dans ce dossier (clé USB, réseau, ou clonage git)
cd ~/Documents/gmao_app_windsurf
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

4. **Configurer le démarrage automatique de l'application en mode kiosque**
En tant que richie ou avec sudo :
```bash
echo -e '#!/bin/bash\n/home/nouveluser/Documents/gmao_app_windsurf/venv/bin/python /home/nouveluser/Documents/gmao_app_windsurf/main.py' | sudo tee /home/nouveluser/.xsession
sudo chmod 755 /home/nouveluser/.xsession
sudo chown nouveluser:nouveluser /home/nouveluser/.xsession
```

5. **Connexion RDP**
- Connecte-toi via RDP avec le nouvel utilisateur : l'application se lance directement en mode kiosque, sans bureau.

### Remarques
- Pour chaque utilisateur, répète la procédure (user2, user3, etc.).
- Chaque utilisateur a son propre environnement, ses propres fichiers et droits.
- Si tu veux supprimer un utilisateur :
```bash
sudo deluser --remove-home nouveluser
```

### Limite XRDP
> Un utilisateur ne peut avoir qu'une seule session graphique ouverte à la fois. Pour des sessions simultanées, il faut utiliser des comptes utilisateurs différents.

---

### Basculer un utilisateur existant en mode kiosque (même application que les autres)

Pour mettre un utilisateur existant (ex : fred, john) en mode kiosque avec la même application et le même environnement Python :

1. **Éditer le fichier `.xsession` de l'utilisateur** :
   ```bash
   sudo nano /home/nom_utilisateur/.xsession
   ```
   et y mettre :
   ```bash
   #!/bin/bash
   /opt/Projets/gmao_app_PostGres/venv/bin/python /opt/Projets/gmao_app_PostGres/main.py
   ```
   (Adapte le chemin si besoin.)

2. **Vérifier les droits** :
   ```bash
   sudo chown nom_utilisateur:nom_utilisateur /home/nom_utilisateur/.xsession
   sudo chmod 700 /home/nom_utilisateur/.xsession
   ```

3. **Supprimer tout autostart parasite** (si besoin) :
   ```bash
   sudo rm /home/nom_utilisateur/.config/autostart/gmao_app.desktop
   ```

4. **À la prochaine connexion RDP** avec ce compte, seule l’application se lancera (mode kiosk).

---

**Notes** :
- Répète la procédure pour chaque utilisateur à basculer.
- L’admin (richie) doit garder un bureau complet (ne pas mettre en mode kiosk).
- Pour revenir à un bureau complet, remets simplement `mate-session` dans `.xsession`.


---
