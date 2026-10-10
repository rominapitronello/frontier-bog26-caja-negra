"""verificar_spec: la cadena de evidencia de spec.md, comprobada contra el log.

cada fila de spec.md es `| ID | comportamiento | evidencia | confianza |`, y la evidencia son ids de
experimentos.jsonl (sueltos o rangos: `16, 25`, `1003–1183`). esta herramienta:

    python3 herramientas/verificar_spec.py            # revisa todas las filas: ¿cada id citado existe en el log?
    python3 herramientas/verificar_spec.py EN-02      # muestra el comportamiento y las líneas del log que lo prueban

sirve para quien evalúa (humano o modelo): cualquier afirmación de la spec se puede rastrear a pedidos reales.
solo biblioteca estándar; no llama a ningún servicio.
"""
import json, re, sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
FILA = re.compile(r"^\|\s*([A-Z]{2}-\d+[a-z]?)\s*\|(.*)\|\s*([^|]*)\|\s*([^|]*)\|\s*$")
RANGO = re.compile(r"(\d+)\s*[–-]\s*(\d+)")

def filas_spec():
    for linea in (RAIZ / "spec.md").read_text(encoding="utf-8").splitlines():
        m = FILA.match(linea)
        if m:
            ident, comp, evid, conf = (x.strip() for x in m.groups())
            yield ident, comp, evid, conf

def ids_citados(evidencia):
    ids, resto = set(), RANGO.sub(" ", evidencia)
    for a, b in RANGO.findall(evidencia):
        a, b = int(a), int(b)
        if a <= b:
            ids.update(range(a, b + 1))
    ids.update(int(n) for n in re.findall(r"\b\d+\b", resto))
    return ids

def log():
    reg = {}
    for l in (RAIZ / "experimentos.jsonl").read_text(encoding="utf-8").splitlines():
        if l.strip():
            r = json.loads(l)
            reg[r["id"]] = r
    return reg

def main():
    reg = log()
    filas = list(filas_spec())
    if len(sys.argv) > 1:
        buscado = sys.argv[1]
        for ident, comp, evid, conf in filas:
            if ident == buscado:
                print(f"{ident} [{conf}] {comp}\nevidencia: {evid}\n")
                for i in sorted(ids_citados(evid))[:40]:
                    r = reg.get(i)
                    if r is None:
                        print(f"  {i}: NO EXISTE EN EL LOG"); continue
                    print(f"  {i} · {r.get('seq')} · {json.dumps(r.get('request'), ensure_ascii=False)[:70]}"
                          f" → {r.get('status')} {json.dumps(r.get('response'), ensure_ascii=False)[:90]}")
                return
        sys.exit(f"no hay una fila {buscado} en spec.md")
    sin_evidencia, rotas, conf = [], [], {}
    for ident, comp, evid, c in filas:
        k = c.replace("*", "").split()[0] if c else "—"
        conf[k] = conf.get(k, 0) + 1
        ids = ids_citados(evid)
        if not ids:
            sin_evidencia.append((ident, c, evid))
        faltan = sorted(i for i in ids if i not in reg)
        if faltan:
            rotas.append((ident, faltan[:5]))
    print(f"spec.md: {len(filas)} comportamientos · log: {len(reg)} líneas")
    print("confianza: " + ", ".join(f"{k} {v}" for k, v in sorted(conf.items())))
    print(f"sin ids del log: {len(sin_evidencia)}" + ("".join(f"\n  {i} [{c}] {e[:60]}" for i, c, e in sin_evidencia)))
    print(f"citas a ids que no existen: {len(rotas)}" + ("".join(f"\n  {i}: {f}" for i, f in rotas)))
    sys.exit(1 if rotas else 0)

if __name__ == "__main__":
    main()
