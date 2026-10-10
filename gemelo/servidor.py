"""el gemelo: responde como el original, sin llamarlo nunca (DISENO.md).

    GEMELO_TOKEN=<token del equipo> PORT=8080 python3 gemelo/servidor.py

un proceso, un estado en memoria (D5). lo tabular vive en gemelo/modelo.json (D4); aquí está la lógica
con estado y el orden en que se evalúan los errores (D3), que es el orden observado en el log:
ruta → token → detenido (HALT) → tamaño → json → m → segmentos → control (no en PING) → comando → aridad
→ reglas del comando.
solo biblioteca estándar, python 3.9+.
"""
import json, os, re, sys, threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlsplit

AQUI = os.path.dirname(os.path.abspath(__file__))
M = json.load(open(os.path.join(AQUI, "modelo.json"), encoding="utf-8"))


class Respuesta(Exception):
    def __init__(self, status, cuerpo):
        self.status, self.cuerpo = status, cuerpo


def error(codigo, **extra):
    status, mensaje = M["errores"][codigo]
    return Respuesta(status, {"error": codigo, "mensaje": mensaje, **extra})


# ---- integridad: el control (S2) ----
def control_esperado(cuerpo_sin_control):
    c = M["control"]
    r = 0
    for ch in cuerpo_sin_control:
        if ch.isascii() and ch.isdigit():
            ds = ch
        elif ch.isascii() and ch.isalpha():
            ds = str(ord(ch.upper()) - 64)
        else:
            continue  # ';', '-', espacios, letras no ascii: no cuentan (44-47, 264-265)
        for d in ds:
            r = (r * 10 + int(d)) % c["modulo"]
    return str(c["resta"] - (r * c["multiplicador"]) % c["modulo"])


def distancia(a, b):
    prev = list(range(len(b) + 1))
    for i, x in enumerate(a, 1):
        cur = [i]
        for j, y in enumerate(b, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (x != y)))
        prev = cur
    return prev[-1]


def sugerencia(cmd):
    s = M["sugerencia"]
    mejores = sorted((distancia(cmd, k), k) for k in s["candidatos"])
    d, k = mejores[0]
    return k if d <= s["distancia_max"] else None


class Banco:
    """el estado de un token: cuentas, operaciones y si está detenido (HALT)."""

    def __init__(self):
        self.cuentas = {}       # id → saldo
        self.titular = {}       # id → nombre del alta (el límite no aplica entre cuentas del mismo nombre)
        self.fallas = {}        # id → transferencias seguidas rechazadas por límite o saldo (3 bloquean)
        self.ops = {}           # id → {"tipo", "monto", "cuentas", "anulada"}
        self.detenido = False

    def cuenta(self, i):
        if i not in self.cuentas:
            raise error("E401")
        return i

    def nueva_op(self, tipo, monto, cuentas):
        oid = M["ids"]["operacion"].format(len(self.ops) + 1)
        self.ops[oid] = {"tipo": tipo, "monto": monto, "cuentas": cuentas, "anulada": False}
        return {"status": "recieved", "operacionId": oid}  # sic: "recieved" (ejemplo 6)

    def monto(self, texto):
        if not re.fullmatch(M["monto"]["formato"], texto):
            raise error("E303")
        return int(texto)

    def mensaje(self, m):
        segs = m.split(";")
        if len(segs) < 2:
            raise error("E103")
        if any(s == "" for s in segs):
            raise error("E104")
        cmd = segs[0].upper()
        if cmd not in M["sin_control"]:         # PING no valida el control (39-40)
            ctrl = segs[-1]
            if not re.fullmatch(M["control"]["formato"], ctrl):
                raise error("E201")
            if ctrl != control_esperado(";".join(segs[:-1])):
                raise error("E202")
        if cmd not in M["comandos"]:
            s = sugerencia(cmd)
            raise error("E301", **({"sugerencia": s} if s else {}))
        args = segs[1:-1]
        if len(args) != M["comandos"][cmd]:
            raise error("E302")
        return getattr(self, "cmd_" + cmd.lower())(*args)

    def cmd_ping(self):
        return Respuesta(200, {"pong": True})

    def cmd_alta(self, nombre):
        cid = M["ids"]["cuenta"].format(len(self.cuentas) + 1)
        self.cuentas[cid] = 0
        self.titular[cid] = nombre
        self.fallas[cid] = 0
        return Respuesta(201, {"cuentaId": cid})

    def cmd_consulta(self, cid):
        return Respuesta(200, {"cuenta_id": self.cuenta(cid), "saldo": self.cuentas[cid]})

    def cmd_deposito(self, cid, monto):
        n = self.monto(monto)   # E303 antes que E401 (218)
        self.cuenta(cid)
        self.cuentas[cid] += n
        self.fallas[cid] = 0    # un depósito desbloquea (885-886) y reinicia el conteo (926-928)
        return Respuesta(200, self.nueva_op("deposito", n, [cid]))

    def cmd_transfer(self, origen, destino, monto):
        n = self.monto(monto)   # E303 antes que E304 (220)
        if origen == destino:   # E304 antes que E401 (219)
            raise error("E304")
        self.cuenta(origen); self.cuenta(destino)
        if self.fallas[origen] >= M["bloqueo_tras_fallas"]:   # después de E303/E304/E401 (881-883)
            raise error("E510")
        if self.titular[origen] != self.titular[destino] and n > M["limite_transferencia"]:
            self.fallas[origen] += 1            # el límite va antes que el saldo (766, 816)
            raise error("E506")
        if self.cuentas[origen] < n:
            self.fallas[origen] += 1
            raise error("E507")
        self.fallas[origen] = 0
        self.cuentas[origen] -= n
        self.cuentas[destino] += n
        return Respuesta(200, self.nueva_op("transfer", n, [origen, destino]))

    def cmd_anula(self, oid):
        op = self.ops.get(oid)
        if op is None:
            raise error("E402")
        if op["anulada"]:
            return Respuesta(200, {"ok": False, "motivo": "ya anulada"})
        if op["tipo"] == "deposito":            # puede dejar el saldo negativo (116-117)
            self.cuentas[op["cuentas"][0]] -= op["monto"]
        else:                                    # el destino puede quedar negativo (228-230)
            o, d = op["cuentas"]
            self.cuentas[o] += op["monto"]
            self.cuentas[d] -= op["monto"]
        op["anulada"] = True
        return Respuesta(200, {"ok": True, "anulada": oid})

    def cmd_halt(self, confirmacion):
        if confirmacion != M["halt_confirmacion"]:
            raise error("E520")
        self.detenido = True
        raise error("E599")


