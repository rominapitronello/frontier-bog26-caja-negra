#!/usr/bin/env python3
"""Pruebas de caja negra por HTTP real, sin dependencias externas.

Autora: Sol <sol@pasaelfiltro.cl>.
"""
import base64
import hashlib
import hmac
import json
import socket
import subprocess
import sys
import time
import unittest
from contextlib import contextmanager
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

SERVICIO = Path(__file__).with_name("servicio.py")
CASO = {"meses": 5, "categoria": "regular", "respaldo": False}
CASO_SI = {"meses": 15, "categoria": "urgente", "respaldo": True}
MODOS = "ABCDE"


def puerto_libre():
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def consulta(base, ruta, metodo="GET", dato=None, headers=None):
    req = Request(base + ruta, data=dato, method=metodo, headers=headers or {})
    try:
        with urlopen(req, timeout=2) as respuesta:
            return respuesta.status, json.loads(respuesta.read()), respuesta.headers
    except HTTPError as error:
        return error.code, json.loads(error.read()), error.headers


@contextmanager
def servidor(acceso, cambia_a=None, cambia_tras=40, semilla=7):
    puerto = puerto_libre()
    comando = [sys.executable, str(SERVICIO), "--puerto", str(puerto),
               "--acceso", acceso, "--cambia-tras", str(cambia_tras),
               "--semilla", str(semilla)]
    if cambia_a is not None:
        comando += ["--cambia-a", cambia_a]
    proceso = subprocess.Popen(comando, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    base = "http://127.0.0.1:%d" % puerto
    try:
        for _ in range(100):
            if proceso.poll() is not None:
                raise AssertionError("el servidor terminó al arrancar")
            try:
                if consulta(base, "/")[0] == 200:
                    break
            except (URLError, OSError):
                time.sleep(0.03)
        else:
            raise AssertionError("el servicio no empezó a escuchar")
        yield base
    finally:
        proceso.terminate()
        try:
            proceso.wait(timeout=2)
        except subprocess.TimeoutExpired:
            proceso.kill()
            proceso.wait(timeout=2)


def enviar(base, modo, dato=CASO, reutilizar=None):
    """Cliente oráculo del test, no el cliente que aprende."""
    cuerpo = json.dumps(dato, separators=(",", ":")).encode()
    headers = {"Content-Type": "application/json"}
    ruta = "/query"
    metodo = "POST"
    if modo == "A":
        cookie = reutilizar
        if cookie is None:
            estado, _, encabezados = consulta(base, "/recepcion")
            assert estado == 200
            cookie = encabezados["Set-Cookie"].split(";", 1)[0]
        headers["Cookie"] = cookie
    elif modo == "B":
        turno = reutilizar
        if turno is None:
            estado, respuesta, _ = consulta(base, "/desafio")
            assert estado == 200
            turno = respuesta["turno"]
        headers["X-Turno"] = turno
    elif modo == "C":
        headers["Content-Type"] = "application/octet-stream"
        cuerpo = base64.b64encode(cuerpo)
    elif modo == "D":
        estado, respuesta, _ = consulta(base, "/clave")
        assert estado == 200
        headers["X-Firma"] = hmac.new(respuesta["material"].encode(), cuerpo, hashlib.sha256).hexdigest()
    elif modo == "E":
        metodo = "PUT"
        ruta = "/buzon"
    return consulta(base, ruta, metodo, cuerpo, headers)


class PruebasServicio(unittest.TestCase):
    def test_cinco_accesos_aceptan_y_rechazan(self):
        for modo in MODOS:
            with self.subTest(acceso=modo), servidor(modo) as base:
                # Una petición común sin autorización (o sin embalaje) debe fallar.
                mal = consulta(base, "/query", "POST", json.dumps(CASO).encode(),
                               {"Content-Type": "application/json"})
                self.assertNotEqual(mal[0], 200)
                self.assertTrue(mal[1].get("pista"))
                bien = enviar(base, modo, CASO)
                self.assertEqual(bien[0], 200)
                self.assertEqual(bien[1], {"decision": "no"})
                bien = enviar(base, modo, CASO_SI)
                self.assertEqual(bien[0], 200)
                self.assertEqual(bien[1], {"decision": "si"})
                self.assertEqual(enviar(base, modo, CASO)[1], {"decision": "no"})

    def test_ticket_uso_unico(self):
        with servidor("B") as base:
            estado, datos, _ = consulta(base, "/desafio")
            self.assertEqual(estado, 200)
            ticket = datos["turno"]
            self.assertEqual(enviar(base, "B", reutilizar=ticket)[0], 200)
            codigo, cuerpo, _ = enviar(base, "B", reutilizar=ticket)
            self.assertEqual(codigo, 401)
            self.assertIn("pista", cuerpo)
            self.assertEqual(enviar(base, "B")[0], 200)

    def test_cambio_en_n_mas_uno_y_no_por_fallos(self):
        for origen, destino in zip(MODOS, "BCDEA"):
            with self.subTest(transicion=origen+destino), servidor(origen, destino, 2) as base:
                # Los errores no consumen cupo.
                for _ in range(3):
                    self.assertNotEqual(consulta(base, "/query", "POST", b"{}",
                                                   {"Content-Type": "application/json"})[0], 200)
                self.assertEqual(enviar(base, origen)[0], 200)  # N=1
                self.assertEqual(enviar(base, origen)[0], 200)  # N=2
                # El próximo intento en modo viejo falla; el nuevo sí funciona.
                # Las excepciones de los ayudantes indican que ni el GET preparatorio existe.
                try:
                    viejo = enviar(base, origen)
                except AssertionError:
                    pass  # GET preparatorio del modo antiguo ya no existe.
                else:
                    self.assertNotEqual(viejo[0], 200)
                    self.assertIn("pista", viejo[1])
                self.assertEqual(enviar(base, destino)[0], 200)  # N+1
                self.assertEqual(enviar(base, destino)[0], 200)
                self.assertEqual(enviar(base, destino, CASO_SI)[1], {"decision": "si"})

    def test_validacion_no_cuenta_como_exito(self):
        with servidor("E", "A", 1) as base:
            codigo, datos, _ = enviar(base, "E", {"meses": True, "categoria": "regular", "respaldo": False})
            self.assertEqual(codigo, 422)
            self.assertIn("pista", datos)
            self.assertEqual(enviar(base, "E")[0], 200)
            self.assertEqual(enviar(base, "A")[0], 200)

    def test_semilla_reproducible(self):
        with servidor("B", semilla=123) as base:
            primero = consulta(base, "/desafio")[1]["turno"]
        with servidor("B", semilla=123) as base:
            segundo = consulta(base, "/desafio")[1]["turno"]
        self.assertEqual(primero, segundo)
        with servidor("B", semilla=124) as base:
            tercero = consulta(base, "/desafio")[1]["turno"]
        self.assertNotEqual(primero, tercero)


if __name__ == "__main__":
    unittest.main(verbosity=2)