"""centinela: repite contra el original una secuencia canónica y avisa si algo cambió (DISENO.md § 7).

    python3 herramientas/centinela.py            # una vuelta: reset + 31 pedidos, todo al log (seq centinela-HHMM)

compara cada vuelta con dos cosas:
  1. la vuelta anterior del centinela en el log: **una repetición exacta que cambia acredita un cambio** del original.
  2. el gemelo (levantado aquí mismo, en un puerto local): si difiere del original, el gemelo tiene un error
     o el original cambió en algo que el gemelo no sabe.
imprime una línea por vuelta: «centinela HH:MM sin cambios» o qué cambió, con los ids del log. sale con 3 si
el original cambió y con 4 si solo el gemelo difiere. toma el turno del token (lote.turno): no pisa la exploración.
"""
import json, os, socket, sys, tempfile, threading, time
AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(AQUI)
sys.path.insert(0, AQUI); sys.path.insert(0, RAIZ)
from lote import correr, turno
from control import control

def c(b):
    return f"{b};{control(b)}"

def relleno(m, n):
    base = json.dumps({"m": m}, ensure_ascii=False)
    return base[:-1] + " " * (n - len(base.encode())) + "}"

J = [["Content-Type", "application/json"]]
PASOS = [
    {"m": c("PING"), "hipotesis": "centinela PI-01"},
    {"m": c("ALTA;Lucia"), "hipotesis": "centinela AL-01"},
    {"m": c("ALTA;Mateo"), "hipotesis": "centinela AL-01"},
    {"m": c("CONSULTA;AC-0001"), "hipotesis": "centinela CO-01"},
    {"m": c("DEPOSITO;AC-0001;250000"), "hipotesis": "centinela DE-01"},
    {"m": c("TRANSFER;AC-0001;AC-0002;100000"), "hipotesis": "centinela TR-01, TR-06 (100000 pasa)"},
    {"m": c("TRANSFER;AC-0001;AC-0002;100001"), "hipotesis": "centinela TR-06 (límite)"},
    {"m": c("TRANSFER;AC-0002;AC-0001;200000"), "hipotesis": "centinela TR-07 (saldo antes que límite)"},
    {"m": c("TRANSFER;AC-0001;AC-0001;5"), "hipotesis": "centinela TR-03"},
    {"m": c("DEPOSITO;AC-0001;0100"), "hipotesis": "centinela DE-02"},
    {"m": c("CONSULTA;AC-0009"), "hipotesis": "centinela CO-02"},
    {"m": c("ANULA;OP-0002"), "hipotesis": "centinela AN-01, AN-03"},
    {"m": c("ANULA;OP-0002"), "hipotesis": "centinela AN-04"},
    {"m": c("ANULA;OP-0099"), "hipotesis": "centinela AN-05"},
    {"m": c("CONSULTA;AC-0002"), "hipotesis": "centinela AN-03 (destino de vuelta a 0)"},
    {"m": c("HELP"), "hipotesis": "centinela DC-02 (sugerencia HALT)"},
    {"m": c("ALTA;Lucia;Gomez"), "hipotesis": "centinela CM-02"},
    {"m": "CONSULTA;AC-0001;XX", "hipotesis": "centinela IN-03"},
    {"m": "CONSULTA;AC-0001;15", "hipotesis": "centinela IN-04 (14 es el válido)"},
    {"m": "CONSULTA;;99", "hipotesis": "centinela IN-02"},
    {"m": "CONSULTA", "hipotesis": "centinela IN-01"},
    {"metodo": "POST", "ruta": "/msg", "cuerpo": "hola", "headers": J, "hipotesis": "centinela EN-09"},
    {"metodo": "POST", "ruta": "/msg", "cuerpo": "{}", "headers": J, "hipotesis": "centinela EN-10"},
    {"metodo": "GET", "ruta": "/no-existe", "hipotesis": "centinela EN-01"},
    {"metodo": "POST", "ruta": "/msg", "cuerpo": json.dumps({"m": c("PING")}), "headers": J, "auth": "sin token",
     "hipotesis": "centinela EN-05"},
    {"metodo": "POST", "ruta": "/msg", "cuerpo": relleno(c("PING"), 8193), "headers": J, "hipotesis": "centinela EN-12"},
    {"m": c("ANULA;OP-0001"), "hipotesis": "centinela AN-02"},
    {"m": c("CONSULTA;AC-0001"), "hipotesis": "centinela AN-02 (saldo tras anular)"},
    {"m": c("HALT;SI"), "hipotesis": "centinela HA-01"},
    {"m": c("HALT;1"), "hipotesis": "centinela HA-02"},
    {"m": c("PING"), "hipotesis": "centinela HA-03"},
]

