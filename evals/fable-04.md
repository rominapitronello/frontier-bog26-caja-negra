# fable-04 · venenos retenidos: doble falla, bordes y orden inesperado

**autoría:** fable (claude fable 5.1, claude code con terminal, sesión `012YBokg…`) · 10 oct 2026, 12:0x bog · encargo de romina en el chat: «usa el mismo formato y las mismas reglas que `sol-04`, pero tu foco es otro: mensajes que rompen dos cosas a la vez, bordes del control y de los montos, y comandos en el orden menos esperado, en secuencias de 2 a 8 pedidos».

**base exclusiva:** `spec.md` v2 en `main` (`cde2fe6`), `material/README.md`, `material/pruebas/ejemplos.jsonl` y `evals/sol-03.jsonl` (solo para copiar el formato). **no abrí** `gemelo/`, `experimentos*.jsonl` ni `herramientas/` durante este encargo. una salvedad honesta: más temprano hoy, al fusionar `main` en mi PR #2, vi `herramientas/control.py` de quien lidera; es la misma fórmula de § 2 de la spec y no contiene nada del gemelo. **no consulté** el original ni el gemelo: no tengo token.

## entrega y cómo leerla

- `fable-04.jsonl`: **38 secuencias, 238 pedidos**, largos de 3 a 8 (1×3, 5×4, 6×5, 10×6, 3×7, 13×8). ids globales 1–238. mismo formato que `sol-03`: cada secuencia exige un `POST /__reset` previo que no está en el archivo; `metodo`, `ruta`, `auth` y `cuerpo` mandan sobre los valores por defecto (`POST`, `/msg`, token correcto, el `request` como json). **tres secuencias llevan un `POST /__reset` como fila** (f04-12, f04-28, f04-31): es una fila más, con `metodo` y `ruta`.
- `HALT;1` detiene en **4 secuencias** (f04-28 a f04-31), bajo el techo de 5 del encargo de sol.
- **10 filas `ambiguo`**: donde la spec no decide, con mi mejor predicción. el resto lo decide la spec y una predicción fallida ahí es una fila de la spec que está mal.
- ningún mensaje suelto ni secuencia coincide letra por letra con los 20 ejemplos (para consultar `AC-0001` uso `Consulta`, que CM-01 confirma equivalente).
- `fable-04-generador.py` produjo el archivo: es **mi modelo mínimo de la spec**, escrito solo desde ella, con el control de § 2 implementado de cero. no es el gemelo ni lo mira. cada fila lleva el código que yo esperaba a mano, y el generador no escribe nada si su lectura de la spec y mi expectativa difieren (hoy coincidieron en las 238). sirve para auditar cómo leí cada regla, y para regenerar si se corrige una predicción.
- quien lidera las corre contra el original y el gemelo con su oráculo, como `sol-03`, y separa (A) predicción ≠ original: hueco o error de la spec; (B) original ≠ gemelo: error del gemelo.

## los silencios de la spec que estas secuencias prueban

| # | silencio | fila de la spec | secuencia | mi predicción |
|---|---|---|---|---|
| 1 | **anular el depósito que desbloqueó una cuenta**: ¿vuelve el bloqueo? TR-08 dice que el depósito reinicia la racha y que anular no reinicia; no dice si anular ese depósito la restaura | TR-08 (calla) | f04-03 | no vuelve: E507, no E510 |
| 2 | **titular con espacio al final** («Noa» vs «Noa »): el espacio no aporta al control, así que el mensaje pasa, y el titular queda distinto | TR-06 (exacto, probó solo mayúsculas) | f04-14 | distintos: E506 |
| 3 | **un espacio como titular, dos veces**: ¿mismo titular? | AL-02 + TR-06 | f04-15 | mismo: sin límite |
| 4 | **tilde en el titular** («Ines» vs «Inés»): mismo control, ¿otro titular? | TR-06 | f04-17 | distintos: E506 |
| 5 | **confirmación de HALT con espacios** («1 », « 1»): mismo control que `HALT;1` | HA-05 (probó 0, 2, 01) | f04-27, f04-30 | E520, no detiene |
| 6 | **id de cuenta con espacio al final** (`AC-0001 `): mismo control, ¿misma cuenta? | CO-03 (probó espacio delante) | f04-34 | E401 |
| 7 | **clave `m` repetida en el json**; **json con relleno alrededor** | EN-09, EN-10 (callan) | f04-35 | la última `m` gana → pong; el relleno es json válido → pong |
| 8 | **`OP-01`** (otro ancho de id) | AN-05 (probó `op-0001`, un id de cuenta) | f04-13 | E402 |
| 9 | **E104 contra E201** (`CONSULTA;;5X`): ER-20 da el orden, pero ese par no tiene evidencia citada | ER-20 | f04-23 | E104 |
| 10 | **doble falla con bloqueo**: bloqueada + destino inexistente, bloqueada + mismo destino, bloqueada + monto inválido, bloqueada + límite + saldo | TR-07 (evidencia 881–883 para un par) | f04-01, f04-02, f04-06 | E401, E304, E303, E510 |
| 11 | **anular tras tres transferencias fallidas**: no hay `OP-0001` que anular | ME-03 + AN-05 (se deduce, no se dice) | f04-08 | E402 |
| 12 | **controles 97, 98 y de una cifra en comandos con estado** (DEPOSITO, TRANSFER): IN-06 e IN-07 se probaron, por los ids del log, con mensajes sin estado | IN-06, IN-07 | f04-19, f04-20 | pasan; `1`, `05` y `005` no |
| 13 | **el reset con otro token no repara ni borra**: EN-07 da el 401 pero no dice que el estado quede intacto | EN-07 | f04-28 | sigue detenido; las cuentas siguen |
| 14 | **una transferencia por el saldo exacto reinicia la racha** (TR-05 + TR-08 juntas) | TR-08 | f04-07 | reinicia: E507 y no E510 |
| 15 | **detenido gana al bloqueo** | ER-20 (se deduce del orden) | f04-31 | E599 |
| 16 | **los fallos antes del alta no consumen ids** (DEPOSITO y TRANSFER a cuentas que no existen todavía) | ME-03 | f04-32 | AC-0001 y OP-0001 después |
| 17 | **monto con espacio al final en TRANSFER** (`1 `): el control no lo ve, el monto sí | DE-02/TR-02 (probado en DEPOSITO) | f04-21 | E303 |
| 18 | **punto y coma y dígitos de ancho completo** (`；`, `１４`) | IN-01, IN-03 (ascii) | f04-36 | E103, E201 |

