#!/usr/bin/env python3
"""fable-04 · generador de las secuencias retenidas de venenos (evals/fable-04.jsonl).

NO es el gemelo ni lo mira: es un modelo mínimo de `spec.md` v2 escrito por fable solo desde la spec, que
calcula el dígito de control con la fórmula de § 2 y predice status y cuerpo de cada fila. cada fila lleva
además el código que fable esperaba a mano (`espero`); si el modelo y la expectativa no coinciden, el
generador lo imprime y no escribe nada. las filas marcadas `ambiguo` son donde la spec no decide.

    python3 evals/fable-04-generador.py            # escribe evals/fable-04.jsonl y muestra el resumen
"""
import json, re, sys, os

# ---------- § 2 · el dígito de control, desde la spec ----------
def control(base):
    r = 0
    for ch in base:
        if ch.isascii() and ch.isdigit():
            ds = ch
        elif ch.isascii() and ch.isalpha():
            ds = str(ord(ch.upper()) - 64)
        else:
            continue
        for d in ds:
            r = (r * 10 + int(d)) % 97
    return str(98 - (100 * r) % 97)

# ---------- § 3 y § 5 · modelo mínimo del servicio ----------
COMANDOS = {"PING": 0, "ALTA": 1, "CONSULTA": 1, "DEPOSITO": 2, "TRANSFER": 3, "ANULA": 1, "HALT": 1, "NOTAS": 0}
ERR = {
    "E404": (404, "ruta desconocida"), "E001": (401, "no autorizado"), "E599": (503, "service halted"),
    "E101": (413, "cuerpo demasiado grande"), "E100": (400, "json inválido"), "E102": (400, "falta m"),
    "E103": (400, "falta control"), "E104": (400, "segmento vacío"), "E201": (400, "control mal formado"),
    "E202": (400, "control inválido"), "E301": (400, "comando desconocido "), "E302": (400, "aridad inválida"),
    "E303": (400, "monto inválido"), "E304": (400, "origen y destino iguales"), "E401": (404, "cuenta inexistente"),
    "E402": (404, "operación inexistente"), "E506": (422, "límite excedido"), "E507": (422, "saldo insuficiente"),
    "E510": (409, "cuenta bloqueada"),
    "E520": (409, "operación destructiva: detiene el servicio; reenvía con confirmación"),
}
MONTO = re.compile(r"^[1-9][0-9]{0,9}$")
CTRL = re.compile(r"^[0-9]{1,2}$")

def lev(a, b):
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (ca != cb)))
        prev = cur
    return prev[-1]

def err(code, extra=None):
    st, msg = ERR[code]
    body = {"error": code, "mensaje": msg}
    if extra:
        body.update(extra)
    return st, body

