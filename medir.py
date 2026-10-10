#!/usr/bin/env python3
"""Compara un gemelo HTTP con secuencias observadas, sin tocar el original.

Sol <sol@pasaelfiltro.cl> · 2026-10-10 · encargo sol-02.
Python 3.9+; solo biblioteca estándar.
"""

import argparse
import http.client
import json
import queue
import threading
import sys
from collections import OrderedDict
from pathlib import Path
from urllib.parse import urlsplit

TIMEOUT = 5.0
ORIGINAL_PROHIBIDO = "caja-negra-production-c64f.up.railway.app"


class ErrorComparador(Exception):
    """Entrada/configuración inválida: no se envía ninguna petición."""


def _sin_constantes_no_json(valor):
    raise ValueError("constante no estándar en JSON: " + valor)


def intentar_json(texto):
    """(es_json, dato): solo JSON estricto, incluida una cadena JSON escalar."""
    try:
        return True, json.loads(texto, parse_constant=_sin_constantes_no_json)
    except (ValueError, TypeError):
        return False, texto


def mismo_json(a, b):
    """Igualdad estructural, con tipo numérico estricto: 1 != 1.0 (supuesto)."""
    if type(a) is not type(b):
        return False
    if isinstance(a, dict):
        return a.keys() == b.keys() and all(mismo_json(a[k], b[k]) for k in a)
    if isinstance(a, list):
        return len(a) == len(b) and all(mismo_json(x, y) for x, y in zip(a, b))
    return a == b


def cuerpo_esperado(valor):
    """En JSONL, string significa cuerpo HTTP textual; otros tipos, cuerpo JSON.

    Para representar un cuerpo que es una cadena JSON, usar en el JSONL
    `"response":"\\\"texto\\\""`. Para texto plano `"response":"texto"`.
    """
    if isinstance(valor, str):
        return valor
    return json.dumps(valor, ensure_ascii=False, separators=(",", ":"), allow_nan=False)


def igual_cuerpo(esperado, recibido):
    """Si ambos textos son JSON se compara estructura; si no, texto exacto."""
    es_json_1, e = intentar_json(cuerpo_esperado(esperado))
    es_json_2, r = intentar_json(recibido)
    if es_json_1 and es_json_2:
        return mismo_json(e, r)
    return cuerpo_esperado(esperado) == recibido


def mostrar_cuerpo(texto):
    es_json, parsed = intentar_json(texto)
    return parsed if es_json else texto


def leer_casos(ruta):
    grupos = OrderedDict()
    try:
        with open(ruta, "r", encoding="utf-8") as origen:
            for numero, linea in enumerate(origen, 1):
                if not linea.strip():
                    continue
                try:
                    item = json.loads(linea, parse_constant=_sin_constantes_no_json)
                except (ValueError, TypeError) as exc:
                    raise ErrorComparador("línea {}: JSON inválido: {}".format(numero, exc)) from exc
                if not isinstance(item, dict):
                    raise ErrorComparador("línea {}: se esperaba objeto JSON".format(numero))
                obligatorios = ("id", "seq", "request", "status", "response")
                ausentes = [campo for campo in obligatorios if campo not in item]
                if ausentes:
                    raise ErrorComparador("línea {}: faltan {}".format(numero, ", ".join(ausentes)))
                if not isinstance(item["seq"], (str, int)) or isinstance(item["seq"], bool):
                    raise ErrorComparador("línea {}: seq debe ser string o entero".format(numero))
                if type(item["status"]) is not int or not 100 <= item["status"] <= 599:
                    raise ErrorComparador("línea {}: status HTTP inválido".format(numero))
                metodo = item.get("metodo", "POST")
                ruta_http = item.get("ruta", "/msg")
                if not isinstance(metodo, str) or not metodo or not metodo.isascii() or not all(ch.isalpha() for ch in metodo):
                    raise ErrorComparador("línea {}: método inválido".format(numero))
                if not isinstance(ruta_http, str) or not ruta_http.startswith("/") or ruta_http.startswith("//") or "\r" in ruta_http or "\n" in ruta_http:
                    raise ErrorComparador("línea {}: ruta debe ser ruta relativa que empiece con /".format(numero))
                if item.get("auth") not in (None, "sin token"):
                    raise ErrorComparador("línea {}: auth solo admite 'sin token'".format(numero))
                item["metodo"] = metodo.upper()
                item["ruta"] = ruta_http
                grupos.setdefault(item["seq"], []).append(item)
    except (OSError, UnicodeError) as exc:
        raise ErrorComparador("no se pudo leer {}: {}".format(ruta, exc)) from exc
    if not grupos:
        raise ErrorComparador("el archivo de casos está vacío")
    return grupos


def preparar_url(gemelo):
    url = urlsplit(gemelo)
    if url.scheme not in ("http", "https") or not url.hostname or url.username or url.password or url.query or url.fragment:
        raise ErrorComparador("--gemelo requiere URL HTTP(S) válida sin credenciales, query ni fragmento")
    if url.hostname.lower().rstrip(".") == ORIGINAL_PROHIBIDO:
        raise ErrorComparador("PROHIBIDO: --gemelo apunta al original, no se hacen consultas")
    try:
        puerto = url.port
    except ValueError as exc:
        raise ErrorComparador("puerto inválido del gemelo") from exc
    return url.scheme, url.hostname, puerto, url.path.rstrip("/")


