"""el dígito de control del servicio (spec § 2), hipótesis I1 · ver experimentos.jsonl.

N = el mensaje sin su último campo, leído como número decimal: cada dígito vale lo que es, cada letra
su posición en el alfabeto (A=1 … Z=26, sin importar mayúsculas), y ';' y '-' no aportan nada.
control = 98 - (100·N mod 97), un número de 2 a 98 escrito sin ceros a la izquierda: ISO 7064 MOD 97-10,
el verificador del IBAN. el servicio lo compara como texto ('2' vale, '02' no). log: ids 2-21, 24-30.

    python3 herramientas/control.py 'CONSULTA;AC-0001'      # → 14
"""
import sys

def digitos(cuerpo):
    out = []
    for c in cuerpo:
        if c.isdigit() and c.isascii():
            out.append(c)
        elif c.isascii() and c.isalpha():
            out.append(str(ord(c.upper()) - 64))
        # lo demás no aporta: ';', '-', espacio, é, ñ (log 44, 45, 47); el punto, por probar
    return "".join(out)

def control(cuerpo):
    r = 0
    for d in digitos(cuerpo):  # módulo 97 dígito a dígito: sirve para mensajes de cualquier largo
        r = (r * 10 + int(d)) % 97
    return 98 - (r * 100) % 97

if __name__ == "__main__":
    for a in sys.argv[1:]:
        print(control(a))
