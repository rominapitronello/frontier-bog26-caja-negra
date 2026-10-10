"""dígito de control del servicio: el de los iban (iso 7064, mod 97-10), sobre el mensaje sin su último campo.

    letras  → posición en el alfabeto, sin distinguir mayúsculas (a/A = 1 … z/Z = 26)
    dígitos → tal cual
    ';' y '-' → se descartan
    N = todo eso concatenado como número decimal
    control = 98 - (N * 100 % 97)

hipótesis de fable (encargos/fable-02-respuesta.md § 0), 10 oct 10:4x bog, sin consultar el original.
calza los 20 ejemplos del material: 16 controles válidos, rechaza el 83 del ejemplo 2.
**probable, no confirmado**: falta un mensaje nuevo contra el original (sondas en la respuesta, § 3).
lo que no se sabe y el gemelo tiene que decidir como supuesto hasta que se pruebe:
  - caracteres fuera de [A-Za-z0-9;-] (espacio, ñ, tildes, '_'): aquí se descartan.
  - control con ceros a la izquierda, signo, espacios, tres dígitos: aquí vale si int() lo lee y coincide.
  - cuando N*100 % 97 == 0 o == 1: aquí el control es 98 y 97 (la forma «calcular»); la forma «validar
    int(N‖control) % 97 == 1» aceptaría también 1 y 0. la sonda 5 de la respuesta lo separa.

uso:
    python3 herramientas/control.py 'ALTA;Lucia'                       → 82
    python3 herramientas/control.py material/pruebas/ejemplos.jsonl    → autoprueba contra los ejemplos
"""
import json, sys

MODULO = 97          # parámetros, no constantes: si el incidente los cambia, se cambia aquí (DISENO.md D4)
MULTIPLICADOR = 100
RESTA = 98
DESCARTADOS = ";-"


def numero(mensaje_sin_control):
    """el mensaje como número decimal: letras a su posición en el alfabeto, dígitos tal cual."""
    partes = []
    for ch in mensaje_sin_control:
        if ch.isdigit():
            partes.append(ch)
        elif "a" <= ch.lower() <= "z":
            partes.append(str(ord(ch.lower()) - 96))
        elif ch in DESCARTADOS:
            continue
        # supuesto: cualquier otro carácter se descarta (no probado)
    return int("".join(partes)) if partes else 0


def control(mensaje_sin_control):
    return RESTA - (numero(mensaje_sin_control) * MULTIPLICADOR % MODULO)


def bien_formado(texto):
    """supuesto: dígitos puros. 'E201 control mal formado' si no."""
    return texto.isdigit()


def valido(mensaje_sin_control, texto_control):
    """True si el control coincide; None si está mal formado (E201); False si no coincide (E202)."""
    if not bien_formado(texto_control):
        return None
    return int(texto_control) == control(mensaje_sin_control)


def partir(m):
    """'CMD;arg;…;control' → ('CMD;arg;…', 'control'). sin ';' no hay control."""
    base, sep, c = m.rpartition(";")
    return (base, c) if sep else (m, None)


def autoprueba(ruta):
    fallas = 0
    for linea in open(ruta, encoding="utf-8"):
        if not linea.strip():
            continue
        e = json.loads(linea)
        m = e["request"]["m"]
        base, c = partir(m)
        err = e["response"].get("error") if isinstance(e["response"], dict) else None
        v = valido(base, c)
        if err == "E201":
            ok = v is None
        elif err == "E202":
            ok = v is False
        else:
            ok = v is True
        fallas += not ok
        print(f"{e['n']:2d} {m:38s} control={control(base):3d} {'ok' if ok else 'FALLA'}")
    print(f"{'todo calza' if not fallas else str(fallas) + ' fallas'} sobre los ejemplos de {ruta}")
    return fallas


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(__doc__)
        sys.exit(2)
    arg = sys.argv[1]
    if arg.endswith(".jsonl"):
        sys.exit(1 if autoprueba(arg) else 0)
    print(control(arg))
