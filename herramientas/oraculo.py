"""oráculo: corre un archivo de casos (formato de medir.py) contra el original y compara tres cosas.

    python3 herramientas/oraculo.py evals/sol-03.jsonl

por cada secuencia: POST /__reset y sus pedidos contra el original, todo anotado en experimentos.jsonl
(seq = la del caso). después:
  1. la predicción del caso contra lo que respondió el original → donde difieren, la spec dice mal o no dice.
  2. el gemelo (levantado aquí, puerto local) contra lo que respondió el original → donde difieren, el gemelo
     tiene un error.
imprime un resumen y escribe el detalle en <casos>.resultado.json. toma el turno del token (lote.turno).
"""
import json, os, sys, collections
AQUI = os.path.dirname(os.path.abspath(__file__)); RAIZ = os.path.dirname(AQUI)
sys.path.insert(0, AQUI); sys.path.insert(0, RAIZ)
from lote import correr, turno
import centinela

J = [["Content-Type", "application/json"]]

def paso(caso):
    metodo = caso.get("metodo", "POST").upper()
    ruta = caso.get("ruta", "/msg")
    if isinstance(caso.get("cuerpo"), str):
        cuerpo = caso["cuerpo"]
    elif metodo in ("GET", "HEAD") or caso.get("request") is None:
        cuerpo = None
    else:
        cuerpo = json.dumps(caso["request"], ensure_ascii=False)
    p = {"metodo": metodo, "ruta": ruta, "cuerpo": cuerpo, "headers": J,
         "hipotesis": f"{caso['seq']} caso {caso['id']} ({', '.join(caso.get('spec', []))}): {caso.get('hipotesis', '')}"}
    if caso.get("auth"):
        p["auth"] = caso["auth"]
    return p

def igual(st1, r1, st2, r2):
    return st1 == st2 and r1 == r2

def main():
    casos_f = sys.argv[1]
    base, token = os.environ.get("ORIGINAL_URL"), os.environ.get("ORIGINAL_TOKEN")
    if not base or not token:
        sys.exit("oráculo: faltan ORIGINAL_URL u ORIGINAL_TOKEN")
    os.chdir(RAIZ)
    casos = [json.loads(l) for l in open(casos_f, encoding="utf-8") if l.strip()]
    seqs = collections.OrderedDict()
    for cc in casos:
        seqs.setdefault(cc["seq"], []).append(cc)
    reales = {}
    with turno():
        for seq, cs in seqs.items():
            pasos = [{"reset": True, "hipotesis": f"{seq}: reset (oráculo {os.path.basename(casos_f)})"}] + [paso(cc) for cc in cs]
            r = correr(pasos, seq, base, token, eco=False)
            reales[seq] = r
    prediccion, lineas = [], []
    for seq, cs in seqs.items():
        r = reales[seq]
        lineas += r
        for cc, real in zip(cs, r[1:]):
            if not igual(cc["status"], cc["response"], real["status"], real["response"]):
                prediccion.append({"seq": seq, "caso": cc["id"], "log": real["id"], "pedido": cc.get("request"),
                                   "predicho": [cc["status"], cc["response"]], "original": [real["status"], real["response"]],
                                   "spec": cc.get("spec"), "ambiguo": cc.get("ambiguo")})
    gemelo = []
    for seq in seqs:
        dif = centinela.contra_gemelo(reales[seq])
        if dif:
            gemelo.append({"seq": seq, **dif})
    ok_seq = sum(1 for seq in seqs if not any(p["seq"] == seq for p in prediccion))
    print(f"oráculo {casos_f}: {len(casos)} pedidos en {len(seqs)} secuencias, log {lineas[0]['id']}-{lineas[-1]['id']}")
    print(f"  predicción = original en {ok_seq}/{len(seqs)} secuencias; {len(prediccion)} pedidos difieren")
    print(f"  gemelo = original en {len(seqs) - len(gemelo)}/{len(seqs)} secuencias")
    for p in prediccion:
        print(f"  PREDICCIÓN {p['seq']} caso {p['caso']} (log {p['log']}, {', '.join(p['spec'] or [])}): {json.dumps(p['pedido'], ensure_ascii=False)} "
              f"predicho {p['predicho'][0]} {json.dumps(p['predicho'][1], ensure_ascii=False)} · original {p['original'][0]} {json.dumps(p['original'][1], ensure_ascii=False)}"
              + (" [marcado ambiguo]" if p['ambiguo'] else ""))
    for g in gemelo:
        print(f"  GEMELO {g['seq']} log {g['id']}: esperado {json.dumps(g['esperado'], ensure_ascii=False)} obtenido {json.dumps(g['obtenido'], ensure_ascii=False)}")
    json.dump({"prediccion": prediccion, "gemelo": gemelo}, open(casos_f.rsplit('.', 1)[0] + ".resultado.json", "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)

if __name__ == "__main__":
    main()
