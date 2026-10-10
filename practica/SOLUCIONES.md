# SOLUCIONES · **NO ENTREGAR AL AGENTE INVESTIGADOR**

**Autora:** Sol <sol@pasaelfiltro.cl> · 10 de octubre de 2026.

Este archivo es exclusivamente para quien diseña/verifica el experimento. La separación con el agente investigador exige no permitirle leer este repositorio ni sus fuentes durante las pruebas (el repo es público, así que no constituye una barrera de seguridad).

Los cinco accesos permiten la **misma** decisión; solo cambia el transporte y la autorización. En todas las solicitudes exitosas el cuerpo *lógico* de JSON es un objeto con claves exactas `meses`, `categoria`, `respaldo`.

| Modo | Acceso correcto | Indicio al equivocarse |
|---|---|---|
| **A · Cookie de recepción** | `GET /recepcion` entrega `Set-Cookie: visita=...`. Reenviar esa cookie en `POST /query` con `Content-Type: application/json` y JSON normal. | `401`, memoria del navegador y recepción. |
| **B · Turno de uso único** | `GET /desafio` entrega `turno`; enviarlo en `X-Turno` con `POST /query`, `Content-Type: application/json`, JSON normal. El turno se consume al tener respuesta válida y no se reutiliza. | `401`, mostrador de desafíos y turno efímero. |
| **C · Cuerpo envuelto** | `POST /query`, `Content-Type: application/octet-stream`, bytes de `base64.b64encode(json_bytes)`. | `415` si envías JSON común, `400` si base64 es incorrecto; habla de sobre y embalaje. |
| **D · Firma HMAC del cuerpo** | `GET /clave` entrega `material` (texto UTF-8), calcular `HMAC-SHA256(material.encode(), body_exacto).hexdigest()` y colocarlo en `X-Firma` con `POST /query`, `Content-Type: application/json` y los mismos bytes firmados. | `401`, resumen firmado de bytes exactos y material de clave. |
| **E · Método y destino distintos** | `PUT /buzon`, `Content-Type: application/json`, JSON normal. | `405` por método equivocado, `404` por destino equivocado. |

Los `GET` de preparación solo funcionan en su modo respectivo; no cambian el contador. Un HTTP 200 de la operación de decisión sí lo cambia. Si se parte en A, se pide `--cambia-a C --cambia-tras 40`: las 40 solicitudes válidas con A responden normalmente; inmediatamente después, la siguiente con A falla y una con C funciona. La transición es silenciosa, sin indicador de fase en el cuerpo ni en `/salud`.

## Decisión oculta tras la puerta

El cuerpo lógico es, por ejemplo, `{"meses":5,"categoria":"regular","respaldo":false}`.

```python
puntos = min(meses, 24) + (8 if categoria == 'urgente' else 0) + (5 if respaldo else 0)
decision = 'si' if puntos >= 18 else 'no'
```

Validaciones: `meses` debe ser `int` exacto (no acepta booleanos) entre 0 y 120; `categoria` `regular` o `urgente`; `respaldo` `bool` exacto; ninguna clave adicional o ausente. Errores: HTTP 422 con descripción. No se exponen puntos ni umbral en las respuestas correctas.

## Oráculo mínimo

`python3 practica/probar.py` es el oráculo HTTP autónomo; levanta instancias distintas y comprueba todos los accesos, el uso único, la semilla y el cambio en N+1. **No importar funciones de `servicio.py` en el cliente que aprende**: el acceso al código anularía la medición.