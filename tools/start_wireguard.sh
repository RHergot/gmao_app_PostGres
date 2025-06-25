#!/bin/bash
# Script pour démarrer, arrêter ou vérifier l'état de WireGuard (wg0)
# Usage : ./start_wireguard.sh [start|stop|status|restart]

WG_INTERFACE="wg0"

case "$1" in
  start)
    sudo wg-quick up $WG_INTERFACE
    ;;
  stop)
    sudo wg-quick down $WG_INTERFACE
    ;;
  restart)
    sudo wg-quick down $WG_INTERFACE
    sudo wg-quick up $WG_INTERFACE
    ;;
  status)
    sudo wg
    sudo systemctl status wg-quick@${WG_INTERFACE}
    ;;
  enable)
    sudo systemctl enable --now wg-quick@${WG_INTERFACE}
    ;;
  disable)
    sudo systemctl disable --now wg-quick@${WG_INTERFACE}
    ;;
  *)
    echo "Usage: $0 [start|stop|restart|status|enable|disable]"
    ;;
esac