ESTADO = {"banco": Banco(), "x_req": 0}
CANDADO = threading.Lock()
TOKEN = os.environ.get("GEMELO_TOKEN", "").strip()   # un salto de línea pegado en la variable dejaría todo en 401


class Manejador(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"
    server_version = "gemelo"
    sys_version = ""

    def log_message(self, fmt, *args):
        pass

    def responder(self, r, x_req=None):
        datos = json.dumps(r.cuerpo, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
        self.send_response(r.status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(datos)))
        if x_req is not None:
            self.send_header("X-Req", str(x_req))
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(datos)

    def atender(self):
        largo = int(self.headers.get("Content-Length") or 0)
        crudo = self.rfile.read(largo) if largo > 0 else b""
        ruta = urlsplit(self.path).path            # la query string se ignora (62)
        destino = M["rutas"].get(f"{self.command} {ruta}")
        x_req = None
        with CANDADO:
            try:
                if destino is None:                 # la ruta va antes que el token (59)
                    raise error("E404")
                if self.headers.get("Authorization") != f"Bearer {TOKEN}":
                    raise error("E001")
                if destino == "health":
                    raise Respuesta(200, {"ok": True})
                if destino == "reset":
                    ESTADO["banco"] = Banco()
                    raise Respuesta(200, {"ok": True})
                ESTADO["x_req"] += 1
                x_req = ESTADO["x_req"]
                if ESTADO["banco"].detenido:            # antes que el tamaño, el json y el mensaje (720-726)
                    raise error("E599")
                if len(crudo) > M["cuerpo_max_bytes"]:   # después del token (712), antes del json (713)
                    raise error("E101")
                try:
                    cuerpo = json.loads(crudo.decode("utf-8"))
                except (ValueError, UnicodeDecodeError):
                    raise error("E100")
                if not isinstance(cuerpo, dict) or not isinstance(cuerpo.get("m"), str):
                    raise error("E102")
                raise ESTADO["banco"].mensaje(cuerpo["m"])
            except Respuesta as r:
                self.responder(r, x_req)

    do_GET = do_POST = do_PUT = do_DELETE = do_PATCH = do_HEAD = do_OPTIONS = atender


def main():
    if not TOKEN:
        sys.exit("gemelo: falta GEMELO_TOKEN (el token del equipo); sin él respondería 401 a todo")
    puerto = int(os.environ.get("PORT", "8080"))
    srv = ThreadingHTTPServer(("0.0.0.0", puerto), Manejador)
    print(f"gemelo escuchando en :{puerto}", flush=True)
    srv.serve_forever()


if __name__ == "__main__":
    main()
