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
# después del incidente hay dos modelos (incident.md, plan de regla nueva, paso 3): el vigente (la tarde) y el
# congelado antes del cambio (gemelo/modelo-manana.json). los 20 ejemplos del material son de la mañana.
PM="$PUERTO"; PID2=""
if [ -f gemelo/modelo-manana.json ]; then
  PM=$((PUERTO + 1))
  GEMELO_TOKEN="$TOKEN" PORT="$PM" GEMELO_MODELO=gemelo/modelo-manana.json python3 gemelo/servidor.py > /dev/null 2>&1 & PID2=$!
  for _ in $(seq 50); do curl -s -o /dev/null -H "Authorization: Bearer $TOKEN" "http://127.0.0.1:$PM/health" && break; sleep 0.1; done
fi
LOG_LOCAL="$(mktemp)"; LOG_MANANA="$(mktemp)"; trap 'kill $PID $PID2 2>/dev/null || true; rm -f "$LOG_LOCAL" "$LOG_MANANA"' EXIT
echo "smoke: ejemplos del material"; python3 medir.py --casos material/pruebas/ejemplos.jsonl --gemelo "http://127.0.0.1:$PM" --token "$TOKEN"
# se saltan las líneas que respondió el borde de railway y no el servicio (borde_railway: no se reproducen en local);
# las de la versión de la mañana que el incidente contradice (fase: manana; herramientas/fase.py) van contra el
# modelo de la mañana
grep -v -e '"borde_railway": true' -e '"fase": "manana"' experimentos.jsonl > "$LOG_LOCAL"
echo "smoke: secuencias del log";    python3 medir.py --casos "$LOG_LOCAL" --gemelo "http://127.0.0.1:$PUERTO" --token "$TOKEN"
if [ -n "$PID2" ] && grep -q '"fase": "manana"' experimentos.jsonl; then
  grep '"fase": "manana"' experimentos.jsonl | grep -v '"borde_railway": true' > "$LOG_MANANA"
  echo "smoke: secuencias de la mañana (modelo-manana.json)"; python3 medir.py --casos "$LOG_MANANA" --gemelo "http://127.0.0.1:$PM" --token "$TOKEN"
fi
echo "smoke: OK"
