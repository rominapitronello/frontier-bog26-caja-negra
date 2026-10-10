#!/usr/bin/env python3
"""Caja negra de práctica: cinco puertas, decisión determinista y cambio furtivo.

Autora: Sol <sol@pasaelfiltro.cl>. Python >= 3.9, sólo stdlib.
No importar este módulo en el agente que investiga: es el oráculo de prueba.
"""

import argparse
import base64
import binascii
import hashlib
import hmac
import json
import threading
from http.cookies import CookieError, SimpleCookie
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlsplit

MAX_BODY = 64 * 1024
MODOS = ("A", "B", "C", "D", "E")


class Estado:
    """Todo acceso y avance de fase se protege con el mismo lock."""

    def __init__(self, acceso, cambia_a, cambia_tras, semilla):
        self.acceso = acceso
        self.cambia_a = cambia_a
        self.cambia_tras = cambia_tras
        self.semilla = semilla
        self.aciertos = 0
        self.cambiado = False
        self.lock = threading.RLock()
        self.tickets = set()
        self.ticket_num = 0
        self.cookie = hashlib.sha256(("visita:" + str(semilla)).encode()).hexdigest()[:24]
        self.clave = hashlib.sha256(("clave:" + str(semilla)).encode()).hexdigest()

    def emitir_ticket(self):
        self.ticket_num += 1
        ticket = hashlib.sha256(
            ("turno:%s:%s" % (self.semilla, self.ticket_num)).encode()
        ).hexdigest()[:32]
        self.tickets.add(ticket)
        return ticket

    def contar_exito(self, ticket=None):
        if ticket is not None:
            self.tickets.discard(ticket)
        self.aciertos += 1
        if (not self.cambiado and self.cambia_a is not None
                and self.aciertos == self.cambia_tras):
            self.acceso = self.cambia_a
            self.cambiado = True
            self.tickets.clear()


def decidir(dato):
    """La regla no aparece en las respuestas; se documenta en SOLUCIONES.md."""
    if not isinstance(dato, dict) or set(dato) != {"meses", "categoria", "respaldo"}:
        raise ValueError("se espera un objeto con meses, categoria y respaldo")
    meses, categoria, respaldo = dato["meses"], dato["categoria"], dato["respaldo"]
    if type(meses) is not int or not (0 <= meses <= 120):
        raise ValueError("meses debe ser entero entre 0 y 120")
    if categoria not in ("regular", "urgente") or type(categoria) is not str:
        raise ValueError("categoria debe ser regular o urgente")
    if type(respaldo) is not bool:
        raise ValueError("respaldo debe ser booleano")
    puntos = min(meses, 24) + (8 if categoria == "urgente" else 0) + (5 if respaldo else 0)
    return {"decision": "si" if puntos >= 18 else "no"}