def clave(r):
    return (r["status"], json.dumps(r["response"], sort_keys=True, ensure_ascii=False))

def anterior(log):
    """las líneas de la última vuelta completa del centinela en el log, en orden."""
    vueltas = {}
    if os.path.exists(log):
        for l in open(log, encoding="utf-8"):
            r = json.loads(l)
            if str(r.get("seq", "")).startswith("centinela-"):
                vueltas.setdefault(r["seq"], []).append(r)
    completas = [v for v in vueltas.values() if len(v) == len(PASOS) + 1]
    return completas[-1] if completas else None

def contra_gemelo(lineas):
    """corre las mismas líneas contra el gemelo (en un hilo, puerto libre) con la regla del juez."""
    tok = "centinela-local"
    os.environ["GEMELO_TOKEN"] = tok
    sys.path.insert(0, os.path.join(RAIZ, "gemelo"))
    import servidor, medir
    servidor.TOKEN = tok
    s = socket.socket(); s.bind(("127.0.0.1", 0)); puerto = s.getsockname()[1]; s.close()
    srv = servidor.ThreadingHTTPServer(("127.0.0.1", puerto), servidor.Manejador)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    with tempfile.NamedTemporaryFile("w", suffix=".jsonl", delete=False, encoding="utf-8") as f:
        for r in lineas:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    try:
        inf = medir.medir(medir.leer_casos(f.name), medir.preparar_url(f"http://127.0.0.1:{puerto}"), token=tok)
    finally:
        srv.shutdown(); os.unlink(f.name)
    return inf["resultados"][0]["primera_diferencia"]

def main():
    base, token = os.environ.get("ORIGINAL_URL"), os.environ.get("ORIGINAL_TOKEN")
    if not base or not token:
        sys.exit("centinela: faltan ORIGINAL_URL u ORIGINAL_TOKEN")
    os.chdir(RAIZ)
    log = "experimentos.jsonl"
    hora = time.strftime("%H%M")
    seq = f"centinela-{hora}"
    with turno():
        previa = anterior(log)
        pasos = [{"reset": True, "hipotesis": "centinela: reset antes de la secuencia canónica"}] + PASOS
        nuevas = correr(pasos, seq, base, token, log=log, eco=False)
    cambios = []
    if previa:
        for a, b in zip(previa, nuevas):
            if clave(a) != clave(b):
                cambios.append(f"id {b['id']} (antes {a['id']}): {a['status']} {json.dumps(a['response'], ensure_ascii=False)} → "
                               f"{b['status']} {json.dumps(b['response'], ensure_ascii=False)}")
    dif = contra_gemelo(nuevas)
    ids = f"{nuevas[0]['id']}-{nuevas[-1]['id']}"
    if cambios:
        print(f"centinela {hora} CAMBIO DEL ORIGINAL ({ids}, comparado con {previa[0]['seq']}): " + " | ".join(cambios), flush=True)
    if dif:
        print(f"centinela {hora} GEMELO DIFIERE en id {dif['id']}: esperado {json.dumps(dif['esperado'], ensure_ascii=False)} "
              f"obtenido {json.dumps(dif['obtenido'], ensure_ascii=False)}", flush=True)
    if not cambios and not dif:
        print(f"centinela {hora} sin cambios ({ids}{', primera vuelta' if not previa else ''}); el gemelo calza", flush=True)
    sys.exit(3 if cambios else (4 if dif else 0))

if __name__ == "__main__":
    main()
