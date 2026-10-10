"""lote: corre una lista de pedidos contra el original y deja cada uno en el log, como la sonda.

cada línea de entrada (jsonl, por archivo o stdin) es un pedido:
    {"m": "PING;64", "hipotesis": "..."}                       # POST /msg con ese cuerpo
    {"reset": true, "hipotesis": "..."}                         # POST /__reset
    {"metodo": "GET", "ruta": "/x", "cuerpo": "...", "auth": "sin token" | "otro token" | "token propio",
     "headers": [["Content-Type", "text/plain"]], "hipotesis": "..."}

    python3 herramientas/lote.py --seq s3 pasos.jsonl [--reset] [--hipotesis-reset '...']

--reset antepone un POST /__reset (anotado en el log, como cualquier otro pedido).
el ritmo queda bajo el límite del material (10/s por token). una respuesta de la infraestructura
(X-Frontier-Infra) no va al log: se espera y se repite.
"""
import argparse, contextlib, fcntl, json, os, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sonda import pedir, tapar, como_json

# un token = un estado = un explorador a la vez (objeción de fable, fable-02 § 1): toda secuencia contra el
# original toma este turno, y el centinela y la exploración se esperan en vez de pisarse el estado.
_CANDADO = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".turno-original.lock")
_turno_tomado = 0

@contextlib.contextmanager
def turno():
    global _turno_tomado
    if _turno_tomado:
        _turno_tomado += 1
        try:
            yield
        finally:
            _turno_tomado -= 1
        return
    with open(_CANDADO, "w") as f:
        fcntl.flock(f, fcntl.LOCK_EX)
        _turno_tomado = 1
        try:
            yield
        finally:
            _turno_tomado = 0
            fcntl.flock(f, fcntl.LOCK_UN)

OTRO_TOKEN = "tok-que-no-existe-0000"

# freno (cicatriz del 10 oct, log 289-686): una búsqueda binaria mal escrita repitió el mismo pedido ~400 veces.
# el proceso se detiene si manda el mismo pedido más de REPETIDOS_MAX veces seguidas o más de TOPE en total.
REPETIDOS_MAX, TOPE = 5, int(os.environ.get("LOTE_TOPE", "400"))
_ultimo, _seguidos, _total = None, 0, 0

def _frenar(clave):
    global _ultimo, _seguidos, _total
    _seguidos = _seguidos + 1 if clave == _ultimo else 1
    _ultimo, _total = clave, _total + 1
    if _seguidos > REPETIDOS_MAX:
        sys.exit(f"lote: el mismo pedido {_seguidos} veces seguidas; me detengo (¿un bucle?)")
    if _total > TOPE:
        sys.exit(f"lote: más de {TOPE} pedidos en este proceso; me detengo (LOTE_TOPE lo sube)")

def siguiente_id(log):
    n = 0
    if os.path.exists(log):
        with open(log, encoding="utf-8") as f:
            for l in f:
                if l.strip():
                    n = max(n, json.loads(l)["id"])
    return n + 1

def correr(pasos, seq, base, token, log="experimentos.jsonl", crudo="experimentos_crudo.jsonl",
           ritmo=8.0, eco=True):
    with turno():
        return _correr(pasos, seq, base, token, log, crudo, ritmo, eco)

