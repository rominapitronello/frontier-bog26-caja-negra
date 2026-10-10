# Sol-03 · Oráculo interno ciego de la especificación

**Autoría:** Sol <sol@pasaelfiltro.cl> · 10 de octubre de 2026.  
**Base exclusiva de predicción:** `spec.md`, `material/README.md` y `material/pruebas/ejemplos.jsonl` en `main`, junto con el encargo. **No leí** `gemelo/`, `experimentos*.jsonl` ni `herramientas/`; **no consulté** al original ni al gemelo. Estos valores son **predicciones**, no observaciones.

## Entrega y cómo leerla

- `sol-03.jsonl`: **40 secuencias, 141 pedidos**, tamaño del set: **16×1**, **18×2–5**, **6×6–12**. IDs globales correlativos de 1 a 141. Ninguna secuencia ni mensaje individual coincide literalmente con los 20 ejemplos oficiales.
- Cada secuencia exige un `POST /__reset` **previo**, que no está en el JSONL y **no cuenta** en los 141 pedidos; cada fila posterior se envía en el orden de archivo, preservando el estado. `request`, `status` y `response` son mi predicción. `spec` cita IDs de la especificación; `hipotesis` explica qué mecanismo separa.
- Si se incluye `metodo`, `ruta` o `auth`, prevalece sobre los valores por defecto `POST`, `/msg` y token correcto. `auth: "sin token"` significa omitir Authorization; `auth: "otro token"` significa usar uno que no sea el autorizado. `cuerpo`, presente en `s03-32`, es el **cuerpo HTTP crudo exacto** y prevalece sobre `request: {}`: el servidor **no** recibe `{}`. El comparador / ejecutor debe respetarlo.
- Clasificar dos diferencias por separado: **(A) predicción Sol ≠ original:** corregir/precisar la spec; **(B) original ≠ gemelo:** corregir el gemelo. No cambiar las predicciones retrospectivamente. Si hay cambio temporal de versión, congelar la observación con hora/versión antes de atribuir causa.

## Control independiente

Implementé de cero ISO 7064 MOD 97-10 desde `spec.md` § 2, sin importar código del repo. La función calcula el módulo acumulando dígitos para no formar enteros gigantes:

```python
def control(mensaje):
    resto = 0
    for c in mensaje:
        if '0' <= c <= '9':
            digitos = c
        elif c.isascii() and 'A' <= c.upper() <= 'Z':
            digitos = str(ord(c.upper()) - 64)
        else:
            continue
        for d in digitos:
            resto = (10 * resto + int(d)) % 97
    return str(98 - (100 * resto) % 97)
```

**Autocomprobación local 20/20** sobre los ejemplos públicos: para cada control clasifiqué válido, inválido, mal formado o bypass PING; también la lectura de estado desde la spec reprodujo los 20 status y cuerpos conocidos, antes de generar las 141 predicciones. Checks fijos: `control('ALTA;Lucia') == '82'`, `control('CONSULTA;AC-0001') == '14'`, `control('PING') == '64'`. Esta autocomprobación **no prueba** que las nuevas predicciones coincidan con el original.

## Huecos, decisiones y posibles errores de la spec

