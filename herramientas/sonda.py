"""sonda: manda un pedido http exacto al servicio y lo deja en el log, tal cual vino.

una línea del log = un experimento. el número de línea es la cita que usa la spec.
se usa http.client y no una librería de alto nivel para no tocar lo que se observa:
los headers quedan en el orden y con las mayúsculas en que llegaron.

    python3 herramientas/sonda.py --base URL GET /ruta [--cuerpo '...'] [-H 'Nombre: valor'] [--sin-token]

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
    """agrega una línea al log y devuelve su número (1-indexado): la cita."""
    n = 0
    if os.path.exists(log):
        with open(log, "rb") as f:
            n = sum(1 for _ in f)
    with open(log, "a", encoding="utf-8") as f:
        f.write(json.dumps(registro, ensure_ascii=False) + "\n")
    return n + 1

def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("metodo"); p.add_argument("ruta")
    p.add_argument("--base", default=os.environ.get("ORIGINAL_URL"))
    p.add_argument("--cuerpo"); p.add_argument("-H", dest="headers", action="append", default=[])
    p.add_argument("--sin-token", action="store_true", help="no manda Authorization")
    p.add_argument("--otro-token", help="manda este token en vez del del equipo (queda como <otro-token>)")
    p.add_argument("--log", default="log.jsonl")
    p.add_argument("--nota", default="", help="por qué se hace este experimento (hipótesis que separa)")
    a = p.parse_args()
    if not a.base:
        sys.exit("sonda: falta --base u ORIGINAL_URL")
    token = os.environ.get("ORIGINAL_TOKEN", "")
    hs = [tuple(h.split(":", 1)) for h in a.headers]
    hs = [(k.strip(), v.strip()) for k, v in hs]
    if a.otro_token:
        hs.insert(0, ("Authorization", f"Bearer {a.otro_token}"))
    elif not a.sin_token and token:
        hs.insert(0, ("Authorization", f"Bearer {token}"))
    r = pedir(a.base, a.metodo, a.ruta, hs, a.cuerpo)
    reg = {"t": time.strftime("%Y-%m-%dT%H:%M:%S%z"), "nota": a.nota,
           "pedido": {"metodo": a.metodo, "ruta": a.ruta,
                      "headers": [[k, ("Bearer <otro-token>" if a.otro_token and k == "Authorization" else v)]
                                  for k, v in tapar(hs, token)],
                      "cuerpo": a.cuerpo},
           "respuesta": {**r, "headers": tapar(r["headers"], token)}}
    linea = anotar(a.log, reg)
    print(f"log:{linea}  {r['status']} {r['reason']}  {r['ms']} ms")
    for k, v in r["headers"]:
        print(f"  {k}: {v}")
    print(r["cuerpo"][:2000])

if __name__ == "__main__":
    main()