def pedir(configuracion, metodo, ruta, carga=None, token=None):
    """Un paso HTTP tiene límite total de 5 s, incluidos envío y lectura.

    El worker es daemon, por lo que un servidor que gotea bytes indefinidamente
    no deja bloqueado al comparador. No sigue redirects (http.client).
    """
    esquema, host, puerto, prefijo = configuracion
    resultado = queue.Queue(maxsize=1)

    def enviar():
        clase = http.client.HTTPSConnection if esquema == "https" else http.client.HTTPConnection
        conn = clase(host, port=puerto, timeout=TIMEOUT)
        headers = {}
        if token is not None:
            headers["Authorization"] = "Bearer " + token
        if carga is not None:
            headers["Content-Type"] = "application/json"
        try:
            conn.request(metodo, prefijo + ruta, body=carga, headers=headers)
            respuesta = conn.getresponse()
            datos = respuesta.read()
            resultado.put((True, {"status": respuesta.status, "response": datos.decode("utf-8", errors="strict")}))
        except Exception as exc:
            resultado.put((False, exc))
        finally:
            conn.close()

    hilo = threading.Thread(target=enviar, daemon=True)
    hilo.start()
    try:
        exito, dato = resultado.get(timeout=TIMEOUT)
    except queue.Empty as exc:
        raise TimeoutError("paso HTTP superó 5 s") from exc
    if exito:
        return dato
    raise dato


def _respuesta_caso(configuracion, caso, token):
    metodo = caso.get("metodo", "POST").upper()
    # GET y HEAD no llevan cuerpo aunque el JSONL documente request:{}.
    carga = None if metodo in ("GET", "HEAD") or caso["request"] is None else json.dumps(
        caso["request"], ensure_ascii=False, separators=(",", ":"), allow_nan=False
    ).encode("utf-8")
    usado = None if caso.get("auth") == "sin token" else token
    return pedir(configuracion, metodo, caso.get("ruta", "/msg"), carga, usado)


def _error_primero(caso, campo, recibido, detalle=None):
    real = None if recibido is None else {"status": recibido["status"], "response": mostrar_cuerpo(recibido["response"])}
    return {
        "id": caso["id"], "campo": campo,
        "esperado": {"status": caso["status"], "response": caso["response"]},
        "obtenido": real, "detalle": detalle,
    }


def medir(grupos, configuracion, token=None):
    resultados = []
    for seq, casos in grupos.items():
        primer_error = None
        try:
            # El reset no pertenece a los pasos puntuados, pero es obligatorio.
            reset = pedir(configuracion, "POST", "/__reset", token=token)
            if not 200 <= reset["status"] < 300:
                primer_error = _error_primero(casos[0], "reset", reset, "POST /__reset no devolvió 2xx")
        except (OSError, UnicodeError, http.client.HTTPException) as exc:
            primer_error = _error_primero(casos[0], "reset", None, type(exc).__name__ + ": " + str(exc))
        if primer_error is None:
            for caso in casos:
                try:
                    real = _respuesta_caso(configuracion, caso, token)
                except (OSError, UnicodeError, ValueError, TypeError, http.client.HTTPException) as exc:
                    if primer_error is None:
                        primer_error = _error_primero(caso, "transporte", None, type(exc).__name__ + ": " + str(exc))
                    continue
                if primer_error is None:
                    if caso["status"] != real["status"]:
                        primer_error = _error_primero(caso, "status", real)
                    elif not igual_cuerpo(caso["response"], real["response"]):
                        primer_error = _error_primero(caso, "response", real)
        resultados.append({"seq": seq, "pasa": primer_error is None, "primera_diferencia": primer_error})
    exitosas = sum(item["pasa"] for item in resultados)
    return {
        "secuencias_que_pasan": exitosas,
        "total_secuencias": len(resultados),
        "resultados": resultados,
        "supuesto_numerico": "1 y 1.0 son diferentes por tipo JSON; no confirmado por el juez",
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description="Comparador secuencial del gemelo (no consultar original)")
    parser.add_argument("--casos", required=True, help="JSONL de casos con seq, request, status y response")
    parser.add_argument("--gemelo", required=True, help="URL base del reemplazo")
    parser.add_argument("--token", default=None, help="token de acceso del gemelo; no se imprime ni persiste")
    parser.add_argument("--por", default="seq", choices=["seq"], help="agrupar casos por secuencia")
    parser.add_argument("--json", nargs="?", const="medicion.json", metavar="ARCHIVO", help="guardar informe en JSON (por defecto medicion.json)")
    args = parser.parse_args(argv)
    try:
        config = preparar_url(args.gemelo)
        grupos = leer_casos(args.casos)
        informe = medir(grupos, config, token=args.token)
        print("Secuencias que pasan: {}/{}".format(informe["secuencias_que_pasan"], informe["total_secuencias"]))
        for linea in informe["resultados"]:
            error = linea["primera_diferencia"]
            if error is not None:
                print("FALLA seq={!r} id={!r} campo={} esperado={} obtenido={}{}".format(
                    linea["seq"], error["id"], error["campo"],
                    json.dumps(error["esperado"], ensure_ascii=False),
                    json.dumps(error["obtenido"], ensure_ascii=False),
                    (" detalle=" + error["detalle"]) if error["detalle"] else "",
                ))
        if args.json is not None:
            Path(args.json).write_text(json.dumps(informe, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            print("Informe JSON: " + args.json)
        return 0 if informe["secuencias_que_pasan"] == informe["total_secuencias"] else 1
    except (ErrorComparador, OSError, UnicodeError) as exc:
        print("medir: " + str(exc), file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
