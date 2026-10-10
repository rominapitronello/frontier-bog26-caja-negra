"""las cuatro piezas del preregistro (PREDICCION_INCIDENTE.md) se cambian con datos, sin tocar el código.

    python3 pruebas/test_piezas.py

por cada pieza: una copia de gemelo/modelo.json con un cambio plausible para el incidente, un gemelo levantado
con esa copia (GEMELO_MODELO) y una secuencia corta que muestra que la respuesta cambia como se espera. y el
modelo de hoy, sin cambios, sigue respondiendo como el original.
"""
import json, os, socket, subprocess, sys, tempfile, time, unittest, http.client

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RAIZ, "herramientas"))
from control import control

TOKEN = "prueba-piezas"


def c(cuerpo):
    return f"{cuerpo};{control(cuerpo)}"


class Gemelo:
    def __init__(self, cambio=None):
        modelo = json.load(open(os.path.join(RAIZ, "gemelo", "modelo.json"), encoding="utf-8"))
        if cambio:
            cambio(modelo)
        self.archivo = tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8")
        json.dump(modelo, self.archivo, ensure_ascii=False); self.archivo.close()
        s = socket.socket(); s.bind(("127.0.0.1", 0)); self.puerto = s.getsockname()[1]; s.close()
        env = dict(os.environ, GEMELO_TOKEN=TOKEN, PORT=str(self.puerto), GEMELO_MODELO=self.archivo.name)
        self.proc = subprocess.Popen([sys.executable, os.path.join(RAIZ, "gemelo", "servidor.py")], env=env,
                                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        for _ in range(50):
            try:
                self.pedir("GET", "/health"); break
            except OSError:
                time.sleep(0.1)

    def pedir(self, metodo, ruta, cuerpo=None):
        con = http.client.HTTPConnection("127.0.0.1", self.puerto, timeout=5)
        con.request(metodo, ruta, body=cuerpo, headers={"Authorization": f"Bearer {TOKEN}"})
        r = con.getresponse(); datos = json.loads(r.read() or b"null"); con.close()
        return r.status, datos

    def m(self, mensaje):
        return self.pedir("POST", "/msg", json.dumps({"m": mensaje}))

    def cerrar(self):
        self.proc.terminate(); self.proc.wait(); os.unlink(self.archivo.name)


class Piezas(unittest.TestCase):
    def secuencia(self, cambio, pasos):
        g = Gemelo(cambio)
        try:
            g.pedir("POST", "/__reset")
            return [g.m(p) for p in pasos]
        finally:
            g.cerrar()

    def test_hoy_sin_cambios(self):
        r = self.secuencia(None, [c("ALTA;Lucia"), c("ALTA;Mateo"), c("CONSULTA;ac-0001"),
                                  c("TRANSFER;AC-0002;AC-0001;150000")])
        self.assertEqual(r[2][1]["error"], "E401")            # ids exactos
        self.assertEqual(r[3][1]["error"], "E506")            # límite antes que saldo

    def test_normalizacion(self):
        def cambio(mo): mo["normalizacion"]["ids"] = "mayusculas"
        r = self.secuencia(cambio, [c("ALTA;Lucia"), c("CONSULTA;ac-0001")])
        self.assertEqual(r[1], (200, {"cuenta_id": "AC-0001", "saldo": 0}))

    def test_orden(self):
        def cambio(mo):
            o = mo["orden"]["transfer"]; i, j = o.index("limite"), o.index("saldo"); o[i], o[j] = o[j], o[i]
        r = self.secuencia(cambio, [c("ALTA;Lucia"), c("ALTA;Mateo"), c("TRANSFER;AC-0002;AC-0001;150000")])
        self.assertEqual(r[2][1]["error"], "E507")            # ahora el saldo va antes que el límite

    def test_control(self):
        def cambio(mo): mo["control"]["compara"] = "entero"
        cuerpo = "CONSULTA;AC-0005"                            # su control es 2
        r = self.secuencia(cambio, [f"{cuerpo};02"])
        self.assertEqual(r[0][1]["error"], "E401")            # '02' ya vale (pasa el control, la cuenta no existe)

    def test_estado(self):
        def cambio(mo): mo["estado"]["bloqueo"]["tras_fallas"] = 2
        r = self.secuencia(cambio, [c("ALTA;Lucia"), c("ALTA;Mateo"), c("TRANSFER;AC-0001;AC-0002;1"),
                                    c("TRANSFER;AC-0001;AC-0002;1"), c("TRANSFER;AC-0001;AC-0002;1")])
        self.assertEqual(r[4][1]["error"], "E510")            # bloquea con dos fallas


if __name__ == "__main__":
    unittest.main(verbosity=2)
