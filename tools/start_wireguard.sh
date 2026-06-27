#!/bin/bash
# Script pour démarrer, arrêter ou vérifier l'état de WireGuard (wg0)
# Usage : ./start_wireguard.sh [start|stop|status|restart]

set -euo pipefail

WG_INTERFACE="wg0"
WG_CONF="/etc/wireguard/${WG_INTERFACE}.conf"

# Vérification préalable : le fichier de configuration doit exister pour les actions start/restart/enable
check_config() {
    if [ ! -f "$WG_CONF" ]; then
        echo "ERREUR: Le fichier de configuration $WG_CONF n'existe pas."
        echo "Veuillez créer la configuration WireGuard avant de lancer cette action."
        exit 1
    fi
}

case "$1" in
  start)
    check_config
    sudo wg-quick up $WG_INTERFACE
    ;;
  stop)
    sudo wg-quick down $WG_INTERFACE
    ;;
  restart)
    check_config
    sudo wg-quick down $WG_INTERFACE
    sudo wg-quick up $WG_INTERFACE
    ;;
  status)
    sudo wg
    sudo systemctl status wg-quick@${WG_INTERFACE}
    ;;
  enable)
    check_config
    sudo systemctl enable --now wg-quick@${WG_INTERFACE}
    ;;
  disable)
    sudo systemctl disable --now wg-quick@${WG_INTERFACE}
    ;;
  *)
    echo "Usage: $0 [start|stop|restart|status|enable|disable]"
    ;;
esac
