#!/usr/bin/env bash
# el centinela en ciclo (incident.md): cada 15 min, y cada 5 min entre las 14:50 y las 16:40 bog.
# se arma con el monitor de claude code; imprime una línea por vuelta (o un aviso).
cd "$(dirname "$0")/.."
while true; do
  python3 herramientas/centinela.py 2>&1 | grep --line-buffered -E 'centinela|Traceback|Error|faltan'
  hm=$(TZ=America/Bogota date +%H%M)
  if [ $((10#$hm)) -ge 1450 ] && [ $((10#$hm)) -le 1640 ]; then sleep 300; else sleep 900; fi
done