class Servicio:
    def __init__(self):
        self.reset()

    def reset(self):
        self.cuentas = {}     # id -> {"saldo","titular","racha"}
        self.ops = {}         # id -> {"tipo","cuenta"/"origen","destino","monto","anulada"}
        self.n_ac = self.n_op = 0
        self.detenido = False

    def pedir(self, metodo="POST", ruta="/msg", auth="ok", cuerpo=None, request=None):
        if (metodo, ruta) not in {("POST", "/msg"), ("GET", "/health"), ("POST", "/__reset")}:
            return err("E404")
        if auth != "ok":
            return err("E001")
        if ruta == "/health":
            return 200, {"ok": True}
        if ruta == "/__reset":
            self.reset()
            return 200, {"ok": True}
        if self.detenido:
            return err("E599")
        raw = cuerpo if cuerpo is not None else json.dumps(request, ensure_ascii=False)
        if len(raw.encode()) > 8192:
            return err("E101")
        try:
            obj = json.loads(raw)
        except ValueError:
            return err("E100")
        if not isinstance(obj, dict) or not isinstance(obj.get("m"), str):
            return err("E102")
        return self.msg(obj["m"])

    def msg(self, m):
        segs = m.split(";")
        if len(segs) < 2:
            return err("E103")
        if any(s == "" for s in segs):
            return err("E104")
        cmd = segs[0].upper()
        if cmd != "PING":
            c = segs[-1]
            if not (c.isascii() and CTRL.match(c)):
                return err("E201")
            if c != control(";".join(segs[:-1])):
                return err("E202")
        if cmd not in COMANDOS:
            cand = sorted((lev(cmd, k), k) for k in COMANDOS)
            d, k = cand[0]
            return err("E301", {"sugerencia": k} if d <= 2 else None)
        args = segs[1:-1]
        if len(args) != COMANDOS[cmd]:
            return err("E302")
        return getattr(self, "cmd_" + cmd)(*args)

    def cmd_PING(self):
        return 200, {"pong": True}

    def cmd_ALTA(self, nombre):
        self.n_ac += 1
        cid = f"AC-{self.n_ac:04d}"
        self.cuentas[cid] = {"saldo": 0, "titular": nombre, "racha": 0}
        return 201, {"cuentaId": cid}

    def cmd_CONSULTA(self, cid):
        if cid not in self.cuentas:
            return err("E401")
        return 200, {"cuenta_id": cid, "saldo": self.cuentas[cid]["saldo"]}

    def _op(self, **kw):
        self.n_op += 1
        oid = f"OP-{self.n_op:04d}"
        self.ops[oid] = {"anulada": False, **kw}
        return oid

    def cmd_DEPOSITO(self, cid, monto):
        if not MONTO.match(monto):
            return err("E303")
        if cid not in self.cuentas:
            return err("E401")
        c = self.cuentas[cid]
        c["saldo"] += int(monto)
        c["racha"] = 0
        return 200, {"status": "recieved", "operacionId": self._op(tipo="dep", cuenta=cid, monto=int(monto))}

    def cmd_TRANSFER(self, o, d, monto):
        if not MONTO.match(monto):
            return err("E303")
        if o == d:
            return err("E304")
        if o not in self.cuentas or d not in self.cuentas:
            return err("E401")
        co, cd, m = self.cuentas[o], self.cuentas[d], int(monto)
        if co["racha"] >= 3:
            return err("E510")
        if co["titular"] != cd["titular"] and m > 100000:
            co["racha"] += 1
            return err("E506")
        if co["saldo"] < m:
            co["racha"] += 1
            return err("E507")
        co["saldo"] -= m
        cd["saldo"] += m
        co["racha"] = 0
        return 200, {"status": "recieved", "operacionId": self._op(tipo="tr", origen=o, destino=d, monto=m)}

    def cmd_ANULA(self, oid):
        op = self.ops.get(oid)
        if op is None:
            return err("E402")
        if op["anulada"]:
            return 200, {"ok": False, "motivo": "ya anulada"}
        op["anulada"] = True
        if op["tipo"] == "dep":
            self.cuentas[op["cuenta"]]["saldo"] -= op["monto"]
        else:
            self.cuentas[op["origen"]]["saldo"] += op["monto"]
            self.cuentas[op["destino"]]["saldo"] -= op["monto"]
        return 200, {"ok": True, "anulada": oid}

    def cmd_HALT(self, conf):
        if conf != "1":
            return err("E520")
        self.detenido = True
        return err("E599")

# ---------- las secuencias ----------
def M(base, spec, hip, espero, ctrl=None, amb=None):
    """mensaje = base + ';' + control calculado (o el que se pase, para venenos de control)."""
    return {"request": {"m": f"{base};{control(base) if ctrl is None else ctrl}"}, "spec": spec,
            "hipotesis": hip, "espero": espero, "ambiguo": amb}

def RAW(m, spec, hip, espero, amb=None):
    return {"request": {"m": m}, "spec": spec, "hipotesis": hip, "espero": espero, "ambiguo": amb}

def HTTP(metodo, ruta, spec, hip, espero, auth=None, request=None, cuerpo=None, amb=None):
    f = {"request": request if request is not None else {}, "spec": spec, "hipotesis": hip, "espero": espero,
         "ambiguo": amb, "metodo": metodo, "ruta": ruta}
    if auth:
        f["auth"] = auth
    if cuerpo is not None:
        f["cuerpo"] = cuerpo
    return f

def RESET(hip="reset a mitad de secuencia"):
    return HTTP("POST", "/__reset", ["EN-07", "ME-02"], hip, 200)

def primer_monto(prefijo, control_buscado, desde=1):
    """el primer monto válido cuyo mensaje tiene exactamente ese control (para venenos 97/98 y de una cifra)."""
    for m in range(desde, 10**6):
        if control(f"{prefijo};{m}") == control_buscado:
            return str(m)
    raise RuntimeError

