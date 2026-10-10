"""filas_v2: que cada fila de spec.md tenga evidencia de la versión 2 (pedido de romina, 16:3x bog).

    python3 herramientas/filas_v2.py                 # informa: qué filas tienen v2, cuáles se cubren solas, qué falta repetir
    python3 herramientas/filas_v2.py --casos SALIDA  # además escribe las secuencias a repetir (formato de oraculo.py)
    python3 herramientas/filas_v2.py --aplicar       # agrega «v2: ids» a la evidencia de cada fila que lo tenga

una fila tiene evidencia de v2 si cita un id desde V2_DESDE (el primer pedido después del cambio, 4622). si no, se
busca una: (1) una **repetición exacta** de alguna de sus citas hecha en v2 (hipótesis «repetición exacta de N»), o
(2) el **mismo paso del centinela** en la última vuelta completa de v2. si la respuesta de v2 es la misma, la fila
vale en v2 con ese id; si es distinta, la fila cambió con el incidente y se informa para corregirla a mano. lo que
no se cubre así se repite: una secuencia por fila (la más corta de las que cita), con seq «v2-fila-<seq vieja>».
"""
import argparse, json, os, re, sys
RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
V2_DESDE = 4622

def leer_log():
    return [json.loads(l) for l in open(os.path.join(RAIZ, "experimentos.jsonl"), encoding="utf-8")]

def filas_spec(texto):
    out = []
    for n, l in enumerate(texto.split("\n")):
        m = re.match(r"^\| ([A-Z]{2}-\d+[a-z]?) \|", l)
        if m:
            celdas = [c.strip() for c in l.strip().strip("|").split(" | ")]
            out.append({"n": n, "id": m.group(1), "evidencia": celdas[-2], "confianza": celdas[-1], "linea": l})
    return out

def ids_de(evidencia):
    ids = set()
    for a, b in re.findall(r"(\d+)\s*[–-]\s*(\d+)|(?<![\w.])(\d+)(?![\w.])", evidencia.replace("—", " ")) and \
            re.findall(r"(\d+)(?:\s*[–-]\s*(\d+))?", evidencia):
        a = int(a); b = int(b) if b else a
        if b - a <= 2000:
            ids.update(range(a, b + 1))
    return ids

def clave(r):
    return (r["status"], json.dumps(r["response"], sort_keys=True, ensure_ascii=False))

def mapa_v2(log):
    """id viejo → id de v2 que lo repite exacto (repeticiones y pasos del centinela)."""
    por_id = {r["id"]: r for r in log}
    m = {}
    for r in log:
        if r["id"] >= V2_DESDE:
            x = re.search(r"repetición exacta de (\\d+|\d+)", r.get("hipotesis", ""))
            if x:
                m.setdefault(int(x.group(1)), r["id"])
    vueltas = {}
    for r in log:
        if str(r["seq"]).startswith("centinela-"):
            vueltas.setdefault(r["seq"], []).append(r)
    largo = max(len(v) for v in vueltas.values())
    v2 = [v for v in vueltas.values() if v[0]["id"] >= V2_DESDE and len(v) == largo]
    if v2:
        ultima = v2[-1]
        for v in vueltas.values():
            if v[0]["id"] < V2_DESDE and len(v) == largo:
                for a, b in zip(v, ultima):
                    m.setdefault(a["id"], b["id"])
    return m, por_id

def rangos(ids):
    ids = sorted(ids); out = []; i = 0
    while i < len(ids):
        j = i
        while j + 1 < len(ids) and ids[j + 1] == ids[j] + 1:
            j += 1
        out.append(f"{ids[i]}–{ids[j]}" if j > i + 1 else (f"{ids[i]}, {ids[j]}" if j == i + 1 else f"{ids[i]}"))
        i = j + 1
    return ", ".join(out)

def main():
    a = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    a.add_argument("--casos"); a.add_argument("--aplicar", action="store_true")
    x = a.parse_args()
    log = leer_log(); mapa, por_id = mapa_v2(log)
    ruta = os.path.join(RAIZ, "spec.md"); texto = open(ruta, encoding="utf-8").read()
    filas = filas_spec(texto)
    ya, cubre, cambia, falta, sin = [], {}, {}, {}, []
    for f in filas:
        ids = {i for i in ids_de(f["evidencia"]) if i in por_id}
        if not ids:
            sin.append(f["id"]); continue
        if any(i >= V2_DESDE for i in ids):
            ya.append(f["id"]); continue
        pares = [(i, mapa[i]) for i in sorted(ids) if i in mapa]
        iguales = [(i, j) for i, j in pares if clave(por_id[i]) == clave(por_id[j])]
        if iguales:
            cubre[f["id"]] = sorted({j for _, j in iguales})[:6]
        elif pares:
            cambia[f["id"]] = pares[:3]
        else:
            seqs = {}
            for i in ids:
                s = por_id[i]["seq"]
                if not str(s).startswith("centinela-"):
                    seqs[s] = sum(1 for r in log if r["seq"] == s)
            falta[f["id"]] = min(seqs.items(), key=lambda kv: kv[1]) if seqs else None
    print(f"filas: {len(filas)} · ya citan v2: {len(ya)} · se cubren con lo ya repetido: {len(cubre)} · "
          f"cambiaron en v2 (a mano): {len(cambia)} · sin ids del log: {len(sin)} · falta repetir: {len(falta)}")
    for k, v in cambia.items():
        i, j = v[0]
        print(f"  CAMBIA {k}: {i} {clave(por_id[i])[0]} → {j} {clave(por_id[j])[0]} {clave(por_id[j])[1][:90]}")
    seqs = {}
    for k, v in falta.items():
        if v: seqs.setdefault(v[0], (v[1], []))[1].append(k)
        else: print(f"  SIN SECUENCIA {k}")
    costo = sum(n for n, _ in seqs.values())
    print(f"secuencias a repetir: {len(seqs)}, ~{costo} pedidos")
    for s, (n, fs) in sorted(seqs.items(), key=lambda kv: kv[1][0]):
        print(f"  {s} ({n}): {', '.join(fs)}")
    if x.casos:
        out = []
        for s in seqs:
            ls = [r for r in log if r["seq"] == s and not r.get("borde_railway")]
            if ls and ls[0].get("ruta") == "/__reset":
                ls = ls[1:]
            for r in ls:
                c = {k: r[k] for k in ("request", "status", "response", "cuerpo", "cuerpo_hex", "headers", "auth", "metodo", "ruta") if k in r}
                c.update(id=r["id"], seq=f"v2-fila-{s}",
                         hipotesis=f"spec en v2 (romina 16:3x): repetición exacta de {r['id']} ({s}, v1: {r['status']})")
                out.append(c)
        open(x.casos, "w", encoding="utf-8").write("".join(json.dumps(c, ensure_ascii=False) + "\n" for c in out))
        print(f"→ {x.casos}: {len(out)} pedidos en {len(seqs)} secuencias")
    if x.aplicar:
        L = texto.split("\n")
        for f in filas:
            if f["id"] in cubre:
                celdas = f["linea"].strip().strip("|").split(" | ")
                celdas[-2] = celdas[-2].strip() + f"; v2: {rangos(cubre[f['id']])}"
                L[f["n"]] = "| " + " | ".join(c.strip() for c in celdas) + " |"
        open(ruta, "w", encoding="utf-8").write("\n".join(L))
        print(f"spec.md: {len(cubre)} filas con «v2: ids» agregados")

if __name__ == "__main__":
    main()