el resto de las secuencias (f04-04, 05, 09, 10, 11, 12, 16, 18, 22, 24, 25, 26, 29, 33, 37, 38) combina reglas que la spec sí fija, en órdenes que el log probablemente no recorrió: rachas mezcladas E506/E507, el destino que no se bloquea, mismo titular bloqueado y desbloqueado, saldos negativos que después reciben plata, el reset a mitad, sugerencias con palabras nuevas, dos rachas independientes.

## lo que creo que a la spec le falta, aparte de los silencios

- **NOTAS no se puede reimplementar desde la spec.** NO-01 dice que el texto exacto «está en la línea 1663 del log y en `gemelo/modelo.json`». el jurado lee la spec contra el servicio y pide que otro ingeniero reimplemente sin tocar el original: el texto literal tiene que estar en la spec. por eso aquí no hay ninguna fila con `NOTAS`: no puedo predecirla.
- **ER-20 no cita evidencia para varios pares del orden** (E104/E201, E302/E401, E304/E401 sin bloqueo). el orden es una cadena y cada eslabón sin par probado es una afirmación inferida que la tabla marca como confirmada. f04-23 y f04-13 cubren dos; bajar la confianza de los demás a «probable» cuesta nada y evita que una afirmación falsa reste.
- **no encontré una afirmación que crea falsa.** las dos de arriba son omisiones.

## para romina (agents.md § 4 y rúbrica)

- **qué pasó:** 38 secuencias de venenos escritas solo desde la spec, con 10 filas donde la spec no decide. no gasté pedidos ni validaciones.
- **qué significa:** cada predicción que falle contra el original es un hueco de la spec que el set del jurado puede estar pisando; cada diferencia con el gemelo, un arreglo antes de la próxima corrida. cubre **plan para medir** (casos difíciles, borde y nuevos, con comando para regenerar) y alimenta **resultado en el set oculto** y la spec del reto 2 (confirmado / probable / supuesto). queda flojo: no está corrido (no tengo token), y `NOTAS` no se pudo cubrir.
- **qué tienes que hacer tú:** nada. quien lidera fusiona y corre.
- **pendiente y de quién:** quien lidera corre las 238 contra el original y el gemelo, y escribe debajo qué falló. si una ambigua falla, la fila de la spec correspondiente gana una regla; si una no ambigua falla, la spec tiene un error.

---

## resultado de la corrida (claude, lidera · 10 oct 12:1x bog)

`python3 herramientas/oraculo.py evals/fable-04.jsonl`, log 1905–2180 (238 pedidos y 38 resets).

- **predicción = original en 38/38 secuencias: las 238 predicciones calzaron**, incluidas las 10 `ambiguo`. no hubo hueco ni error de la spec que el original desmintiera.
- **gemelo = original en 38/38.** ningún arreglo pendiente: estas secuencias no explican ninguno de los 17 de la corrida 1.
- **los 18 silencios** pasan a la spec como filas con evidencia: EN-15, IN-13, IN-14, CO-04, TR-09, TR-10, TR-11, TR-12, AN-06, HA-06, HA-07, ME-10 y ME-11 (confirmado donde se repite, probable donde se vio una vez). CA-05 cuenta la prueba.
- **ER-20**: tomada la objeción. «confirmado» queda solo para los pares citados; el resto de la cadena, probable por transitividad.
- **NOTAS**: el texto literal queda citado por su línea del log (1663), que también se entrega, y no copiado a la spec, por lo que contiene (spec RI-12). límite conocido: desde la spec sola no se reimplementa la nota palabra por palabra.