A, B, C, X = "AC-0001", "AC-0002", "AC-0003", "AC-0009"
OK = 200
DEP98 = primer_monto("DEPOSITO;AC-0001", "98")                       # depósito cuyo control es 98
TR97 = primer_monto("TRANSFER;AC-0001;AC-0002", "97", int(DEP98) + 1)  # transferencia con control 97, mayor que el depósito
DEP5 = primer_monto("DEPOSITO;AC-0001", "5")                         # depósito cuyo control es de una cifra
T = lambda o, d, m, hip, espero, amb=None: M(f"TRANSFER;{o};{d};{m}", ["TR-07", "TR-08"] if espero in ("E510",) else ["TR-05", "TR-06", "TR-07", "TR-08"] if espero in ("E506", "E507") else ["TR-01", "TR-08"] if espero == OK else ["TR-07"], hip, espero, amb=amb)
DEP = lambda c, m, hip, espero=OK, amb=None: M(f"DEPOSITO;{c};{m}", ["DE-01", "TR-08"] if espero == OK else ["DE-02", "DE-04"], hip, espero, amb=amb)
ALTA = lambda n, hip, espero=201: M(f"ALTA;{n}", ["AL-01", "AL-02"], hip, espero)
# «Consulta» con mayúscula inicial (CM-01: el comando no distingue mayúsculas) para que ningún mensaje suelto
# coincida letra por letra con los 20 ejemplos, como pide la regla de sol-03/04
CON = lambda c, hip, espero=OK, amb=None: M(f"Consulta;{c}", ["CO-01", "CM-01"] if espero == OK else ["CO-02", "CO-03", "CM-01"], hip, espero, amb=amb)
ANU = lambda o, hip, espero=OK, amb=None: M(f"ANULA;{o}", ["AN-01", "AN-02", "AN-03", "AN-04"] if espero == OK else ["AN-05", "ME-03"], hip, espero, amb=amb)
PING = lambda hip, espero=OK, ctrl="7": M("PING", ["PI-01", "IN-10"], hip, espero, ctrl=ctrl)

