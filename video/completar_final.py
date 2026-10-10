#!/usr/bin/env python3
"""Completa la grilla final SVG. Requiere un resultado y una fuente reales.

Ejemplo:
  python3 video/completar_final.py --aciertos 91 --fuente 'ESTADO.md: validación 3, 19:15 bog'
No rellena datos ausentes; sin --aciertos el SVG del repositorio queda null.
"""
import argparse
import html
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parent
IN = ROOT / "02_grilla_final_null.svg"
COL_JADE = "#2BB5A0"
COL_GRAFITO = "#3A3A4A"
PATTERN = re.compile(r'<rect x="(\d+)" y="(\d+)" width="55" height="55" rx="1" fill="none" stroke="#3A3A4A" stroke-opacity=".58" stroke-width="2"/>')

def main():
    ap = argparse.ArgumentParser(description="Genera SVG de 100 cuadrados exactos desde una medición")
    ap.add_argument("--aciertos", type=int, required=True)
    ap.add_argument("--fuente", required=True, help="Ruta/commit o registro auditable del puntaje final")
    ap.add_argument("--salida", default=str(ROOT / "02_grilla_final_medida.svg"))
    args = ap.parse_args()
    if not 0 <= args.aciertos <= 100:
        ap.error("--aciertos debe ser entero entre 0 y 100")
    if not args.fuente.strip():
        ap.error("--fuente no puede estar vacía")
    s = IN.read_text(encoding="utf-8")
    n = 0
    def fill(m):
        nonlocal n
        n += 1
        color = COL_JADE if n <= args.aciertos else COL_GRAFITO
        return f'<rect x="{m.group(1)}" y="{m.group(2)}" width="55" height="55" rx="1" fill="{color}"/>'
    s = PATTERN.sub(fill, s)
    if n != 100:
        raise RuntimeError(f"Se esperaban 100 cuadros, aparecen {n}; no se escribe nada")
    s = s.replace("null / 100", f"{args.aciertos} / 100", 1)
    s = s.replace("resultado final: null", f"resultado final: {args.aciertos}/100; {html.escape(args.fuente)}", 1)
    if "null / 100" in s or "resultado final: null" in s:
        raise RuntimeError("Quedó un null en el puntaje")
    path = pathlib.Path(args.salida)
    path.write_text(s, encoding="utf-8")
    print(f"{path}: {args.aciertos} jade + {100-args.aciertos} grafito = 100, fuente: {args.fuente}")

if __name__ == "__main__":
    main()
