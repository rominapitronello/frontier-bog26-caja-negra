"""sonda: manda un pedido http exacto al servicio y lo deja en el log, tal cual vino.

una línea del log = un experimento. su id es la cita que usa la spec.
se usa http.client y no una librería de alto nivel para no tocar lo que se observa:
los headers quedan en el orden y con las mayúsculas en que llegaron.

    python3 herramientas/sonda.py --seq s1 --hipotesis '...' --m 'PING;64'          # POST /msg
    python3 herramientas/sonda.py --seq s1 --hipotesis '...' GET /otra [--sin-token] [--cuerpo '...']

escribe experimentos.jsonl con el formato del material (id, seq, x_req, hipotesis, request, status,
response, conclusion) y, aparte, experimentos_crudo.jsonl con los headers completos.

la url base y el token salen de variables de entorno (ORIGINAL_URL, ORIGINAL_TOKEN) si no se pasan;
el token nunca se escribe en el log: queda como <token> o <otro-token>.
"""
import argparse, http.client, json, os, sys, time, urllib.parse

def pedir(base, metodo, ruta, headers=(), cuerpo=None, timeout=15):
    u = urllib.parse.urlsplit(base)
    Con = http.client.HTTPSConnection if u.scheme == "https" else http.client.HTTPConnection
    c = Con(u.hostname, u.port, timeout=timeout)
    prefijo = u.path.rstrip("/")
    c.putrequest(metodo, prefijo + ruta, skip_accept_encoding=True)
    for k, v in headers:
        c.putheader(k, v)
    datos = cuerpo.encode() if isinstance(cuerpo, str) else cuerpo
    if datos is not None and not any(k.lower() == "content-length" for k, _ in headers):
        c.putheader("Content-Length", str(len(datos)))
    c.endheaders(datos)
    t0 = time.monotonic()
    r = c.getresponse()
    crudo = r.read()
    ms = round((time.monotonic() - t0) * 1000)
    c.close()
    try:
        texto, binario = crudo.decode("utf-8"), False
    except UnicodeDecodeError:
        texto, binario = crudo.hex(), True
    return {"status": r.status, "reason": r.reason, "headers": r.getheaders(),
            "cuerpo": texto, "cuerpo_hex": binario, "ms": ms}

def tapar(headers, token):
    out = []
    for k, v in headers:
        if token and token in v:
            v = v.replace(token, "<token>")
        out.append([k, v])
    return out

def anotar(log, registro):
    """agrega una línea al log con el siguiente id y lo devuelve: el id es la cita de la spec."""
    n = 0
    if os.path.exists(log):
        with open(log, encoding="utf-8") as f:
            for l in f:
                if l.strip():
                    n = max(n, json.loads(l)["id"])
    registro = {"id": n + 1, **registro}
    with open(log, "a", encoding="utf-8") as f:
        f.write(json.dumps(registro, ensure_ascii=False) + "\n")
    return n + 1

def _no_json(constante):
    raise ValueError(constante)

def como_json(texto):
    """el cuerpo como json estricto; si no lo es (incluidos NaN e Infinity), el texto tal cual."""
    try:
        return json.loads(texto, parse_constant=_no_json)
    except (ValueError, TypeError):
        return texto

def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("metodo", nargs="?", default="POST"); p.add_argument("ruta", nargs="?", default="/msg")
    p.add_argument("--m", help="atajo: manda {\"m\": M} por POST /msg")
    p.add_argument("--base", default=os.environ.get("ORIGINAL_URL"))
    p.add_argument("--cuerpo"); p.add_argument("-H", dest="headers", action="append", default=[])
    p.add_argument("--sin-token", action="store_true", help="no manda Authorization")
    p.add_argument("--otro-token", help="manda este token en vez del tuyo (queda como <otro-token>)")
    p.add_argument("--log", default="experimentos.jsonl")
    p.add_argument("--crudo", default="experimentos_crudo.jsonl", help="headers completos, aparte del log del formato")
    p.add_argument("--seq", required=True, help="la secuencia: todas sus líneas van tras un mismo reset")
    p.add_argument("--hipotesis", required=True, help="qué separa este pedido")
    a = p.parse_args()
    if not a.base:
        sys.exit("sonda: falta --base u ORIGINAL_URL")
    headers_propios = bool(a.headers)
    if a.m is not None:
        a.cuerpo = json.dumps({"m": a.m}, ensure_ascii=False)
        if not any(h.lower().startswith("content-type") for h in a.headers):
            a.headers.append("Content-Type: application/json")
    token = os.environ.get("ORIGINAL_TOKEN", "")
    hs = [tuple(x.strip() for x in h.split(":", 1)) for h in a.headers]
    if a.otro_token:
        hs.insert(0, ("Authorization", f"Bearer {a.otro_token}"))
    elif not a.sin_token and token:
        hs.insert(0, ("Authorization", f"Bearer {token}"))
    r = pedir(a.base, a.metodo, a.ruta, hs, a.cuerpo)
    hdr = {k.lower(): v for k, v in r["headers"]}
    if hdr.get("x-frontier-infra"):
        print(f"infra ({hdr['x-frontier-infra']}): no es el servicio, no va al log. espera y repite.")
        sys.exit(4)
    reg = {"seq": a.seq, "x_req": hdr.get("x-req"), "hipotesis": a.hipotesis,
           "request": como_json(a.cuerpo), "status": r["status"], "response": como_json(r["cuerpo"]),
           "conclusion": ""}
    if (a.metodo, a.ruta) != ("POST", "/msg") or a.sin_token or a.otro_token or headers_propios:
        reg["metodo"], reg["ruta"] = a.metodo, a.ruta
        reg["auth"] = "sin token" if a.sin_token else ("otro token" if a.otro_token else "token propio")
    n = anotar(a.log, reg)
    with open(a.crudo, "a", encoding="utf-8") as f:
        f.write(json.dumps({"id": n, "t": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
                            "pedido_headers": tapar(hs, token), "status": r["status"], "reason": r["reason"],
                            "headers": tapar(r["headers"], token), "cuerpo": r["cuerpo"], "ms": r["ms"]},
                           ensure_ascii=False) + "\n")
    print(f"id {n}  {r['status']}  x_req={reg['x_req']}  {r['cuerpo'][:500]}")

if __name__ == "__main__":
    main()