class Manejador(BaseHTTPRequestHandler):
    server_version = "Practica/1.0"

    @property
    def estado(self):
        return self.server.estado

    def responder(self, codigo, cuerpo, headers=None):
        datos = json.dumps(cuerpo, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
        self.send_response(codigo)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(datos)))
        self.send_header("Cache-Control", "no-store")
        for k, v in (headers or {}).items():
            self.send_header(k, v)
        self.end_headers()
        self.wfile.write(datos)

    def error_pista(self, codigo, error, pista):
        self.responder(codigo, {"error": error, "pista": pista})

    def do_GET(self):
        ruta = urlsplit(self.path).path
        with self.estado.lock:
            if ruta in ("/", "/salud"):
                return self.responder(200, {"servicio": "practica", "estado": "disponible"})
            if ruta == "/recepcion" and self.estado.acceso == "A":
                return self.responder(200, {"mensaje": "visita iniciada"},
                                      {"Set-Cookie": "visita=%s; HttpOnly; SameSite=Strict; Path=/" % self.estado.cookie})
            if ruta == "/desafio" and self.estado.acceso == "B":
                return self.responder(200, {"turno": self.estado.emitir_ticket(), "uso": "una respuesta"})
            if ruta == "/clave" and self.estado.acceso == "D":
                return self.responder(200, {"material": self.estado.clave, "familia": "hash"})
            return self.error_pista(404, "No hay información disponible aquí",
                                    "La recepción no publica un directorio de sus puertas.")

    def do_POST(self):
        return self.procesar("POST")

    def do_PUT(self):
        return self.procesar("PUT")

    def procesar(self, metodo):
        ruta = urlsplit(self.path).path
        with self.estado.lock:
            modo = self.estado.acceso
            if modo == "E":
                if metodo != "PUT":
                    return self.error_pista(405, "Método no admitido",
                                            "Esta ventanilla reemplaza mensajes en vez de crearlos.")
                if ruta != "/buzon":
                    return self.error_pista(404, "Destino desconocido",
                                            "La ventanilla actual no vive en la ruta habitual.")
            else:
                if metodo != "POST":
                    return self.error_pista(405, "Método no admitido",
                                            "Esta ventanilla acepta mensajes creados por el cliente.")
                if ruta != "/query":
                    return self.error_pista(404, "Destino desconocido",
                                            "Prueba la entrada habitual para consultas.")

            tipo = self.headers.get("Content-Type", "").split(";", 1)[0].strip().lower()
            esperado = "application/octet-stream" if modo == "C" else "application/json"
            if tipo != esperado:
                return self.error_pista(415, "Sobre inesperado",
                                        "El mensaje viaja embalado, no en JSON visible." if modo == "C"
                                        else "Esta ventanilla espera un documento JSON ordinario.")

            if self.headers.get("Transfer-Encoding"):
                return self.error_pista(400, "Transferencia no admitida",
                                        "Envía el tamaño del mensaje sin fragmentarlo.")
            try:
                tamano = int(self.headers.get("Content-Length", "-1"))
            except ValueError:
                tamano = -1
            if tamano < 0:
                return self.error_pista(411, "Falta longitud",
                                        "Incluye el tamaño del cuerpo en bytes.")
            if tamano > MAX_BODY:
                return self.error_pista(413, "Mensaje demasiado grande",
                                        "Reduce el tamaño del sobre.")
            cuerpo = self.rfile.read(tamano)

            ticket = None
            if modo == "A":
                try:
                    cookies = SimpleCookie()
                    cookies.load(self.headers.get("Cookie", ""))
                    visita = cookies.get("visita")
                    valor = visita.value if visita is not None else ""
                except CookieError:
                    valor = ""
                if not hmac.compare_digest(valor, self.estado.cookie):
                    return self.error_pista(401, "Visita desconocida",
                                            "La autorización sobrevive entre peticiones como estado del navegador; empieza por recepción.")
            elif modo == "B":
                ticket = self.headers.get("X-Turno", "")
                if ticket not in self.estado.tickets:
                    return self.error_pista(401, "Turno ausente o vencido",
                                            "Antes de cada envío, pide una invitación efímera al mostrador de desafíos.")
            elif modo == "D":
                firma = self.headers.get("X-Firma", "")
                esperada = hmac.new(self.estado.clave.encode(), cuerpo, hashlib.sha256).hexdigest()
                if not hmac.compare_digest(firma, esperada):
                    return self.error_pista(401, "Sello no coincide",
                                            "La solicitud se valida con un resumen firmado de sus bytes exactos; pide material de clave.")

            if modo == "C":
                try:
                    cuerpo = base64.b64decode(cuerpo, validate=True)
                except (ValueError, binascii.Error):
                    return self.error_pista(400, "Embalaje dañado",
                                            "La carga debe decodificarse antes de leer el JSON.")
            try:
                dato = json.loads(cuerpo.decode("utf-8"))
            except (UnicodeDecodeError, json.JSONDecodeError):
                return self.error_pista(400, "Documento ilegible",
                                        "El mensaje interior debe ser JSON válido.")
            try:
                resultado = decidir(dato)
            except ValueError as error:
                return self.error_pista(422, "Entrada inválida", str(error))

            # La N-ésima respuesta todavía pertenece al acceso antiguo.
            # Sólo después de contarla cambia la puerta; los intentos fallidos no cuentan.
            self.estado.contar_exito(ticket)
            return self.responder(200, resultado)


def main():
    parser = argparse.ArgumentParser(description="Servicio opaco local de práctica")
    parser.add_argument("--puerto", type=int, default=8765)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--acceso", choices=MODOS, default="A")
    parser.add_argument("--cambia-a", choices=MODOS)
    parser.add_argument("--cambia-tras", type=int, default=40)
    parser.add_argument("--semilla", type=int, default=7)
    args = parser.parse_args()
    if not 0 <= args.puerto <= 65535:
        parser.error("--puerto debe estar entre 0 y 65535")
    if args.cambia_tras < 1:
        parser.error("--cambia-tras debe ser >= 1")
    if args.cambia_a == args.acceso:
        parser.error("--cambia-a debe ser distinto de --acceso")
    servidor = ThreadingHTTPServer((args.host, args.puerto), Manejador)
    servidor.estado = Estado(args.acceso, args.cambia_a, args.cambia_tras, args.semilla)
    print("Servicio de práctica escuchando en http://%s:%d" % servidor.server_address, flush=True)
    try:
        servidor.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        servidor.server_close()


if __name__ == "__main__":
    main()