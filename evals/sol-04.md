# sol-04 · secuencias retenidas con estado

**Sol entrega 30 secuencias: 20 de 6–10 pedidos y 10 de 3–4, 189 pedidos en el archivo; 219 contando los 30 resets iniciales del oráculo. Un solo `HALT;1`.** Ninguna secuencia copia `sol-03`. Son **predicciones por contrastar**, no respuestas observadas ni hallazgos confirmados.

Fuentes: `spec.md`, `material/README.md`, los 20 ejemplos del material, `evals/sol-03.jsonl`, el encargo y la rúbrica. Preparación iniciada sobre `cde2fe69ebeafc301a7917572a5beaa3b341e405`; antes de publicar se revisó la spec actual (blob `078960cdb94da0af94ea403c2f1355ca6454acb9`) en `efdb61ed82aae7e0c6d47a36b6cfd6c1bcd5a58c`. EN-15 y TR-11 ya resolvieron dos preguntas de la primera versión local: **se reemplazaron los casos de claves duplicadas y la pregunta de restaurar el bloqueo tras un depósito normal**. El control lo calcula código propio; no se importa código del repo.

**Límite de independencia:** esta misma ventana hizo antes sol-05 y allí leyó `herramientas/control.py`, `herramientas/lote.py` y nombres/códigos del log. No puede certificarse como completamente ciega. Para sol-04 no se abrieron `gemelo/`, `experimentos*.jsonl` ni `herramientas/`; las predicciones se construyeron desde las fuentes permitidas. No se consultó el original ni el gemelo.

## Qué queda abierto y qué secuencia lo separa

Los números de paso son posiciones dentro de cada secuencia, sin contar su reset inicial. Los campos `spec` de cada pedido citan las filas aplicables; `ambiguo` distingue una hipótesis primaria de sus consecuencias.

