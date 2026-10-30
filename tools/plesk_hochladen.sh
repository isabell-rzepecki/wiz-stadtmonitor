#!/usr/bin/env bash
# Fertige Seite (_site) per SFTP auf den Webserver der Subdomain laden (Plesk). Aufruf aus GitHub Actions, Zugangsdaten nur
# als Secrets in der Umgebung, nie im Repository:
#   PLESK_HOST        Servername (Pflicht; ohne ihn wird nichts hochgeladen)
#   PLESK_USER        Benutzer mit SFTP-Zugang (Plesk: FTP-/SSH-Zugang des Abonnements)
#   PLESK_PASSWORT    Passwort dazu
#   PLESK_PFAD        Dokumentstamm der Subdomain auf dem Server, etwa stadtmonitor.wiz-o-mat.de oder httpdocs (Pflicht)
#   PLESK_PORT        SSH-Port (Standard 22)
#   PLESK_KNOWN_HOSTS Zeile(n) für known_hosts; fehlt sie, wird der Hostschlüssel beim Abruf übernommen und ausgegeben
#   PLESK_URL_SCHEMA  sftp (Standard); nur für Tests anders
# Sicherung gegen einen falschen Pfad: Dateien, die es in _site nicht mehr gibt, werden erst gelöscht, wenn im Ziel die
# Markierung .stadtmonitor liegt. Die erste Übertragung legt sie an, ohne etwas zu löschen. Ausgenommen: .well-known
# (Zertifikate von Let's Encrypt).
set -euo pipefail
QUELLE="${1:-_site}"
: "${PLESK_HOST:?}" "${PLESK_USER:?}" "${PLESK_PASSWORT:?}"
PFAD="${PLESK_PFAD:-}"
case "$PFAD" in
  "" | "/" | "." | "./" | "~" | "~/" | ".." | ../*) echo "PLESK_PFAD fehlt oder ist kein Dokumentstamm: »$PFAD«" >&2; exit 2 ;;
esac
PORT="${PLESK_PORT:-22}"
SCHEMA="${PLESK_URL_SCHEMA:-sftp}"
KH="$(mktemp)"
trap 'rm -f "$KH"' EXIT
if [ "$SCHEMA" = sftp ]; then
  if [ -n "${PLESK_KNOWN_HOSTS:-}" ]; then
    printf '%s\n' "$PLESK_KNOWN_HOSTS" > "$KH"
  else
    ssh-keyscan -p "$PORT" "$PLESK_HOST" > "$KH" 2>/dev/null
    echo "Hinweis: Hostschlüssel ungeprüft übernommen (Secret PLESK_KNOWN_HOSTS fehlt). Fingerabdrücke:"
    ssh-keygen -lf "$KH"
  fi
fi
export LFTP_PASSWORD="$PLESK_PASSWORT"
VERBINDUNG="set sftp:auto-confirm no; set sftp:connect-program 'ssh -a -x -o StrictHostKeyChecking=yes -o UserKnownHostsFile=$KH'; set net:max-retries 3; set net:timeout 30; set cmd:fail-exit yes; open -u $PLESK_USER --env-password -p $PORT $SCHEMA://$PLESK_HOST"
if lftp -c "$VERBINDUNG; cls -1 $PFAD/.stadtmonitor" >/dev/null 2>&1; then
  LOESCHEN="--delete"
else
  LOESCHEN=""
  echo "Erste Übertragung nach $PFAD: Markierung .stadtmonitor fehlt, es wird nichts gelöscht."
fi
touch "$QUELLE/.stadtmonitor"
lftp -c "$VERBINDUNG; mirror -R $LOESCHEN --parallel=4 --exclude-glob .well-known/ --verbose=1 $QUELLE/ $PFAD"
echo "Hochgeladen nach $SCHEMA://$PLESK_HOST/$PFAD"
