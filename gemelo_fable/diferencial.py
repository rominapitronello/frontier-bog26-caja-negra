#!/usr/bin/env python3
"""diferencial entre dos gemelos: secuencias aleatorias con estado contra los dos, en local, sin token del original.

    python3 gemelo_fable/diferencial.py --a http://127.0.0.1:8081 --b http://127.0.0.1:8082 --token t \
        --semilla 1 --secuencias 300 --salida evals/fable-d8-discrepancias.jsonl

a = el gemelo de quien lidera (`gemelo/`), b = `gemelo_fable/`. cada secuencia: reset en los dos, y pedidos
sorteados con estado (cuentas y operaciones que existen, titulares repetidos, montos en los bordes, rachas,
anulaciones, HALT raro, dobles fallas, errores de forma, anomalías de entrada). se compara cada respuesta con la
regla del juez (status + json sin orden de claves; texto exacto si no es json). la secuencia se corta en la
**primera** discrepancia: lo que sigue sería consecuencia. las discrepantes se escriben en el formato de
`evals/sol-03.jsonl` (predicción = lo que dijo b) con la respuesta de a aparte, para que quien tiene el token
pregunte al original solo esas.
"""
import argparse, json, random, sys, urllib.request, urllib.error

NOMBRES = ["Noa", "Ines", "Inés", "Noa ", "Teo", "Vera", "Gael", "Rosa", "Iker", "Luz", " ", "noa", "Isla Azul", "Ñandú", "1234"]
MONTOS_RAROS = ["0", "-5", "10.5", "0100", "1 ", "10000000000", "+100", "1e3", "abc", " 100", "1\n"]
MONTOS = ["1", "5", "10", "100", "250", "99999", "100000", "100001", "150000", "200000", "999999999", "9999999999"]
DESCONOCIDOS = ["PONG", "NOTA", "ALTO", "HELP", "SALDO", "TRANSFERS", "PIN", "HALTS", "CONSUL", "DEPOSIT", "ANULAR", "XYZ"]


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


def con_control(base, rnd, prob_mal=0.04):
    c = control(base)
    x = rnd.random()
    if x < prob_mal / 2:
        c = str((int(c) + 1) % 100)          # inválido (E202)
    elif x < prob_mal:
        c = rnd.choice(["XX", "0" + c, c + " ", "999", c + "\n"])  # mal formado (E201) o 0-cero
    return base + ";" + c


