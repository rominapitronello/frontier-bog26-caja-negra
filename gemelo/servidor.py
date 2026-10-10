"""el gemelo: responde como el original, sin llamarlo nunca (DISENO.md).

    GEMELO_TOKEN=<token del equipo> PORT=8080 python3 gemelo/servidor.py

un proceso, un estado en memoria (D5). lo tabular vive en gemelo/modelo.json (D4). las cuatro piezas que el
preregistro del incidente nombra (PREDICCION_INCIDENTE.md) se cambian sin tocar el resto:
  · normalización     → modelo.json "normalizacion" + normalizar()
  · orden de errores  → modelo.json "orden" (listas de pasos) + los pasos _paso_* de cada nivel
  · dígito de control → modelo.json "control" + control_esperado() y control_valido()
  · transiciones      → modelo.json "estado" (límite, bloqueo, halt, anula) + los métodos _bloqueo_* del Banco
el orden observado hoy (spec ER-20): ruta → token → detenido → tamaño → json → m → segmentos → control (no en
PING) → comando → aridad → reglas del comando. solo biblioteca estándar, python 3.9+.
"""
import json, os, re, sys, threading, time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

VERSION = "v11"   # va en el header X-Gemelo-Version (los headers no se comparan): confirma qué versión está desplegada
ARRANQUE = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())  # X-Gemelo-Arranque: delata un reinicio
AQUI = os.path.dirname(os.path.abspath(__file__))
M = json.load(open(os.environ.get("GEMELO_MODELO") or os.path.join(AQUI, "modelo.json"), encoding="utf-8"))


if hasattr(sys, "set_int_max_str_digits"):
    sys.set_int_max_str_digits(0)   # el original lee un entero de 4301 dígitos (3445); python ≥ 3.11 lo rechazaría


def _no_json(constante):
    raise ValueError(constante)


def profundidad(texto):
    """el anidamiento máximo de un json, contando el de afuera y sin mirar dentro de los strings (3464-3470)."""
    d = maximo = 0
    en_string = escape = False
    for ch in texto:
        if en_string:
            if escape:
                escape = False
            elif ch == "\\":
                escape = True
            elif ch == '"':
                en_string = False
        elif ch == '"':
            en_string = True
        elif ch in "[{":
            d += 1
            maximo = max(maximo, d)
        elif ch in "]}":
            d -= 1
    return maximo


class Respuesta(Exception):
    def __init__(self, status, cuerpo):
        self.status, self.cuerpo = status, cuerpo


def error(codigo, **extra):
    # un código nuevo encendido antes de copiar su texto no tumba el proceso: 422 y el código como texto (provisorio)
    status, mensaje = M["errores"].get(codigo, [422, codigo])
    return Respuesta(status, {"error": codigo, "mensaje": mensaje, **extra})


# ---- pieza 1: normalización ----
def normalizar(parte, texto):
    """cómo se lee una parte del mensaje antes de compararla (modelo.json "normalizacion")."""
    forma = M["normalizacion"].get(parte, "tal cual")
    if forma in ("recortar", "recortar_mayusculas"):
        texto = texto.strip()
    if forma in ("mayusculas", "recortar_mayusculas"):
        texto = texto.upper()
    elif forma == "minusculas":
        texto = texto.lower()
    return texto


# ---- pieza 3: el dígito de control (S2) ----
def control_esperado(cuerpo_sin_control):
    c = M["control"]
    r = 0
    for ch in cuerpo_sin_control:
        if ch.isascii() and ch.isdigit():
            ds = ch
        elif ch.isascii() and ch.isalpha():
            letras = c.get("letras", "posicion")
            ds = str(ord(ch.upper()) - (64 if letras == "posicion" else 55)) if letras in ("posicion", "iban") else str(ord(ch))
        else:
            continue  # ';', '-', espacios, letras no ascii: no cuentan (44-47, 264-265)
        for d in ds:
            r = (r * 10 + int(d)) % c["modulo"]
    return str(c["resta"] - (r * c["multiplicador"]) % c["modulo"])


