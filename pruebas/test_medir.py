#!/usr/bin/env python3
"""Pruebas de medir.py con un gemelo HTTP local; jamás se consulta el original.

Sol <sol@pasaelfiltro.cl> · 2026-10-10.
"""

import json
import subprocess
import sys
import tempfile
import threading
import time
import unittest
from contextlib import contextmanager
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import medir


@contextmanager
def gemelo_falso(modo="bien"):
    registro = {"reset": 0, "pedidos": [], "pasos": 0}

    class Falso(BaseHTTPRequestHandler):
        def log_message(self, formato, *args):
            pass

        def do_POST(self):
            self.responder()

        def do_GET(self):
            self.responder()

        def responder(self):
            largo = int(self.headers.get("Content-Length", "0"))
            cuerpo = self.rfile.read(largo)
            registro["pedidos"].append({
                "ruta": self.path, "metodo": self.command,
                "auth": self.headers.get("Authorization"), "cuerpo": cuerpo,
            })
            if self.path == "/__reset":
                registro["reset"] += 1
                registro["pasos"] = 0
                if modo == "reset_mal":
                    self.enviar(409, '{"error":"reset"}')
                else:
                    self.enviar(200, '{"ok":true}')
                return
            registro["pasos"] += 1
            if modo == "lento":
                time.sleep(5.2)
            if self.path == "/salud" and self.command == "GET":
                self.enviar(200, '{"listo":true}')
            elif modo == "clave_mal":
                self.enviar(200, '{"b":3,"a":1}')
            elif modo == "float":
                self.enviar(200, '{"a":1.0,"b":2}')
            elif modo == "bool":
                self.enviar(200, '{"a":true,"b":2}')
            elif modo == "array":
                self.enviar(200, '[2,1]')
            elif modo == "texto":
                self.enviar(200, "hola\\n")
            elif modo == "texto-json-mal":
                self.enviar(200, "no es json")
            else:
                self.enviar(200, '{"b":2,"a":1}')

        def enviar(self, status, cuerpo):
            data = cuerpo.encode("utf-8")
            try:
                self.send_response(status)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(data)))
                self.end_headers()
                self.wfile.write(data)
            except (BrokenPipeError, ConnectionResetError):
                pass

    httpd = ThreadingHTTPServer(("127.0.0.1", 0), Falso)
    httpd.daemon_threads = True
    hilo = threading.Thread(target=httpd.serve_forever, daemon=True)
    hilo.start()
    try:
        yield "http://127.0.0.1:{}".format(httpd.server_port), registro
    finally:
        httpd.shutdown()
        httpd.server_close()
        hilo.join(timeout=2)


def caso(id_, seq="s1", response=None, **extra):
    c = {"id": id_, "seq": seq, "request": {"m": "PING;64"}, "status": 200,
         "response": {"a": 1, "b": 2} if response is None else response}
    c.update(extra)
    return c


def informe_local(casos, base, token="abc"):
    grupos = {}
    for c in casos:
        grupos.setdefault(c["seq"], []).append(c)
    return medir.medir(grupos, medir.preparar_url(base), token=token)