| Secuencia | Pedidos | Fila y silencio o afirmación a refutar | Paso discriminante y mejor predicción |
|---|---:|---|---|
| s04-01 | 7 | TR-08: efecto de E201 sobre una racha de dos | 7: E510 si no la corta; E507 si la reinicia |
| s04-02 | 7 | TR-08: efecto de E202 | 7: E510 frente a E507 |
| s04-03 | 7 | TR-08: efecto de E302 | 7: E510 frente a E507 |
| s04-04 | 7 | TR-08: efecto de E301 | 7: E510 frente a E507 |
| s04-05 | 7 | TR-08: efecto de JSON inválido, E100 | 7: E510 frente a E507 |
| s04-06 | 7 | TR-08: efecto de m nulo, E102 | 7: E510 frente a E507 |
| s04-07 | 10 | TR-08/AN-03: anular el éxito que había borrado una racha, ¿restaura el contador anterior? | 9: éxito OP-0003; restaurar dos fallas daría E510 |
| s04-08 | 8 | DE-02/TR-11: LF en el depósito con la cuenta ya bloqueada | 6: hipótesis de aceptar LF y desbloquear; 8 entonces E507; si LF fue rechazado, E510 |
| s04-09 | 10 | AN-05/06: LF terminal en el id de una operación, dentro de una cadena de tres cuentas | 7: E402 por id literal; si recorta LF, anula OP-0003 y cambian los saldos |
| s04-10 | 8 | EN-01/06: contrato de HEAD con estado; TR-06: refutación de comparación literal de titulares Unicode | 7: HEAD 404 vacío; 4 contrasta José con Jose + U+0301 |
| s04-11 | 6 | EN-01/06: HEAD; TR-06: espacio ASCII frente a U+00A0 | 5: HEAD 404 vacío; 4 predice E506 por nombres distintos |
| s04-12 | 8 | DE-01/ME-03: idempotencia de un depósito idéntico reintentado | 4: otro abono, OP-0002; después se gastan ambos y se anula el segundo |
| s04-13 | 8 | TR-02/DE-02: LF terminal en un monto durante una secuencia | 4: hipótesis de aceptación por regex con `$`; alternativa E303 |
| s04-14 | 8 | DE-02: diez cifras + LF; CO-01/DE-03: acumulación por encima de diez cifras | 4: hipótesis de aceptar LF, saldo 18.888.888.887; luego transferencia propia y anulación dejan -1.111.111.111 |
| s04-15 | 10 | EN-07: cuerpo JSON truncado en reset; ME-02: reutilización posterior de ids | 5: ok y reset; después OP-0002 viejo no existe y OP-0001 nombra el abono nuevo |
| s04-16 | 9 | HA-03/EN-01/06: HEAD detenido y regreso con reset | 4: HEAD 404 vacío; 5 no anula; tras reset AC-0001 y OP-0001 vuelven a empezar |
| s04-17 | 7 | EN-07/TR-08: reset sin token en medio de la racha | 7: E510; limpiar racha daría E507, borrar cuentas daría E401 |
| s04-18 | 7 | TR-08 enumera E401 de TRANSFER, no E401 de CONSULTA | 7: E510 si la consulta fallida no corta la racha |
| s04-19 | 8 | DE-02/TR-08: aceptar LF en un depósito cambia la racha posterior | 5: abona 1; 7 entonces puede transferir, en vez de E510 |
| s04-20 | 8 | EN-01/07: GET de reset intercalado con cuentas y operaciones | 4: E404 y conservar estado; si existe un alias, borra cuentas y cambian transferencia, anulación e ids |
| s04-21 | 3 | DE-02: `$` no distingue match de fullmatch; LF terminal no está probado | 2: hipótesis de aceptar 7 + LF; alternativa E303; consulta separa 7 de 0 |
| s04-22 | 3 | DE-02: posible contraejemplo al patrón ASCII, si el autor usó `\d` | 2: hipótesis de aceptar 1٢ como 12; patrón escrito en spec da E303 |
| s04-23 | 3 | EN-08 solo habla de Content-Type: ninguna fila define Content-Encoding | 2: JSON sin comprimir con header gzip; hipótesis de ignorarlo y abonar 5; un decodificador lo rechazaría |
| s04-24 | 3 | EN-09: ninguna fila fija la tolerancia a BOM UTF-8 | 2: E100; parser que tolera BOM abonaría 5 |
| s04-25 | 3 | EN-03: ruta exacta antes o después de decodificar %6d | 2: /%6dsg da E404; decodificarla permitiría el depósito |
| s04-26 | 3 | EN-01: HEAD /msg con cuerpo válido, transporte y posible efecto de ese cuerpo | 2: 404 vacío, sin abonar; la consulta debe seguir en cero |
| s04-27 | 3 | EN-07: cuerpo que no es JSON en reset | 2: ok y borrar cuenta; exigir JSON podría conservarla con E100 |
| s04-28 | 3 | EN-01/03: reset con escape porcentual en el path | 2: /%5f_reset da E404 y conserva la cuenta; decodificado borra |
| s04-29 | 4 | EN-01/07: GET reset con saldo, versión corta que aísla la respuesta | 3: E404 y conservar 5; un alias que resetee borraría la cuenta |
| s04-30 | 4 | EN-01: OPTIONS de reset no está probado; puede tener un handler automático | 3: E404; alternativa 200/204 con otro cuerpo; el saldo debe seguir en 5 |

**Dudas que ya están resueltas:** TR-08 sí dice que anular o recibir una transferencia no reinicia la racha, y que E303/E304/E401 de TRANSFER no la suman ni la cortan. EN-15 ya fija la última clave JSON y TR-11 la no restauración del bloqueo tras anular un depósito normal. No se presentan como silencios nuevos. s04-07 pregunta si deshacer una transferencia exitosa restaura su racha anterior; s04-08 pregunta si el depósito con LF fue aceptado, usando TR-11 para predecir lo que sigue.