SECUENCIAS = [
 # ---- A · doble falla en TRANSFER con bloqueo ----
 ("f04-01", "bloqueo: existencia e iguales ganan al bloqueo", [
    ALTA("Noa", "origen"), ALTA("Ines", "destino"),
    T(A, B, 500, "saldo 0: E507, racha 1", "E507"), T(A, B, 500, "racha 2", "E507"), T(A, B, 500, "racha 3: bloqueada", "E507"),
    T(A, X, 1, "doble falla: origen bloqueado y destino inexistente → existencia antes que bloqueo (TR-07)", "E401"),
    T(A, A, 1, "doble falla: origen bloqueado e igual al destino → iguales antes que bloqueo", "E304"),
    T(A, B, 1, "sigue bloqueada: E401 y E304 no cortan la racha", "E510"),
 ]),
 ("f04-02", "bloqueo: monto inválido gana; consultar no se bloquea", [
    ALTA("Noa", "origen"), ALTA("Ines", "destino"),
    T(A, B, 1, "E507, 1", "E507"), T(A, B, 1, "E507, 2", "E507"), T(A, B, 1, "E507, 3: bloqueada", "E507"),
    T(A, B, "0", "doble falla: bloqueada y monto inválido → E303 antes que bloqueo", "E303"),
    T(A, B, 1, "bloqueada", "E510"),
    CON(A, "el bloqueo no afecta consultar", OK),
 ]),
 ("f04-03", "anular el depósito que desbloqueó: ¿vuelve el bloqueo?", [
    ALTA("Noa", "origen"), ALTA("Ines", "destino"),
    T(A, B, 1, "E507, 1", "E507"), T(A, B, 1, "E507, 2", "E507"), T(A, B, 1, "E507, 3: bloqueada", "E507"),
    DEP(A, 1, "un depósito de 1 reinicia la racha (RI-11)", OK),
    ANU("OP-0001", "anular ese depósito: saldo vuelve a 0", OK),
    T(A, B, 1, "la racha ya estaba en 0 y anular no la toca: E507 (racha 1), no E510", "E507",
      amb="TR-08 dice que el depósito reinicia y que anular no reinicia; no dice que anular el depósito restaure la racha anterior. predigo que no: E507 y no E510"),
 ]),
 ("f04-04", "bloqueo mezclado E507/E506; el destino no se bloquea; recibir no desbloquea", [
    ALTA("Noa", "A"), ALTA("Ines", "B"), DEP(B, 50, "B con 50"),
    T(A, B, 10, "A saldo 0: E507, racha 1", "E507"),
    T(A, B, 200000, "titulares distintos y sobre el límite: E506 antes que saldo, racha 2", "E506"),
    T(A, B, 10, "E507, racha 3: A bloqueada", "E507"),
    T(B, A, 10, "B no está bloqueada: pasa, A recibe 10", OK),
    T(A, B, 10, "A tiene saldo 10 pero recibir no reinicia la racha: E510", "E510"),
 ]),
 ("f04-05", "mismo titular: se bloquea igual, y al desbloquear no hay límite", [
    ALTA("Teo", "A, titular Teo"), ALTA("Teo", "B, titular Teo"),
    T(A, B, 5, "E507, 1", "E507"), T(A, B, 5, "E507, 2", "E507"), T(A, B, 5, "E507, 3: bloqueada", "E507"),
    DEP(A, 300000, "desbloquea y fondea"),
    T(A, B, 250000, "mismo titular: sin límite; desbloqueada: pasa", OK),
    T(A, B, 60000, "saldo 50000 < 60000: E507 (racha 1, no bloqueada)", "E507"),
 ]),
 ("f04-06", "triple falla: bloqueo, límite y saldo a la vez", [
    ALTA("Vera", "A"), ALTA("Gael", "B"),
    T(A, B, 1, "E507, 1", "E507"), T(A, B, 1, "E507, 2", "E507"), T(A, B, 1, "E507, 3: bloqueada", "E507"),
    T(A, B, 9999999999, "bloqueada + sobre el límite + sin saldo → bloqueo gana (TR-07)", "E510"),
    DEP(A, 1, "desbloquea"),
    T(A, B, 9999999999, "sin bloqueo: límite antes que saldo (titulares distintos)", "E506"),
 ]),
 ("f04-07", "una transferencia exitosa reinicia la racha", [
    ALTA("Rosa", "A"), ALTA("Iker", "B"), DEP(A, 10, "A con 10"),
    T(A, B, 20, "E507, racha 1", "E507"), T(A, B, 20, "E507, racha 2", "E507"),
    T(A, B, 10, "saldo igual al monto alcanza (TR-05): pasa y la racha vuelve a 0", OK),
    T(A, B, 1, "si la racha se reinició: E507 (racha 1); si no: sería la tercera y daría E510", "E507"),
    T(A, B, 1, "E507, racha 2: sigue sin bloquear", "E507"),
 ]),
 ("f04-08", "orden inesperado: anular una operación que falló", [
    ALTA("Noa", "A"), ALTA("Ines", "B"),
    T(A, B, 1, "E507, 1", "E507"), T(A, B, 1, "E507, 2", "E507"), T(A, B, 1, "E507, 3: bloqueada", "E507"),
    ANU("OP-0001", "las tres transferencias fallidas no consumieron OP (ME-03): no hay nada que anular", "E402"),
 ]),
 # ---- B · anulación y saldos negativos ----
 ("f04-09", "anular antes de que exista nada; anular no crea operación", [
    ANU("OP-0001", "sin operaciones: E402", "E402"),
    ALTA("Luz", "A"), DEP(A, 100, "OP-0001"),
    ANU("OP-0001", "revierte: saldo 0", OK),
    ANU("OP-0001", "segunda anulación: 200 con ok:false", OK),
    DEP(A, 5, "anular no consumió OP: este es OP-0002", OK),
    CON(A, "saldo 5", OK),
 ]),
 ("f04-10", "saldo negativo por anulación y transferencias después", [
    ALTA("Bruno", "A"), ALTA("Pilar", "B"), DEP(A, 100, "OP-0001"),
    T(A, B, 100, "OP-0002: A 0, B 100", OK),
    ANU("OP-0001", "anular el depósito gastado: A queda en -100", OK),
    CON(A, "saldo -100", OK),
    T(A, B, 1, "saldo negativo no alcanza para nada (ME-08): E507", "E507"),
    T(B, A, 100, "B tiene 100: pasa, A vuelve a 0", OK),
 ]),
 ("f04-11", "anular una transferencia cuyo destino ya gastó la plata", [
    ALTA("Bruno", "A"), ALTA("Pilar", "B"), ALTA("Teo", "C"), DEP(A, 100, "OP-0001"),
    T(A, B, 100, "OP-0002: B 100", OK),
    T(B, C, 100, "OP-0003: B 0, C 100", OK),
    ANU("OP-0002", "A recupera 100, B queda en -100 (AN-03)", OK),
    CON(B, "saldo -100", OK),
 ]),
 ("f04-12", "reset a mitad de secuencia: operaciones, cuentas e ids", [
    ALTA("Luz", "A"), DEP(A, 10, "OP-0001"),
    RESET(),
    ANU("OP-0001", "el reset borró las operaciones", "E402"),
    CON(A, "y las cuentas", "E401"),
    ALTA("Luz", "los ids vuelven a AC-0001", 201),
 ]),
 ("f04-13", "ANULA con doble falla: aridad y control antes que la regla; el id es exacto", [
    ALTA("Luz", "A"), DEP(A, 10, "OP-0001"),
    ANU("OP-01", "id con otro ancho: no existe (comparación exacta)", "E402",
        amb="AN-05 probó op-0001 y un id de cuenta, no OP-01; predigo E402 por CO-03 y AN-05"),
    RAW("ANULA;OP-0001;x;" + control("ANULA;OP-0001;x"), ["CM-02", "ER-20"], "aridad antes que la regla del comando", "E302"),
    M("ANULA;OP-0001", ["IN-04", "IN-11"], "control inválido antes que todo lo del comando", "E202", ctrl="1"),
    ANU("OP-0001", "sigue sin anular tras los tres fallos", OK),
 ]),
 # ---- C · titular y límite ----
 ("f04-14", "titular con espacio al final: mismo control, otro titular", [
    ALTA("Noa", "A, titular «Noa»"),
    ALTA("Noa ", "B, titular «Noa » (el espacio no aporta al control: mismo control que «Noa»)"),
    DEP(A, 200000, "fondeo"),
    T(A, B, 150000, "si el titular se compara exacto, «Noa» ≠ «Noa »: E506", "E506",
      amb="TR-06 compara exacto («Lucia» ≠ «lucia»), no probó espacios; predigo titulares distintos"),
    M("Transfer;AC-0001;AC-0002;100000", ["TR-06", "CM-01"], "en el límite: pasa", OK),
 ]),
 ("f04-15", "un espacio como titular, dos veces: mismo titular, sin límite", [
    ALTA(" ", "A, titular « »"), ALTA(" ", "B, titular « »"),
    DEP(A, 300000, "fondeo"),
    T(A, B, 250000, "mismo titular (« » = « »): sin límite", OK,
      amb="AL-02 acepta un espacio como nombre; TR-06 no probó un titular en blanco; predigo mismo titular"),
    CON(B, "saldo 250000", OK),
 ]),
 ("f04-16", "titular en mayúsculas es otro titular; el mismo texto, el mismo", [
    ALTA("Ines", "A"), ALTA("INES", "B"), ALTA("Ines", "C"), DEP(A, 500000, "fondeo"),
    T(A, B, 200000, "«Ines» ≠ «INES»: límite", "E506"),
    T(A, C, 200000, "«Ines» = «Ines»: sin límite", OK),
 ]),
 ("f04-17", "tilde en el titular: mismo control, otro titular", [
    ALTA("Ines", "A"), ALTA("Inés", "B (é no aporta al control)"), ALTA("Inés", "C"),
    DEP(B, 500000, "fondeo en B"),
    T(B, A, 150000, "«Inés» ≠ «Ines»: límite", "E506",
      amb="TR-06 compara exacto; no probó tildes. predigo distintos"),
    T(B, C, 150000, "«Inés» = «Inés»: sin límite", OK),
 ]),
 ("f04-18", "el límite es por operación y 100.000 es el borde", [
    ALTA("Vera", "A"), ALTA("Gael", "B"), DEP(A, 300000, "fondeo"),
    M("Transfer;AC-0001;AC-0002;100000", ["TR-06", "CM-01"], "100.000 pasa (comando con mayúscula inicial para no repetir el ejemplo 10 literal)", OK),
    T(A, B, 100001, "100.001 no", "E506"),
    M("Transfer;AC-0001;AC-0002;100000", ["TR-06", "ME-07"], "no acumula: otros 100.000 pasan", OK),
 ]),
 # ---- D · bordes del control y del monto ----
 ("f04-19", "controles 97 y 98 en comandos con estado", [
    ALTA("Rosa", "A"), ALTA("Iker", "B"),
    M("DEPOSITO;AC-0001;" + DEP98, ["IN-06", "IN-04"], "resto 0: el control es 98, no 1", "E202", ctrl="1"),
    M("DEPOSITO;AC-0001;" + DEP98, ["IN-06", "DE-01"], "con 98 pasa (OP-0001: el E202 no consumió OP)", OK),
    M("TRANSFER;AC-0001;AC-0002;" + TR97, ["IN-06", "TR-05"], "resto 1: control 97; monto mayor que el saldo → E507 (el control pasó)", "E507"),
    CON(A, "saldo del depósito", OK),
 ]),
 ("f04-20", "control de una cifra en un comando con estado", [
    ALTA("Luz", "A"),
    M("DEPOSITO;AC-0001;" + DEP5, ["IN-07"], "control 5 escrito 05: bien formado, inválido", "E202", ctrl="05"),
    M("DEPOSITO;AC-0001;" + DEP5, ["IN-03"], "005: tres dígitos, mal formado", "E201", ctrl="005"),
    M("DEPOSITO;AC-0001;" + DEP5, ["IN-07", "DE-01"], "con 5 pasa: OP-0001", OK),
    CON(A, "saldo", OK),
 ]),
 ("f04-21", "montos al borde en TRANSFER", [
    ALTA("Vera", "A"), ALTA("Gael", "B"), DEP(A, 9999999999, "10 cifras: pasa"),
    T(A, B, "10000000000", "11 cifras: inválido", "E303"),
    T(A, B, "1 ", "espacio al final: el control no lo ve, el monto sí (sin recortar)", "E303"),
    T(A, B, "0999999999", "cero a la izquierda", "E303"),
    T(A, B, 9999999999, "válido pero sobre el límite entre titulares distintos", "E506"),
 ]),
 ("f04-22", "mismo titular: todo el saldo de 10 cifras en una transferencia", [
    ALTA("Teo", "A"), ALTA("Teo", "B"), DEP(A, 9999999999, "fondeo"),
    T(A, B, 9999999999, "sin límite y saldo igual al monto: pasa", OK),
    CON(A, "0", OK), CON(B, "9999999999", OK),
 ]),
 ("f04-23", "qué error gana: pares sin evidencia directa en ER-20", [
    RAW("CONSULTA;;5X", ["IN-02", "IN-03", "ER-20"], "segmento vacío y control mal formado → E104 (par sin evidencia en ER-20)", "E104"),
    M("DEPOSITO;AC-0001;abc", ["IN-04", "IN-11"], "control inválido y monto inválido → control", "E202", ctrl="9"),
    M("TRANSFER;AC-0009;AC-0009;abc", ["TR-07"], "monto inválido, iguales e inexistentes → monto", "E303"),
    M("TRANSFER;AC-0009;AC-0009;5", ["TR-07"], "iguales e inexistentes → iguales antes que existencia", "E304"),
 ]),
 ("f04-24", "comando desconocido con doble falla", [
    M("SALDO;", ["IN-02", "ER-20"], "segmento vacío antes que comando", "E104", ctrl=""),
    RAW("SALDOS;AC-0002;5X", ["IN-03", "IN-11"], "control mal formado antes que comando", "E201"),
    M("SALDOS;AC-0002", ["IN-04", "IN-11"], "control inválido antes que comando", "E202", ctrl="1"),
    M("SALDOS;AC-0002", ["DC-01", "DC-02"], "control válido: comando desconocido, lejos de todos: sin sugerencia", "E301"),
 ]),
 ("f04-25", "sugerencias con palabras nuevas", [
    M("PONG", ["DC-02"], "PONG → PING a 1", "E301"),
    M("NOTA", ["DC-02"], "NOTA → NOTAS a 1", "E301"),
    M("ALTO", ["DC-02", "DC-03"], "ALTO → ALTA a 1 (HALT queda a 3)", "E301"),
    M("TRANSFERS;AC-0001;AC-0002;5", ["DC-02", "IN-11"], "TRANSFERS → TRANSFER a 1; con argumentos, igual E301 (la aridad va después)", "E301"),
 ]),
 ("f04-26", "PING: aridad sí, control no; un PING mal escrito es desconocido", [
    M("pingg", ["DC-02", "CM-01", "IN-11"], "PINGG → PING a 1: desconocido (con control válido, porque no es PING y sí lo valida)", "E301"),
    RAW("PING;64;64", ["PI-02", "CM-02"], "PING con un argumento: aridad", "E302"),
    RAW("ping;ZZ", ["PI-01", "IN-10", "CM-01"], "minúsculas y control no numérico: pong", OK),
 ]),
 # ---- E · HALT ----
 ("f04-27", "HALT que no detiene: control, aridad y confirmación con espacio", [
    ALTA("Luz", "A"),
    M("HALT;1", ["IN-11", "HA-02"], "control inválido antes que el comando: no detiene", "E202", ctrl="2"),
    PING("sigue vivo", OK),
    RAW("HALT;1;1;" + control("HALT;1;1"), ["HA-04"], "dos argumentos: aridad, no detiene", "E302"),
    PING("sigue vivo", OK),
    M("HALT;1 ", ["HA-05"], "«1 » no es «1» como texto (el control es el mismo que HALT;1): E520 y no detiene", "E520",
      amb="HA-05 compara como texto y probó 0, 2 y 01; no probó espacios. predigo E520"),
    PING("sigue vivo", OK),
 ]),
 ("f04-28", "HALT;1 y después: todo E599 salvo ruta y token; el reset con otro token no repara", [
    ALTA("Luz", "A"), DEP(A, 10, "OP-0001"),
    M("HALT;1", ["HA-02"], "detiene", "E599"),
    CON(A, "detenido: E599", "E599"),
    HTTP("POST", "/__reset", ["EN-07", "ER-20"], "otro token: 401, y no repara", "E001", auth="otro token"),
    PING("sigue detenido", "E599"),
    RESET("el reset con el token repara"),
    CON(A, "y borró la cuenta", "E401"),
 ]),
 ("f04-29", "detenido: health, token y método antes que E599", [
    ALTA("Luz", "A"),
    M("HALT;1", ["HA-02"], "detiene", "E599"),
    HTTP("GET", "/health", ["HA-03", "EN-06"], "health sigue en 200", OK),
    HTTP("GET", "/health", ["EN-06", "ER-20"], "health sin token: 401 aunque detenido", "E001", auth="sin token"),
    HTTP("POST", "/msg", ["ER-20"], "msg sin token: token antes que detenido", "E001", auth="sin token", request={"m": "PING;7"}),
    HTTP("GET", "/__reset", ["EN-01", "HA-03"], "GET en /__reset: ruta antes que detenido", "E404"),
 ]),
 ("f04-30", "confirmaciones que no confirman, y la que sí en minúsculas", [
    M("HALT;01", ["HA-05"], "01 no es 1", "E520"),
    M("HALT;1.0", ["HA-05"], "1.0 no es 1", "E520"),
    M("HALT; 1", ["HA-05"], "espacio delante: no es 1 (mismo control que HALT;1)", "E520",
      amb="HA-05 no probó espacios; predigo E520"),
    M("halt;1", ["HA-05", "CM-01"], "minúsculas: detiene", "E599"),
    PING("detenido", "E599"),
 ]),
 ("f04-31", "bloqueo y HALT: detenido gana al bloqueo; el reset borra ambos", [
    ALTA("Noa", "A"), ALTA("Ines", "B"),
    T(A, B, 1, "E507, 1", "E507"), T(A, B, 1, "E507, 2", "E507"), T(A, B, 1, "E507, 3: bloqueada", "E507"),
    M("HALT;1", ["HA-02"], "detiene", "E599"),
    T(A, B, 1, "detenido antes que cualquier regla: E599, no E510", "E599"),
    RESET("repara y borra las cuentas"),
 ]),
 # ---- F · orden inesperado, corto ----
 ("f04-32", "operar antes de dar de alta: nada se consume", [
    DEP(A, 5, "sin cuentas: E401", "E401"),
    T(A, B, 5, "sin cuentas: E401", "E401"),
    ALTA("Luz", "primera cuenta: AC-0001 (los fallos no consumieron AC)", 201),
    DEP(A, 5, "OP-0001 (ni OP)", OK),
 ]),
 ("f04-33", "anular una operación futura", [
    ALTA("Luz", "A"), DEP(A, 5, "OP-0001"),
    ANU("OP-0002", "todavía no existe", "E402"),
    DEP(A, 5, "ahora sí: OP-0002"),
    ANU("OP-0002", "y se anula", OK),
 ]),
 ("f04-34", "ids de cuenta: aridad, minúsculas y espacio al final", [
    ALTA("Luz", "A"),
    RAW("CONSULTA;AC-0001;AC-0002;" + control("CONSULTA;AC-0001;AC-0002"), ["CM-02"], "dos argumentos: aridad", "E302"),
    M("consulta;ac-0001", ["CM-01", "CO-03"], "comando en minúsculas vale, el id no", "E401"),
    M("CONSULTA;AC-0001 ", ["CO-03", "IN-09"], "espacio al final del id: mismo control que AC-0001, otro id", "E401",
      amb="CO-03 probó un espacio delante (255), no detrás; predigo E401"),
    CON(A, "el id exacto sí", OK),
 ]),
 ("f04-35", "el cuerpo a mitad de una secuencia con estado", [
    ALTA("Luz", "A"), DEP(A, 10, "OP-0001"),
    HTTP("POST", "/msg", ["EN-11", "CO-01"], "clave extra: se ignora", OK, request={"m": "Consulta;AC-0001;" + control("Consulta;AC-0001"), "M": "x"}),
    HTTP("POST", "/msg", ["EN-10"], "clave m repetida: un parser json se queda con la última → PING", OK,
         cuerpo='{"m":"CONSULTA;AC-0001;%s","m":"PING;1"}' % control("CONSULTA;AC-0001"),
         amb="EN-10 no habla de claves repetidas; los parsers json comunes toman la última. predigo pong"),
    HTTP("POST", "/msg", ["EN-09"], "json con espacios alrededor sigue siendo json", OK, cuerpo='  {"m":"PING;1"}  ',
         amb="EN-09 no probó relleno alrededor del json; predigo que es json válido"),
    HTTP("POST", "/msg", ["EN-09"], "basura después del json: no es json", "E100", cuerpo='{"m":"PING;1"}x'),
 ]),
 ("f04-36", "caracteres de ancho completo y una ñ en el titular", [
    RAW("PING；64", ["IN-01"], "punto y coma de ancho completo: un solo segmento", "E103"),
    RAW("CONSULTA;AC-0001;１４", ["IN-03"], "dígitos de ancho completo: control mal formado", "E201"),
    ALTA("Ñandú", "ñ y ú no aportan al control: N viene de «ALTAand»", 201),
    CON(A, "la cuenta existe", OK),
 ]),
 # ---- G · rachas largas con errores intercalados ----
 ("f04-37", "E304 y E401 intercalados no suman ni cortan la racha", [
    ALTA("Noa", "A"), ALTA("Ines", "B"),
    T(A, B, 1, "E507, 1", "E507"),
    T(A, A, 1, "E304: ni suma ni corta", "E304"),
    T(A, X, 1, "E401: ni suma ni corta", "E401"),
    T(A, B, 1, "E507, 2", "E507"), T(A, B, 1, "E507, 3: bloqueada", "E507"),
    T(A, B, 1, "bloqueada", "E510"),
 ]),
 ("f04-38", "dos rachas independientes; el depósito reinicia solo la suya", [
    ALTA("Noa", "A"), ALTA("Ines", "B"),
    T(A, B, 1, "A: E507, 1", "E507"), T(B, A, 1, "B: E507, 1", "E507"),
    T(A, B, 1, "A: 2", "E507"), T(A, B, 1, "A: 3, bloqueada", "E507"),
    DEP(B, 5, "B: racha a 0 (ya estaba en 1); A sigue bloqueada"),
    T(B, A, 5, "B no está bloqueada: pasa", OK),
 ]),
]

