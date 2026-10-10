#!/usr/bin/env bash
# lado a lado: el mismo mensaje al original y al gemelo, para grabar el video.
# pide los dos tokens sin mostrarlos en pantalla y no los guarda en ningún lado.
#   bash video/lado_a_lado.sh
# candado (claude, el que lidera): este script resetea el gemelo desplegado. después de las 19:50 bog no se corre,
# porque el set final del jurado corre después de las 20:00 a una hora que no sabemos y un reset le rompería un test.
# sus pedidos al original no quedan en experimentos.jsonl: si se graba, se anota en ESTADO.md cuántos fueron y a qué hora.
hm=$(TZ=America/Bogota date +%H%M)
if [ $((10#$hm)) -ge 1950 ] || [ $((10#$hm)) -lt 600 ]; then
  echo "lado_a_lado: después de las 19:50 bog no se corre (resetea el gemelo desplegado y el set final puede estar corriendo)"; exit 1
fi
# los tokens salen del entorno (ORIGINAL_TOKEN, GEMELO_TOKEN) y si faltan se piden sin mostrarlos.
# GEMELO_URL apunta a otra copia del gemelo: con una copia local del mismo commit no se toca el desplegado.
#   GEMELO_URL=http://127.0.0.1:8090 GEMELO_TOKEN=local bash video/lado_a_lado.sh
ORIG="${ORIGINAL_URL:-https://caja-negra-production-c64f.up.railway.app}"
GEM="${GEMELO_URL:-https://frontier-bog26-caja-negra-production.up.railway.app}"
TO="${ORIGINAL_TOKEN:-}"; TG="${GEMELO_TOKEN:-}"
[ -n "$TO" ] || { read -rsp "token personal de la caja (el de MOSTRAR): " TO; echo; }
[ -n "$TG" ] || { read -rsp "token del equipo (el de COPIAR): " TG; echo; }
VER=$(curl -s -m 5 -D - -o /dev/null "$GEM/health" -H "Authorization: Bearer $TG" | tr -d '\r' | awk -F': ' 'tolower($1)=="x-gemelo-version"{print $2}')
printf '\033[1moriginal:\033[0m %s\n\033[1mgemelo:\033[0m   %s · %s · commit %s\n' "$ORIG" "$GEM" "${VER:-?}" "$(git rev-parse --short HEAD 2>/dev/null || echo '?')"
norm() { if command -v python3 >/dev/null; then python3 -c 'import sys,json
t=sys.stdin.read()
try: print(json.dumps(json.loads(t),ensure_ascii=False,sort_keys=True))
except Exception: print(t)'; else cat; fi; }
paso() {
  local m="$1"
  local a b sa sb
  a=$(curl -s -m 5 -w '\n%{http_code}' -X POST "$ORIG/msg" -H "Authorization: Bearer $TO" -H 'Content-Type: application/json' -d "{\"m\": \"$m\"}")
  b=$(curl -s -m 5 -w '\n%{http_code}' -X POST "$GEM/msg"  -H "Authorization: Bearer $TG" -H 'Content-Type: application/json' -d "{\"m\": \"$m\"}")
  sa=${a##*$'\n'}; sb=${b##*$'\n'}
  a=$(printf '%s' "${a%$'\n'*}" | norm); b=$(printf '%s' "${b%$'\n'*}" | norm)
  printf '\n\033[1m> %s\033[0m\n' "$m"
  printf '  original  %s %s\n' "$sa" "$a"
  printf '  gemelo    %s %s\n' "$sb" "$b"
  if [ "$sa" = "$sb" ] && [ "$a" = "$b" ]; then printf '  \033[32m✓ iguales\033[0m\n'; else printf '  \033[31m✗ distintos\033[0m\n'; fi
  sleep 1.2
}
curl -s -m 5 -o /dev/null -X POST "$ORIG/__reset" -H "Authorization: Bearer $TO"
curl -s -m 5 -o /dev/null -X POST "$GEM/__reset"  -H "Authorization: Bearer $TG"
printf '\033[2m(reset en los dos)\033[0m\n'
paso "PING;64"
paso "ALTA;Lucia;83"
paso "ALTA;Lucia;82"
paso "ALTA;Mateo;3"
paso "DEPOSITO;AC-0001;250000;86"
paso "CONSULTA;AC-0001;14"
paso "TRANSFER;AC-0001;AC-0002;120000;55"
paso "SALDOS;AC-0001;38"
paso "TOTAL;22"
unset TO TG
