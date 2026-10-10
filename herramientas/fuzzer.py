"""fuzzer diferencial: secuencias al azar (con semilla) contra el original, comparadas con el gemelo.

    python3 herramientas/fuzzer.py --semilla 1 --secuencias 30          # ~30 × 9 pedidos, todo al log

cada secuencia arranca con un reset, dos o tres altas y un depósito, y sigue con 4 a 9 pedidos elegidos al
azar entre los comandos, con montos en los bordes que conocemos (100.000, 100.001, 10 cifras), titulares
repetidos, ids que existen y que no, anulaciones repetidas y algún error de forma. el original responde,
todo va al log (seq fuzz-<semilla>-<n>) y el gemelo, levantado aquí, recibe la misma secuencia: cada
diferencia es un comportamiento que la spec no tiene. la hipótesis de cada línea dice qué se sorteó.
el azar elige; no hay bucles: cada secuencia se manda una vez. toma el turno del token.
"""
import argparse, json, os, random, sys
AQUI = os.path.dirname(os.path.abspath(__file__)); RAIZ = os.path.dirname(AQUI)
sys.path.insert(0, AQUI); sys.path.insert(0, RAIZ)
from lote import correr, turno
from control import control
import centinela

NOMBRES = ["Lucia", "Lucia", "Mateo", "Ana", "lucia", "José"]
MONTOS = ["1", "10", "999", "1000", "50000", "99999", "100000", "100001", "150000", "250000", "9999999999", "0", "0100"]

def generar(rng, largo):
    cuentas, ops = 0, 0
    pasos = []
    def m(cuerpo, h, bien=True):
        pasos.append({"m": f"{cuerpo};{control(cuerpo) if bien else rng.choice(['00', '99', 'X'])}", "hipotesis": h})
    def cuenta(existente=True):
        if existente and cuentas:
            c = f"AC-{rng.randint(1, cuentas):04d}"
        else:
            c = f"AC-{cuentas + rng.randint(1, 3):04d}"
        return c.lower() if rng.random() < 0.03 else c
    for _ in range(rng.choice([2, 2, 3])):
        n = rng.choice(NOMBRES); m(f"ALTA;{n}", f"fuzz: alta de {n}"); cuentas += 1
    m(f"DEPOSITO;AC-0001;{rng.choice(['250000', '500000', '150000'])}", "fuzz: depósito inicial"); ops += 1
    for _ in range(largo):
        x = rng.random()
        if x < 0.40:
            o, d, mo = cuenta(), cuenta(rng.random() > 0.05), rng.choice(MONTOS)
            m(f"TRANSFER;{o};{d};{mo}", f"fuzz: transferencia {o}→{d} de {mo}")
            ops += 1
        elif x < 0.55:
            c, mo = cuenta(rng.random() > 0.05), rng.choice(MONTOS)
            m(f"DEPOSITO;{c};{mo}", f"fuzz: depósito de {mo} a {c}"); ops += 1
        elif x < 0.70:
            op = f"OP-{rng.randint(1, max(1, ops + 1)):04d}"
            m(f"ANULA;{op}", f"fuzz: anular {op}")
        elif x < 0.82:
            c = cuenta(rng.random() > 0.05)
            m(f"CONSULTA;{c}", f"fuzz: consultar {c}")
        elif x < 0.90:
            n = rng.choice(NOMBRES); m(f"ALTA;{n}", f"fuzz: alta de {n}"); cuentas += 1
        elif x < 0.95:
            cmd = rng.choice(["consulta", "Deposito", "TRANSFERIR", "ANULAR", "SALDO", "PING"])
            m(f"{cmd};{cuenta()}", f"fuzz: comando raro {cmd}")
        else:
            c = cuenta(); m(f"CONSULTA;{c}", f"fuzz: control equivocado en una consulta de {c}", bien=False)
    return pasos

def main():
    a = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    a.add_argument("--semilla", type=int, required=True)
    a.add_argument("--secuencias", type=int, default=20)
    x = a.parse_args()
    base, token = os.environ.get("ORIGINAL_URL"), os.environ.get("ORIGINAL_TOKEN")
    if not base or not token:
        sys.exit("fuzzer: faltan ORIGINAL_URL u ORIGINAL_TOKEN")
    os.chdir(RAIZ)
    rng = random.Random(x.semilla)
    difs, total = [], 0
    with turno():
        for k in range(1, x.secuencias + 1):
            seq = f"fuzz-{x.semilla}-{k:02d}"
            pasos = [{"reset": True, "hipotesis": f"{seq}: reset"}] + generar(rng, rng.randint(4, 9))
            r = correr(pasos, seq, base, token, eco=False)
            total += len(r)
            d = centinela.contra_gemelo(r)
            if d:
                difs.append((seq, d))
                print(f"DIFIERE {seq} log {d['id']}: original {json.dumps(d['esperado'], ensure_ascii=False)} · gemelo {json.dumps(d['obtenido'], ensure_ascii=False)}", flush=True)
    print(f"fuzzer semilla {x.semilla}: {x.secuencias} secuencias, {total} pedidos, {len(difs)} con diferencias", flush=True)

if __name__ == "__main__":
    main()
