#!/usr/bin/env bash
# prueba de humo (agents.md § 5): levanta el gemelo en local y le pasa, con el comparador de la regla del juez,
# los 20 ejemplos del material y todas las secuencias del log. no toca el original. sale con error si algo difiere.
set -euo pipefail
cd "$(dirname "$0")"
PUERTO="${PUERTO:-18080}"; TOKEN="smoke-local"
GEMELO_TOKEN="$TOKEN" PORT="$PUERTO" python3 gemelo/servidor.py > /dev/null 2>&1 & PID=$!
trap 'kill $PID 2>/dev/null || true' EXIT
python3 - "$PUERTO" "$TOKEN" <<'PY'
import sys, time, http.client
for _ in range(50):
    try:
        c = http.client.HTTPConnection("127.0.0.1", int(sys.argv[1]), timeout=1)
        c.request("GET", "/health", headers={"Authorization": "Bearer " + sys.argv[2]})
        if c.getresponse().status == 200: sys.exit(0)
    except OSError:
        time.sleep(0.1)
sys.exit("smoke: el gemelo no respondió /health en 5 s")
PY
echo "smoke: ejemplos del material"; python3 medir.py --casos material/pruebas/ejemplos.jsonl --gemelo "http://127.0.0.1:$PUERTO" --token "$TOKEN"
# se saltan las líneas que respondió el borde de railway y no el servicio (borde_railway: no se reproducen en local)
# y las de la versión de la mañana que el incidente dejó atrás (fase: manana; incident.md, protocolo 5)
LOG_LOCAL="$(mktemp)"; trap 'kill $PID 2>/dev/null || true; rm -f "$LOG_LOCAL"' EXIT
grep -v -e '"borde_railway": true' -e '"fase": "manana"' experimentos.jsonl > "$LOG_LOCAL"
echo "smoke: secuencias del log";    python3 medir.py --casos "$LOG_LOCAL" --gemelo "http://127.0.0.1:$PUERTO" --token "$TOKEN"
echo "smoke: OK"
