#!/usr/bin/env bash
# pulso del gemelo desplegado (idea de fable, 15:2x bog): un GET /health por minuto, sin token y sin tocar el original.
# sin token el gemelo responde 401 (como el original), pero sus headers dicen qué versión corre y desde cuándo
# (X-Gemelo-Version, X-Gemelo-Arranque): un arranque nuevo sin push nuestro es un reinicio de railway.
# imprime una línea al empezar y después solo si algo cambia: versión, arranque, status distinto de 401,
# más de 2 s de respuesta o sin respuesta. todo queda además en $PULSO_LOG.
URL="${GEMELO_URL:-https://frontier-bog26-caja-negra-production.up.railway.app}/health"
LOG="${PULSO_LOG:-/dev/null}"
previo=""
while true; do
  t=$(date -u +%H:%M:%SZ)
  r=$(curl -s -m 10 -o /dev/null -D - -w 'STATUS %{http_code} %{time_total}\n' "$URL" 2>/dev/null)
  st=$(sed -n 's/^STATUS \([0-9]*\) .*/\1/p' <<<"$r"); seg=$(sed -n 's/^STATUS [0-9]* \(.*\)/\1/p' <<<"$r")
  ver=$(grep -i '^x-gemelo-version' <<<"$r" | tr -d '\r' | cut -d' ' -f2)
  arr=$(grep -i '^x-gemelo-arranque' <<<"$r" | tr -d '\r' | cut -d' ' -f2)
  echo "$t $st $seg $ver $arr" >> "$LOG"
  ahora="$ver $arr"
  if [ -z "$previo" ]; then echo "pulso $t: $st en ${seg}s · $ver desde $arr"
  elif [ "$st" != "401" ] || [ -z "$st" ]; then echo "pulso $t: ALERTA status '${st:-sin respuesta}' (${seg}s) · $ver $arr"
  elif [ "$ahora" != "$previo" ]; then echo "pulso $t: CAMBIO $previo → $ahora (¿push nuestro o reinicio de railway?)"
  elif awk "BEGIN{exit !($seg > 2)}"; then echo "pulso $t: LENTO ${seg}s · $ver"
  fi
  [ -n "$ver" ] && previo="$ahora"
  sleep 60
done