class Generador:
    """sortea pedidos con estado; se le pasa el mismo rnd a las dos secuencias (a y b reciben lo mismo)."""

    def __init__(self, rnd):
        self.rnd = rnd
        self.cuentas = []
        self.ops = []

    def cuenta(self):
        r = self.rnd.random()
        if not self.cuentas or r < 0.06:
            return "AC-0009"
        if r < 0.09:
            return self.rnd.choice(self.cuentas).lower()
        if r < 0.11:
            return self.rnd.choice(self.cuentas) + " "
        return self.rnd.choice(self.cuentas)

    def op(self):
        if not self.ops or self.rnd.random() < 0.1:
            return self.rnd.choice(["OP-0099", "OP-01", "OP-%04d" % (len(self.ops) + 1), "op-0001"])
        return self.rnd.choice(self.ops)

    def paso(self):
        """devuelve un pedido: dict con m (o metodo/ruta/auth/cuerpo)."""
        rnd = self.rnd
        x = rnd.random()
        if x < 0.03:   # anomalías de entrada
            return rnd.choice([
                {"metodo": "GET", "ruta": "/health"}, {"metodo": "POST", "ruta": "/health"}, {"metodo": "GET", "ruta": "/msg"},
                {"metodo": "POST", "ruta": "/__reset", "auth": "otro"}, {"metodo": "POST", "ruta": "/msg", "auth": "sin", "m": "PING;1"},
                {"cuerpo": "NO_ES_JSON"}, {"cuerpo": '{"m":"PING;1"}x'}, {"cuerpo": '  {"m":"PING;1"}  '}, {"cuerpo": "[1,2]"},
                {"cuerpo": '{"m":5}'}, {"cuerpo": '{"M":"PING;1"}'}, {"cuerpo": '{"m":"PING;1","m":"NOTAS;%s"}' % control("NOTAS")},
                {"cuerpo": '{"m":"PING;1","x":NaN}'}, {"cuerpo": '{"m":"PING;1","x":' + "[" * 21 + "]" * 21 + "}"},
                {"cuerpo": '{"m":"PING;1","x":' + "[" * 19 + "]" * 19 + "}"}, {"cuerpo": '{"m":"PING;1","n":' + "9" * 4301 + "}"},
                {"metodo": "POST", "ruta": "/msg?x=1", "m": "PING;1"}, {"metodo": "POST", "ruta": "/MSG", "m": "PING;1"},
            ])
        if x < 0.05:
            return {"metodo": "POST", "ruta": "/__reset", "reset": True}
        if x < 0.08:
            return {"m": rnd.choice(["PING;1", "ping;ZZ", "PING;64;64", "PING;;1", "PING", "", ";PING;1", "PING；64"])}
        if x < 0.10:
            return {"m": con_control("NOTAS", rnd)}
        if x < 0.13:
            return {"m": con_control(rnd.choice(DESCONOCIDOS) + rnd.choice(["", ";" + self.cuenta()]), rnd)}
        if x < 0.15:
            conf = rnd.choice(["0", "01", "1 ", " 1", "1.0", "SI", "2", "1", "1"])
            m = con_control(rnd.choice(["HALT", "halt"]) + ";" + conf, rnd, 0.1)
            return {"m": m, "halt": conf == "1"}
        if x < 0.30:
            nombre = rnd.choice(NOMBRES)
            m = con_control("ALTA;" + nombre, rnd)
            return {"m": m, "alta": True}
        if x < 0.42:
            return {"m": con_control("Consulta;" + self.cuenta() if rnd.random() < 0.3 else "CONSULTA;" + self.cuenta(), rnd)}
        if x < 0.58:
            monto = rnd.choice(MONTOS_RAROS) if rnd.random() < 0.12 else rnd.choice(MONTOS)
            return {"m": con_control("DEPOSITO;%s;%s" % (self.cuenta(), monto), rnd), "op": True}
        if x < 0.86:
            o, d = self.cuenta(), self.cuenta()
            if rnd.random() < 0.05:
                d = o
            monto = rnd.choice(MONTOS_RAROS) if rnd.random() < 0.08 else rnd.choice(MONTOS)
            if rnd.random() < 0.2:
                monto = rnd.choice(["1", "5", "10"])  # chicos, para armar rachas de E507
            return {"m": con_control("TRANSFER;%s;%s;%s" % (o, d, monto), rnd), "op": True}
        if x < 0.97:
            return {"m": con_control("ANULA;" + self.op(), rnd)}
        return {"m": con_control(rnd.choice(["ALTA;a;b", "CONSULTA", "DEPOSITO;AC-0001", "TRANSFER;AC-0001;AC-0002", "ANULA", "HALT", "NOTAS;x"]), rnd)}

    def aprender(self, pedido, status, cuerpo):
        """actualiza lo que existe según lo que respondió el gemelo b (ids correlativos)."""
        if pedido.get("reset"):
            self.cuentas, self.ops = [], []
        if isinstance(cuerpo, dict):
            if "cuentaId" in cuerpo:
                self.cuentas.append(cuerpo["cuentaId"])
            if "operacionId" in cuerpo:
                self.ops.append(cuerpo["operacionId"])


def pedir(base, token, pedido, timeout=10):
    metodo = pedido.get("metodo", "POST")
    ruta = pedido.get("ruta", "/msg")
    if "cuerpo" in pedido:
        datos = pedido["cuerpo"].encode("utf-8")
    elif "m" in pedido:
        datos = json.dumps({"m": pedido["m"]}, ensure_ascii=False).encode("utf-8")
    else:
        datos = b""
    req = urllib.request.Request(base + ruta, data=datos if metodo != "GET" else None, method=metodo)
    auth = pedido.get("auth", "ok")
    if auth == "ok":
        req.add_header("Authorization", "Bearer " + token)
    elif auth == "otro":
        req.add_header("Authorization", "Bearer otro-token")
    req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, r.read()
    except urllib.error.HTTPError as e:
        return e.code, e.read()