**Posibles afirmaciones falsas, todavía sin evidencia nueva:** DE-02 escribe una regex con `$` y describe aceptación estricta. Si el autor la usó con `match`, un LF terminal puede pasar; si usó `fullmatch`, no. s04-13/19/21 eligen la primera hipótesis deliberadamente, con `ambiguo`. s04-22 ataca la generalización ASCII si el patrón real usa `\d`. Las comparaciones Unicode y OPTIONS también ponen a prueba generalizaciones explícitas; no se finge que la spec carezca de una regla general para ellas.

## Cómo interpretar la corrida

Usar `evals/sol-04.jsonl` en la misma invocación de `herramientas/oraculo.py` que se usó para sol-03, con un reset al inicio de cada secuencia. Los resets dentro del archivo son pasos de las secuencias 15, 16, 17 y 27; el de 17 carece de token a propósito. **`cuerpo` conserva bytes UTF-8 significativos:** BOM y JSON inválido no deben reconstruirse desde `request`. En s04-23 hay que preservar los `headers`, y en HEAD el texto realmente recibido, incluido el vacío.

Cada `ambiguo` primario dice la elección y su alternativa. Las filas posteriores marcadas «Predicción derivada» describen la misma rama; si falla la elección inicial, no contar todos esos desacuerdos como causas nuevas. Separar **original frente a predicción** de **original frente a gemelo**: fallar mi hipótesis no implica que falle el gemelo.

**83/100 no demuestra dónde están los 17.** Hay solo 15 tests largos: al menos dos fallos corresponden a tests de 1–5 pedidos si el desglose publicado vale para esa corrida. Además, ESTADO documenta un posible redespliegue durante la primera validación. No podemos adjudicar todos los fallos a una omisión lógica ni prometer que estas 30 secuencias los expliquen. Esta tanda entrega discriminantes; las causas requieren respuestas observadas.

NO-04 sigue interesante: NOTAS con estado. No se incluye una respuesta exacta inventada, porque NO-01 omite su texto y el encargo prohíbe leerlo en el log o el modelo. Quien lidera puede contrastar su propio resultado de NOTAS antes/después sin obedecer la nota.

## Verificación y rúbrica

Verificados fuera de línea: JSONL y campos; ids consecutivos; 20 secuencias largas y 10 cortas; una ambigüedad primaria por secuencia como mínimo; 176 mensajes con control revisado por una implementación incremental distinta, incluyendo los dos controles deliberadamente malos; 12 controles aceptados del material como contraste; saldos e ids revisados con una segunda contabilidad; cero copias completas de sol-03 y del material; un solo HALT confirmado; 219 llamadas previstas con resets iniciales. La contabilidad verifica coherencia de las predicciones, **no su verdad sobre el original**.

| Criterio aplicable de RUBRICA | Evidencia o límite |
|---|---|
| Casos nuevos y difíciles | JSONL y tabla anterior: estado, fronteras léxicas y transporte; sin copias de sol-03. |
| Separar observado, inferido y desconocido | Toda la tanda es predicha; alternativas primarias y consecuencias llevan `ambiguo`. No se modifica la spec sin observaciones. |
| Explicar fallas con causas concretas | La tabla señala qué respuesta discrimina cada mecanismo; resultados todavía pendientes. |
| Reproducibilidad y presupuesto | Mismo formato de sol-03, cuerpos crudos y headers preservados, 189 + 30 = 219; cero validaciones del portal gastadas por Sol. |
| Calidad y secretos | Solo cuentas/titulares sintéticos y predicciones; sin credenciales ni llamadas externas. No se toca DISENO.md ni código del gemelo. |
| Smoke, tag verde y resultado del original | No se ejecutó código del repo ni se consultó la caja. Quien integra corre el smoke de main y el contraste. Último tag según ESTADO: verde-01, solo local. |
| Incidente y costo del reemplazo | Esta entrega no mide el incidente ni el costo por caso del servicio; pendientes de quien lidera. |

## Resultado de quien lidera · pendiente

Añadir debajo sin sustituir las predicciones: ids del log de la corrida; primera divergencia por secuencia; elección resuelta; diferencias del gemelo; cambios en spec/código; cuánto explica de los fallos del portal y con qué evidencia. Integración con merge commit por quien lidera.