def _correr(pasos, seq, base, token, log, crudo, ritmo, eco):
    nid = siguiente_id(log)
    out = []
    t_ult = 0.0
    for p in pasos:
        if p.get("reset"):
            metodo, ruta, cuerpo, auth = "POST", "/__reset", p.get("cuerpo"), p.get("auth", "token propio")
            hs = [tuple(h) for h in p.get("headers", [])]
        elif "m" in p:
            metodo, ruta, auth = "POST", "/msg", p.get("auth", "token propio")
            cuerpo = json.dumps({"m": p["m"]}, ensure_ascii=False)
            hs = [tuple(h) for h in p.get("headers", [["Content-Type", "application/json"]])]
        else:
            metodo, ruta, cuerpo = p.get("metodo", "POST"), p.get("ruta", "/msg"), p.get("cuerpo")
            auth = p.get("auth", "token propio")
            hs = [tuple(h) for h in p.get("headers", [])]
        if auth == "token propio":
            hs.insert(0, ("Authorization", f"Bearer {token}"))
        elif auth == "otro token":
            hs.insert(0, ("Authorization", f"Bearer {OTRO_TOKEN}"))
        elif auth not in ("sin token",):
            hs.insert(0, ("Authorization", auth.replace("<token>", token)))  # forma rara del header, a mano
        if not p.get("reset"):
            _frenar((metodo, ruta, cuerpo, auth))
        for intento in range(6):
            espera = 1.0 / ritmo - (time.monotonic() - t_ult)
            if espera > 0:
                time.sleep(espera)
            t_ult = time.monotonic()
            try:
                r = pedir(base, metodo, ruta, hs, cuerpo)
            except Exception as e:  # red: se repite, no se anota
                print(f"red: {e!r}; repito", file=sys.stderr); time.sleep(1 + intento); continue
            hdr = {k.lower(): v for k, v in r["headers"]}
            if hdr.get("x-frontier-infra"):
                print(f"infra ({hdr['x-frontier-infra']}): espero y repito", file=sys.stderr)
                time.sleep(2 + 2 * intento); continue
            break
        else:
            sys.exit("lote: seis intentos sin respuesta del servicio; me detengo")
        reg = {"id": nid, "seq": seq, "x_req": hdr.get("x-req"), "hipotesis": p.get("hipotesis", ""),
               "request": como_json(cuerpo) if cuerpo is not None else None,
               "status": r["status"], "response": como_json(r["cuerpo"]), "conclusion": p.get("conclusion", "")}
        if cuerpo is not None and ("cuerpo" in p or not isinstance(reg["request"], dict)):
            reg["cuerpo"] = cuerpo  # el texto exacto que se mandó: "request" no distingue 'hola' de '"hola"'
        if (metodo, ruta) != ("POST", "/msg") or auth != "token propio" or "headers" in p:
            reg["metodo"], reg["ruta"], reg["auth"] = metodo, ruta, auth.replace(token, "<token>") if token else auth
            if "headers" in p:
                reg["headers"] = p["headers"]
        with open(log, "a", encoding="utf-8") as f:
            f.write(json.dumps(reg, ensure_ascii=False) + "\n")
        with open(crudo, "a", encoding="utf-8") as f:
            f.write(json.dumps({"id": nid, "t": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
                                "pedido_headers": tapar(hs, token), "status": r["status"], "reason": r["reason"],
                                "headers": tapar(r["headers"], token), "cuerpo": r["cuerpo"], "ms": r["ms"]},
                               ensure_ascii=False) + "\n")
        if eco:
            q = reg["request"]["m"] if isinstance(reg["request"], dict) and "m" in reg["request"] else f"{metodo} {ruta} {cuerpo!r}"
            print(f"{nid:5d} {r['status']} x_req={reg['x_req']}  {q}  →  {r['cuerpo'][:300]}")
        out.append(reg)
        nid += 1
    return out

def main():
    a = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    a.add_argument("pasos", nargs="?", help="jsonl de pedidos (por defecto, stdin)")
    a.add_argument("--seq", required=True)
    a.add_argument("--reset", action="store_true")
    a.add_argument("--hipotesis-reset", default="reset: la secuencia parte del estado inicial")
    a.add_argument("--base", default=os.environ.get("ORIGINAL_URL"))
    a.add_argument("--log", default="experimentos.jsonl")
    a.add_argument("--crudo", default="experimentos_crudo.jsonl")
    a.add_argument("--ritmo", type=float, default=8.0, help="pedidos por segundo (máximo del material: 10)")
    x = a.parse_args()
    token = os.environ.get("ORIGINAL_TOKEN", "")
    if not x.base or not token:
        sys.exit("lote: faltan ORIGINAL_URL u ORIGINAL_TOKEN")
    fuente = open(x.pasos, encoding="utf-8") if x.pasos else sys.stdin
    pasos = [json.loads(l) for l in fuente if l.strip()]
    if x.reset:
        pasos.insert(0, {"reset": True, "hipotesis": x.hipotesis_reset})
    correr(pasos, x.seq, x.base, token, x.log, x.crudo, min(x.ritmo, 9.5))

if __name__ == "__main__":
    main()