def como_json(crudo):
    try:
        return json.loads(crudo.decode("utf-8"))
    except (ValueError, UnicodeDecodeError):
        return None


def iguales(sa, ca, sb, cb):
    """la regla del juez: status igual y cuerpo igual (json comparado como valor; si no, texto exacto)."""
    if sa != sb:
        return False
    ja, jb = como_json(ca), como_json(cb)
    if ja is not None and jb is not None:
        return ja == jb
    return ca == cb


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--a", required=True); p.add_argument("--b", required=True); p.add_argument("--token", required=True)
    p.add_argument("--semilla", type=int, default=1); p.add_argument("--secuencias", type=int, default=100)
    p.add_argument("--largo-max", type=int, default=12); p.add_argument("--salida", default="evals/fable-d8-discrepancias.jsonl")
    args = p.parse_args()
    rnd = random.Random(args.semilla)
    discrepantes, total_pedidos, filas, n_id = 0, 0, [], 0
    resumen = {}
    for n in range(1, args.secuencias + 1):
        seq = "d8-%d-%03d" % (args.semilla, n)
        gen = Generador(rnd)
        largo = rnd.randint(1, args.largo_max)
        for base in (args.a, args.b):
            pedir(base, args.token, {"metodo": "POST", "ruta": "/__reset"})
        pasos = []
        for i in range(largo):
            pedido = gen.paso()
            sa, ca = pedir(args.a, args.token, pedido)
            sb, cb = pedir(args.b, args.token, pedido)
            total_pedidos += 1
            gen.aprender(pedido, sb, como_json(cb))
            pasos.append((pedido, sa, ca, sb, cb))
            if not iguales(sa, ca, sb, cb):
                discrepantes += 1
                clave = "%s→a:%s/b:%s" % (pedido.get("m", pedido.get("cuerpo", pedido.get("ruta")))[:40].split(";")[0], sa, sb)
                resumen[clave] = resumen.get(clave, 0) + 1
                for (pd, xa, xca, xb, xcb) in pasos:   # toda la secuencia hasta la discrepancia, en formato sol-03
                    n_id += 1
                    fila = {"id": n_id, "seq": seq, "request": {"m": pd["m"]} if "m" in pd and "cuerpo" not in pd else {},
                            "status": xb, "response": como_json(xcb) if como_json(xcb) is not None else xcb.decode("utf-8", "replace"),
                            "spec": [], "hipotesis": "diferencial d8: b (fable) dice esto; a (gemelo) dice %s %s" % (xa, xca.decode("utf-8", "replace")[:120]) if (pd, xa, xca, xb, xcb) is pasos[-1] else "paso previo, iguales en a y b"}
                    for k in ("metodo", "ruta", "cuerpo"):
                        if k in pd:
                            fila[k] = pd[k]
                    if pd.get("auth") == "sin":
                        fila["auth"] = "sin token"
                    elif pd.get("auth") == "otro":
                        fila["auth"] = "otro token"
                    filas.append(fila)
                print("DISCREPA %s paso %d: %s\n   a: %s %s\n   b: %s %s" % (seq, i + 1, json.dumps(pedido, ensure_ascii=False)[:160], sa, ca[:160], sb, cb[:160]))
                break
    with open(args.salida, "w", encoding="utf-8") as f:
        for fila in filas:
            f.write(json.dumps(fila, ensure_ascii=False, separators=(",", ":")) + "\n")
    print("\n%d secuencias, %d pedidos, %d secuencias con discrepancia → %s" % (args.secuencias, total_pedidos, discrepantes, args.salida))
    for k, v in sorted(resumen.items(), key=lambda kv: -kv[1]):
        print("  %3d  %s" % (v, k))
    return 1 if discrepantes else 0


if __name__ == "__main__":
    sys.exit(main())