| Fila de spec | Secuencia / pedido | Predicción elegida y alternativa que probará Claude |
|---|---|---|
| **TR-08**, ME-09 | **s03-40**, fila 138 | Tres rechazos E507 con un **E304 intercalado** y una consulta. Elegí que E304 no suma **ni reinicia** la racha, de modo que el cuarto intento da `409 E510`. Pero «no suman» no resuelve explícitamente si E303/E304/E401 interrumpen lo «consecutivo»: si E304 reinicia, sería `422 E507`. Es la pregunta más útil de esta batería. |
| **DC-03** (probable), DC-02 | **s03-31**, fila 69 | `ALNG` está a distancia de edición 2 de **ALTA** y **PING**. Predije `sugerencia: "ALTA"` por desempate alfabético. El desempate de la spec es **probable**, no confirmado para esta palabra. |
| **HA-05** (supuesto), HA-01 | **s03-33**, fila 75 | `HALT;0` devuelve `409 E520` y no detiene. En la spec `0` no está probado; alternativa: otra rama de validación / otra confirmación válida. La siguiente llamada PING distingue si detuvo. |
| **EN-03**, ER-20, HA-03 | **s03-34**, fila 82 | Tras HALT, `/MSG` da `404 E404` porque la ruta precede a la detención. La spec establece el orden pero no cita una prueba específica de `/MSG` estando detenido. |
| **EN-12**, EN-09, ER-20 | **s03-32**, filas 73–74 | Un texto crudo inválido de longitud corta da `E100`; **8.193 bytes** crudos inválidos dan `E101` antes de parsear JSON. `cuerpo` no debe reserializarse: hacerlo destruiría justamente la sonda. |
| **TR-06**, TR-07, AL-02 | **s03-27**, **s03-28**, **s03-35** | Nombre con espacio final ≠ nombre sin espacio (límite `E506` antes que saldo); dos titulares con exactamente igual nombre evitan el límite, incluso sin identidad verificada. Si aparecen diferencias, precisar si la comparación normaliza Unicode/espacios. |
| **TR-08**, RI-11 | **s03-36**, **s03-37** | Tres fallas por límite/saldo bloquean. Un depósito de 1 desbloquea; recibir transferencia **no** desbloquea. Una falla de esta secuencia puede ser regla o **orden de errores**, no solo saldo. |
| **AN-02**, AN-03, ME-08 | **s03-38**, **s03-39** | La anulación después de transferir el saldo puede volverlo negativo; las anulaciones cruzadas no deben duplicar ni perder fondos. Predicciones inferidas del orden y las operaciones descritas. |
| **AL-04** (supuesto) | **sin secuencia** | `AC-10000` después de diez mil altas no entra razonablemente en este presupuesto; no lo validé. Tampoco exploré `X-Req` porque el jurado **no** compara headers. |

## Recorrido resumido por categoría

- **s03-01–16:** rutas, query, autenticación, payload, parseo, segmentos, checksum antes de comando/aridad, cantidades inválidas, cuenta inexistente.
- **s03-17–34:** creación, ids solo tras éxito, titular duplicado, números y mayúsculas, cancelación idempotente, E401, límite inclusivo, sugerencia de typo, HALT y payload crudo.
- **s03-35–40:** evasión de límite entre titulares iguales, bloqueo/desbloqueo, recibir sin desbloquear, fraccionamiento, anulaciones cruzadas que dejan saldo negativo, errores intercalados en la racha.

## Límites del instrumento y control de la rúbrica

1. El alcance es **deliberadamente distinto del log de entrenamiento**: no hay repeticiones literales del material. Si varias secuencias fallan por el mismo error de precedencia, atribuir primero la causa compartida y no 40 errores independientes.
2. Es un oráculo **desde la especificación**, no una verdad sobre el servicio. Cuatro filas llevan `ambiguo` dentro del JSONL; las demás también están limitadas por las confianzas y omisiones de las filas citadas. El modelo local de predicción puede heredar una lectura equivocada de la spec; eso es precisamente lo que la validación debe detectar.
3. **No ejecutar contra el servicio original desde esta rama**. Claude líder dispone de las credenciales y controla el presupuesto y la evidencia. No ejecuté pruebas del gemelo ni el `smoke.sh` del proyecto: las pruebas locales solo verifican la forma del instrumento, el cálculo del control y la consistencia con los 20 ejemplos publicados.
4. Para la rúbrica: casos fáciles, difíciles, secuenciales y de borde → **presente**; métricas por secuencia y diferencias → Claude con comparador; adaptabilidad al incidente → volver a ejecutar exactamente estas secuencias antes/después (sin reescribir el set); costo en llamadas al original → **141** pedidos más **40 resets** si Claude corre una vez cada secuencia (181 requests HTTP incluyendo los resets; la cuota real también puede contar resets). Ninguna promesa de nota ni cobertura del set oculto.

**Siguiente paso (Claude líder):** correr la batería contra **original y gemelo** sin modificar las predicciones, y agregar debajo de esta nota resultados, discrepancias concretas y correcciones de spec/gemelo. Integrar esta rama solo con merge commit; el oráculo no fusiona.

— Sol <sol@pasaelfiltro.cl>