def control_valido(cuerpo_sin_control, texto):
    """None si está mal formado (E201), False si no coincide (E202), True si vale."""
    c = M["control"]
    if not re.fullmatch(c["formato"], texto):
        return None
    esperado = control_esperado(cuerpo_sin_control)
    if c.get("compara", "texto") == "entero":
        return int(texto) == int(esperado)
    return texto == esperado


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
    """el estado de un token: cuentas, titulares, rachas de fallas, operaciones y si está detenido (HALT)."""

    def __init__(self):
        self.cuentas = {}       # id → saldo
        self.titular = {}       # id → nombre del alta (el límite no aplica entre cuentas del mismo nombre)
        self.fallas = {}        # id → transferencias seguidas rechazadas (las que suman al bloqueo)
        self.ops = {}           # id → {"tipo", "monto", "cuentas", "anulada", "comision"}
        self.salidas = {}       # id → transferencias exitosas a otros titulares (solo si el límite acumulado se enciende)
        self.detenido = False

    # ---- pieza 4: transiciones de estado (modelo.json "estado") ----
    def _bloqueo_suma(self, cid, codigo):
        if codigo in M["estado"]["bloqueo"]["suman"]:
            self.fallas[cid] += 1

    def _bloqueo_reinicia(self, cid, motivo):
        if motivo in M["estado"]["bloqueo"]["reinician"]:
            self.fallas[cid] = 0

    def _bloqueada(self, cid):
        return self.fallas[cid] >= M["estado"]["bloqueo"]["tras_fallas"]

    def _con_limite(self, origen, destino):
        lim = M["estado"]["limite"]
        return not (lim.get("exento_mismo_titular") and self.titular[origen] == self.titular[destino])

    # ---- utilidades ----
    def cuenta(self, i):
        if i not in self.cuentas:
            raise error("E401")
        return i

    def nueva_op(self, tipo, monto, cuentas, comision=0):
        oid = M["ids"]["operacion"].format(len(self.ops) + 1)
        self.ops[oid] = {"tipo": tipo, "monto": monto, "cuentas": cuentas, "anulada": False, "comision": comision}
        return {"status": "recieved", "operacionId": oid}  # sic: "recieved" (ejemplo 6)

    def monto(self, texto):
        texto = normalizar("monto", texto)
        if not re.fullmatch(M["monto"]["formato"], texto):
            raise error("E303")
        return int(texto)

    # ---- pieza 2: el orden de los errores del mensaje (modelo.json "orden" → "mensaje") ----
    def mensaje(self, m):
        m = normalizar("mensaje", m)
        x = {"m": m}
        for paso in M["orden"]["mensaje"]:
            getattr(self, "_paso_" + paso)(x)
        return getattr(self, "cmd_" + x["cmd"].lower())(*x["args"])

    def _paso_segmentos(self, x):
        x["segs"] = x["m"].split(";")
        if len(x["segs"]) < 2:
            raise error("E103")

    def _paso_vacios(self, x):
        if any(s == "" for s in x["segs"]):
            raise error("E104")

    def _paso_control(self, x):
        cmd = normalizar("comando", x["segs"][0])
        if cmd in M["sin_control"]:               # PING no valida el control (39-40)
            return
        v = control_valido(";".join(x["segs"][:-1]), normalizar("control", x["segs"][-1]))
        if v is None:
            raise error("E201")
        if not v:
            raise error("E202")

    def _paso_comando(self, x):
        x["cmd"] = normalizar("comando", x["segs"][0])
        if x["cmd"] not in M["comandos"]:
            s = sugerencia(x["cmd"])
            raise error("E301", **({"sugerencia": s} if s else {}))

    def _paso_aridad(self, x):
        x.setdefault("cmd", normalizar("comando", x["segs"][0]))
        x["args"] = x["segs"][1:-1]
        if x["cmd"] in M["comandos"] and len(x["args"]) != M["comandos"][x["cmd"]]:
            raise error("E302")             # un comando desconocido lo resuelve el paso «comando», esté antes o después

    # ---- comandos ----
    def cmd_ping(self):
        return Respuesta(200, {"pong": True})

    def cmd_notas(self):                       # oculto: lo delató la sugerencia de TOTAL (1641)
        return Respuesta(200, M["notas_respuesta"])

    def cmd_alta(self, nombre):
        cid = M["ids"]["cuenta"].format(len(self.cuentas) + 1)
        self.cuentas[cid] = 0
        self.titular[cid] = normalizar("titular", nombre)
        self.fallas[cid] = 0
        return Respuesta(201, {"cuentaId": cid})

    def cmd_consulta(self, cid):
        cid = normalizar("ids", cid)
        return Respuesta(200, {"cuenta_id": self.cuenta(cid), "saldo": self.cuentas[cid]})

    def cmd_deposito(self, cid, monto):
        x = {"cid": normalizar("ids", cid), "texto": monto}
        for paso in M["orden"]["deposito"]:    # hoy: monto (E303) antes que existencia (E401) (218)
            {"monto": lambda: x.__setitem__("n", self.monto(x["texto"])),
             "existencia": lambda: self.cuenta(x["cid"])}[paso]()
        self.cuentas[x["cid"]] += x["n"]
        self._bloqueo_reinicia(x["cid"], "deposito")   # un depósito desbloquea (885-886, 926-928)
        return Respuesta(200, self.nueva_op("deposito", x["n"], [x["cid"]]))

    def cmd_transfer(self, origen, destino, monto):
        o, d = normalizar("ids", origen), normalizar("ids", destino)
        x = {}

        def paso_monto():
            x["n"] = self.monto(monto)

        def paso_mismas():
            if o == d:
                raise error("E304")

        def paso_existencia():
            self.cuenta(o); self.cuenta(d)

        def paso_bloqueo():
            if self._bloqueada(o):
                raise error("E510")

        def paso_limite():
            if self._con_limite(o, d) and x["n"] > M["estado"]["limite"]["monto"]:
                self._bloqueo_suma(o, "E506")
                raise error("E506")

        def paso_acumulado():                  # apagado hoy: solo corre si está en orden.transfer (sol-06 #1)
            acu = M["estado"]["limite"].get("acumulado", {})
            if acu.get("activo") and self._con_limite(o, d) and self.salidas.get(o, 0) + x["n"] > acu["monto"]:
                self._bloqueo_suma(o, acu["codigo"])
                raise error(acu["codigo"])

        def paso_saldo():
            if self.cuentas[o] < x["n"] + comision():
                self._bloqueo_suma(o, "E507")
                raise error("E507")

        def comision():                         # 0 hoy (sol-06 #4)
            com = M["estado"].get("comision", {})
            if not com.get("monto") or (com.get("solo_titulares_distintos", True) and not self._con_limite(o, d)):
                return 0
            return com["monto"]

        pasos = {"monto": paso_monto, "mismas": paso_mismas, "existencia": paso_existencia,
                 "bloqueo": paso_bloqueo, "limite": paso_limite, "acumulado": paso_acumulado, "saldo": paso_saldo}
        for paso in M["orden"]["transfer"]:    # hoy (TR-07): monto → mismas → existencia → bloqueo → límite → saldo
            pasos[paso]()
        self._bloqueo_reinicia(o, "transfer_exitosa")
        com = comision()
        self.cuentas[o] -= x["n"] + com
        self.cuentas[d] += x["n"]
        if self._con_limite(o, d):
            self.salidas[o] = self.salidas.get(o, 0) + x["n"]
        return Respuesta(200, self.nueva_op("transfer", x["n"], [o, d], com))

    def cmd_anula(self, oid):
        op = self.ops.get(normalizar("ids", oid))
        if op is None:
            raise error("E402")
        if op["anulada"]:
            return Respuesta(200, {"ok": False, "motivo": "ya anulada"})
        an = M["estado"]["anula"]
        if op["tipo"] == "deposito":
            efecto = {op["cuentas"][0]: -op["monto"]}
        else:
            o, d = op["cuentas"]
            efecto = {o: op["monto"] + op.get("comision", 0), d: -op["monto"]}
        if not an.get("permite_saldo_negativo", True) and any(self.cuentas[k] + v < 0 for k, v in efecto.items()):
            raise error(an["codigo_si_negativo"])   # apagado hoy: anular puede dejar negativos (116-117, 228-230)
        for k, v in efecto.items():
            self.cuentas[k] += v
        op["anulada"] = True
        return Respuesta(200, {"ok": True, "anulada": normalizar("ids", oid)})

    def cmd_halt(self, confirmacion):
        if confirmacion != M["estado"]["halt"]["confirmacion"]:
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
        self.send_header("X-Gemelo-Version", VERSION)
        self.send_header("X-Gemelo-Arranque", ARRANQUE)
        if x_req is not None:
            self.send_header("X-Req", str(x_req))
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(datos)

    def _leer_chunked(self):
        datos = b""
        while True:
            linea = self.rfile.readline(65537)
            if not linea:
                break
            tam = int(linea.split(b";")[0].strip() or b"0", 16)
            if tam == 0:
                while self.rfile.readline(65537) not in (b"\r\n", b"\n", b""):
                    pass
                break
            datos += self.rfile.read(tam)
            self.rfile.readline(65537)
        return datos

    # ---- pieza 2: el orden de los errores http (modelo.json "orden" → "http") ----
    def _paso_ruta(self, x):
        if x["destino"] is None:               # la ruta va antes que el token (59)
            raise error("E404")

    def _paso_token(self, x):
        if self.headers.get("Authorization") != f"Bearer {TOKEN}":
            raise error("E001")

    def _paso_detenido(self, x):
        if ESTADO["banco"].detenido:            # antes que el tamaño, el json y el mensaje (720-726)
            raise error("E599")

    def _paso_tamano(self, x):
        if len(x["crudo"]) > M["cuerpo_max_bytes"]:   # después del token (712), antes del json (713)
            raise error("E101")

    def _paso_json(self, x):
        try:   # json estricto: NaN e Infinity no son json (1245-1247); python los aceptaría
            texto = x["crudo"].decode("utf-8")
            x["cuerpo"] = json.loads(texto, parse_constant=_no_json)
        except (ValueError, UnicodeDecodeError, RecursionError):
            raise error("E100")
        if profundidad(texto) > M.get("json_profundidad_max", 10 ** 9):   # 20 pasa, 21 no (3462-3463, 3468-3469)
            raise error("E100")

    def _paso_m(self, x):
        if not isinstance(x["cuerpo"], dict) or not isinstance(x["cuerpo"].get("m"), str):
            raise error("E102")

    def atender(self):
        if "chunked" in (self.headers.get("Transfer-Encoding") or "").lower():   # el original los lee (2471)
            crudo = self._leer_chunked()
        else:
            largo = int(self.headers.get("Content-Length") or 0)
            crudo = self.rfile.read(largo) if largo > 0 else b""
        partes = self.requestline.split()           # la ruta cruda: http.server colapsa '//msg' en '/msg' en self.path
        cruda = partes[1] if len(partes) >= 2 else self.path
        ruta = cruda.split("?", 1)[0]              # la query string se ignora (62); '//msg' es otra ruta (1233, 1252)
        x = {"destino": M["rutas"].get(f"{self.command} {ruta}"), "crudo": crudo}
        x_req = None
        with CANDADO:
            try:
                for paso in M["orden"]["http"]:
                    if paso not in ("ruta", "token") and x["destino"] != "msg":
                        continue                    # /health y /__reset solo pasan por ruta y token
                    if paso == "detenido" and x_req is None:
                        ESTADO["x_req"] += 1        # el contador cuenta los pedidos a /msg con token (62, 68)
                        x_req = ESTADO["x_req"]
                    getattr(self, "_paso_" + paso)(x)
                if x["destino"] == "health":
                    raise Respuesta(200, {"ok": True})
                if x["destino"] == "reset":
                    ESTADO["banco"] = Banco()
                    raise Respuesta(200, {"ok": True})
                raise ESTADO["banco"].mensaje(x["cuerpo"]["m"])
            except Respuesta as r:
                self.responder(r, x_req)

    def __getattr__(self, nombre):              # cualquier método (TRACE, PROPFIND…) va a la tabla de rutas: 404 (1658, 1660)
        if nombre.startswith("do_"):
            return self.atender
        raise AttributeError(nombre)


def main():
    if not TOKEN:
        sys.exit("gemelo: falta GEMELO_TOKEN (el token del equipo); sin él respondería 401 a todo")
    puerto = int(os.environ.get("PORT", "8080"))
    srv = ThreadingHTTPServer(("0.0.0.0", puerto), Manejador)
    print(f"gemelo escuchando en :{puerto}", flush=True)
    srv.serve_forever()


if __name__ == "__main__":
    main()
