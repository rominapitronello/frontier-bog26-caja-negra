"""fase: después del incidente, separa en el log lo que el cambio contradice (incident.md, protocolo 2 y 5).

    python3 herramientas/fase.py --hasta 3302              # solo informa
    python3 herramientas/fase.py --hasta 3302 --marcar     # además marca "fase": "manana" en el log

toma las secuencias del log con ids ≤ --hasta (la última línea antes del cambio), sin las de borde_railway ni las
ya marcadas, y las corre contra un gemelo local con el modelo de la tarde (gemelo/modelo.json). las que difieren
son las que el cambio contradice: con --marcar, todas sus líneas llevan "fase": "manana" (la secuencia entera,
porque el estado de un paso depende de los anteriores). después comprueba que esas mismas secuencias calzan con
el modelo congelado de la mañana (gemelo/modelo-manana.json), que es contra el que las corre smoke.sh.
no toca el original.
"""
import argparse, json, os, socket, subprocess, sys, tempfile, time, http.client
AQUI = os.path.dirname(os.path.abspath(__file__)); RAIZ = os.path.dirname(AQUI)
sys.path.insert(0, AQUI); sys.path.insert(0, RAIZ)
import medir
from lote import turno

TOKEN = "fase-local"

def levantar(modelo):
    s = socket.socket(); s.bind(("127.0.0.1", 0)); puerto = s.getsockname()[1]; s.close()
    env = dict(os.environ, GEMELO_TOKEN=TOKEN, PORT=str(puerto), GEMELO_MODELO=modelo)
    proc = subprocess.Popen([sys.executable, os.path.join(RAIZ, "gemelo", "servidor.py")], env=env,
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    for _ in range(50):
        try:
            c = http.client.HTTPConnection("127.0.0.1", puerto, timeout=1)
            c.request("GET", "/health", headers={"Authorization": f"Bearer {TOKEN}"}); c.getresponse(); break
        except OSError:
            time.sleep(0.1)
    return proc, puerto

def difieren(lineas, modelo):
    """las seq (de estas líneas) que no calzan con un gemelo levantado con este modelo."""
    proc, puerto = levantar(modelo)
    with tempfile.NamedTemporaryFile("w", suffix=".jsonl", delete=False, encoding="utf-8") as f:
        for r in lineas:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    try:
        inf = medir.medir(medir.leer_casos(f.name), medir.preparar_url(f"http://127.0.0.1:{puerto}"), token=TOKEN)
    finally:
        proc.terminate(); proc.wait(); os.unlink(f.name)
    return {r["seq"]: r["primera_diferencia"] for r in inf["resultados"] if not r["pasa"]}

def main():
    a = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    a.add_argument("--hasta", type=int, required=True, help="último id del log anterior al cambio")
    a.add_argument("--marcar", action="store_true")
    a.add_argument("--tarde", default="gemelo/modelo.json", help="modelo de la tarde (por defecto, el vigente)")
    a.add_argument("--manana", default="gemelo/modelo-manana.json", help="modelo congelado de la mañana")
    x = a.parse_args()
    os.chdir(RAIZ)
    log = [json.loads(l) for l in open("experimentos.jsonl", encoding="utf-8")]
    viejas = [r for r in log if r["id"] <= x.hasta and not r.get("borde_railway") and r.get("fase") != "manana"]
    tarde = difieren(viejas, x.tarde)
    for seq, d in tarde.items():
        print(f"contradice la tarde: {seq} (primera diferencia en id {d['id']}: esperado {json.dumps(d['esperado'], ensure_ascii=False)}"
              f" · tarde {json.dumps(d['obtenido'], ensure_ascii=False)})")
    print(f"fase: {len(tarde)} secuencias de {len({r['seq'] for r in viejas})} (ids ≤ {x.hasta}) no calzan con el modelo de la tarde")
    if os.path.exists(x.manana) and tarde:
        manana = difieren([r for r in viejas if r["seq"] in tarde], x.manana)
        print(f"fase: con el modelo de la mañana calzan {len(tarde) - len(manana)} de {len(tarde)}"
              + (f"; no calzan: {', '.join(manana)}" if manana else ""))
    if x.marcar and tarde:
        with turno():                       # el centinela escribe al log: se relee y se reescribe con el candado
            marcar(set(tarde), x.hasta)

def marcar(seqs, hasta):
    log = [json.loads(l) for l in open("experimentos.jsonl", encoding="utf-8")]
    n = 0
    for r in log:
        if r["id"] <= hasta and r["seq"] in seqs and not r.get("borde_railway"):
            r["fase"] = "manana"; n += 1
    with open("experimentos.jsonl", "w", encoding="utf-8") as f:
        for r in log:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(f"fase: {n} líneas marcadas \"fase\": \"manana\"")

if __name__ == "__main__":
    main()
