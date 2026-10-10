#!/usr/bin/env bash
# Prueba de humo del entrypoint (Ley 2). Se completa el sábado, cuando el brief diga
# cómo se invoca el entrypoint. Mientras tanto FALLA a propósito, para que nadie crea
# que hay algo verde que no existe.
set -euo pipefail

ENTRYPOINT_CMD="${ENTRYPOINT_CMD:-}"   # ej: "python main.py --input ejemplos/caso1.json"

if [ -z "$ENTRYPOINT_CMD" ]; then
  echo "smoke: ENTRYPOINT_CMD no está definido todavía. Completar este script según el brief."
  exit 1
fi

echo "smoke: corriendo -> $ENTRYPOINT_CMD"
OUT=$(eval "$ENTRYPOINT_CMD")
echo "$OUT" | head -20

# TODO sábado: chequear que la salida tenga la forma que pide el brief.
# Ejemplo: echo "$OUT" | python -c 'import json,sys; json.load(sys.stdin)'

echo "smoke: OK"