class MedirTest(unittest.TestCase):
    def test_json_objetos_no_importa_orden_claves_y_secuencias_completas(self):
        with gemelo_falso() as (base, r):
            # El agrupamiento respeta el orden relativo dentro de cada seq.
            casos = [caso(1, "s1"), caso(2, "s2"), caso(3, "s1"), caso(4, "s2")]
            with tempfile.TemporaryDirectory() as carpeta:
                destino = Path(carpeta) / "casos.jsonl"
                destino.write_text("\n".join(json.dumps(c) for c in casos) + "\n", encoding="utf-8")
                grupos = medir.leer_casos(destino)
                self.assertEqual([c["id"] for c in grupos["s1"]], [1, 3])
                res = medir.medir(grupos, medir.preparar_url(base), token="abc")
            self.assertEqual(res["secuencias_que_pasan"], 2)
            self.assertEqual(res["total_secuencias"], 2)
            self.assertEqual(r["reset"], 2)
            self.assertEqual(len(r["pedidos"]), 6)

    def test_falla_primera_diferencia_con_id(self):
        with gemelo_falso("clave_mal") as (base, r):
            casos = [caso(11), caso(12, response={"a": 999})]
            res = informe_local(casos, base)
            self.assertEqual(res["secuencias_que_pasan"], 0)
            self.assertEqual(res["resultados"][0]["primera_diferencia"]["id"], 11)
            self.assertEqual(res["resultados"][0]["primera_diferencia"]["campo"], "response")
            self.assertEqual(r["pasos"], 2)  # procesa toda la secuencia

    def test_1_vs_1_0_distinto_asuncion_documentada(self):
        self.assertFalse(medir.mismo_json(1, 1.0))
        self.assertTrue(medir.mismo_json({"a": 1, "b": 2}, {"b": 2, "a": 1}))
        with gemelo_falso("float") as (base, _):
            res = informe_local([caso(1)], base)
            self.assertEqual(res["secuencias_que_pasan"], 0)

    def test_bool_distinto_int_y_array_con_orden(self):
        self.assertFalse(medir.mismo_json(True, 1))
        self.assertFalse(medir.mismo_json([1, 2], [2, 1]))
        with gemelo_falso("bool") as (base, _):
            self.assertEqual(informe_local([caso(1)], base)["secuencias_que_pasan"], 0)
        with gemelo_falso("array") as (base, _):
            self.assertEqual(informe_local([caso(1, response=[1, 2])], base)["secuencias_que_pasan"], 0)

    def test_texto_exacto_y_json_con_texto_no_json(self):
        with gemelo_falso("texto") as (base, _):
            res = informe_local([caso(1, response="hola")], base)
            self.assertEqual(res["secuencias_que_pasan"], 0)
        with gemelo_falso("texto-json-mal") as (base, _):
            res = informe_local([caso(1, response={"a": 1})], base)
            self.assertEqual(res["secuencias_que_pasan"], 0)
        self.assertTrue(medir.igual_cuerpo('{"a":1,"b":2}', '{"b":2,"a":1}'))
        self.assertFalse(medir.igual_cuerpo("texto ", "texto"))
        self.assertTrue(medir.igual_cuerpo('"hola"', '"hola"'))

    def test_auth_sin_token_y_metodo_ruta(self):
        with gemelo_falso() as (base, r):
            casos = [caso(1, auth="sin token"), caso(2)]
            res = informe_local(casos, base, "secreto_test")
            self.assertEqual(res["secuencias_que_pasan"], 1)
            self.assertEqual([p["auth"] for p in r["pedidos"]], [
                "Bearer secreto_test", None, "Bearer secreto_test"
            ])
        with gemelo_falso() as (base, r):
            res = informe_local([caso(3, response={"listo": True}, metodo="GET", ruta="/salud")], base)
            self.assertEqual(res["secuencias_que_pasan"], 1)
            self.assertEqual(r["pedidos"][1]["metodo"], "GET")
            self.assertEqual(r["pedidos"][1]["ruta"], "/salud")
            self.assertEqual(r["pedidos"][1]["cuerpo"], b"")

    def test_reset_no_2xx_falla_sin_mandar_msg(self):
        with gemelo_falso("reset_mal") as (base, r):
            res = informe_local([caso(1)], base)
            self.assertEqual(res["secuencias_que_pasan"], 0)
            self.assertEqual(res["resultados"][0]["primera_diferencia"]["campo"], "reset")
            self.assertEqual(len(r["pedidos"]), 1)

    def test_timeout_por_paso_5s(self):
        with gemelo_falso("lento") as (base, _):
            inicio = time.monotonic()
            res = informe_local([caso(77)], base)
            self.assertEqual(res["secuencias_que_pasan"], 0)
            self.assertEqual(res["resultados"][0]["primera_diferencia"]["campo"], "transporte")
            self.assertLess(time.monotonic() - inicio, 5.9)

    def test_cli_json_en_archivo_y_codigo_salida(self):
        with gemelo_falso() as (base, _):
            with tempfile.TemporaryDirectory() as carpeta:
                entrada = Path(carpeta) / "ej.jsonl"
                salida = Path(carpeta) / "res.json"
                entrada.write_text(json.dumps(caso(1)) + "\n", encoding="utf-8")
                proc = subprocess.run([sys.executable, str(Path(medir.__file__)),
                    "--casos", str(entrada), "--gemelo", base, "--por", "seq", "--token", "secreto_test",
                    "--json", str(salida)], capture_output=True, text=True, timeout=12)
                self.assertEqual(proc.returncode, 0, proc.stderr)
                self.assertIn("Secuencias que pasan: 1/1", proc.stdout)
                dato = json.loads(salida.read_text(encoding="utf-8"))
                self.assertEqual(dato["secuencias_que_pasan"], 1)
                self.assertNotIn("secreto_test", salida.read_text(encoding="utf-8"))

    def test_original_bloqueado_sin_tocar_red(self):
        with self.assertRaises(medir.ErrorComparador):
            medir.preparar_url("https://caja-negra-production-c64f.up.railway.app")
        with self.assertRaises(medir.ErrorComparador):
            medir.preparar_url("https://caja-negra-production-c64f.up.railway.app.")

    def test_casos_invalidos_rechazados_antes_de_conectar(self):
        with tempfile.TemporaryDirectory() as carpeta:
            entrada = Path(carpeta) / "mal.jsonl"
            entrada.write_text('{"id":1,"seq":"s1","status":200}\n', encoding="utf-8")
            with self.assertRaises(medir.ErrorComparador):
                medir.leer_casos(entrada)


if __name__ == "__main__":
    unittest.main(verbosity=2)