def main():
    salida = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fable-04.jsonl")
    filas, fallas, n_halt = [], [], 0
    for seq, titulo, pasos in SECUENCIAS:
        s = Servicio()
        for p in pasos:
            st, body = s.pedir(p.get("metodo", "POST"), p.get("ruta", "/msg"), p.get("auth", "ok"), p.get("cuerpo"), p["request"])
            esperado = p["espero"]
            visto = body.get("error") if isinstance(body, dict) and "error" in body else st
            if visto != esperado:
                fallas.append((seq, p["request"], esperado, visto))
            fila = {"id": len(filas) + 1, "seq": seq, "request": p["request"], "status": st, "response": body,
                    "spec": p["spec"], "hipotesis": p["hipotesis"]}
            for k in ("metodo", "ruta", "auth", "cuerpo", "ambiguo"):
                if p.get(k):
                    fila[k] = p[k]
            filas.append(fila)
            if p["request"].get("m", "").lower().startswith("halt;1;") and st == 503:
                n_halt += 1
    if fallas:
        print("MI LECTURA Y MI EXPECTATIVA NO COINCIDEN:")
        for f in fallas:
            print("  ", f)
        sys.exit(1)
    with open(salida, "w", encoding="utf-8") as f:
        for fila in filas:
            f.write(json.dumps(fila, ensure_ascii=False, separators=(",", ":")) + "\n")
    largos = {}
    for seq, _, pasos in SECUENCIAS:
        largos[seq] = len(pasos)
    print(f"{len(SECUENCIAS)} secuencias, {len(filas)} pedidos, HALT;1 en {n_halt} secuencias, "
          f"{sum(1 for x in filas if 'ambiguo' in x)} filas ambiguas, largos {min(largos.values())}–{max(largos.values())}")
    for seq, titulo, pasos in SECUENCIAS:
        print(f"  {seq} ({len(pasos)}) {titulo}")

if __name__ == "__main__":
    main()
