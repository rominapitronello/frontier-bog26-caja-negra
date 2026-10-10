# debrief.md · hoja de romina para los 10 minutos

> criterio que alimenta: **profundidad técnica** (15 %). un 4: explica fallas, límites y qué haría después; explica cada falla con una causa concreta.

## cómo funciona, en cinco frases
1. el gemelo es un solo proceso python, solo biblioteca estándar, con el estado en memoria por token y un `POST /__reset` que lo vuelve a cero; no llama al original ni a ningún modelo.
2. lo que es tabla vive como dato en `gemelo/modelo.json` (rutas, códigos y textos de error, el dígito de control, el orden en que se evalúan los errores, el límite, el bloqueo); el código solo recorre esas tablas.
3. todo lo que el gemelo hace salió de medir el original con hipótesis, una línea del log por pedido (`experimentos.jsonl`, ~6.500), y cada fila de la spec cita las líneas que la prueban.
4. un centinela repitió una secuencia canónica cada 5–15 minutos todo el día: una repetición exacta que cambia es un cambio del original; si solo difiere el gemelo, el error es nuestro.
5. cuando llegó la versión 2, la mañana quedó congelada en `gemelo/modelo-manana.json` y la tarde entró como dos datos y dos interruptores de código; el smoke prueba cada línea del log contra el modelo de su versión.

## tres decisiones y la alternativa que descartamos
| decisión | alternativa descartada | por qué |
|---|---|---|
| **reglas en código y datos, sin modelo dentro del gemelo** | un llm que responda lo que no sabemos | el juez compara status y cuerpo exactos; un modelo agrega variación y latencia donde se necesita determinismo. lo desconocido se mide o se declara «supuesto». costo: 0 us$ por caso |
| **medir antes de construir, con un log citado** | escribir el gemelo desde los 20 ejemplos y corregir con las validaciones | solo había 3 validaciones y no dan detalle de qué falla; el log sí. cada respuesta del gemelo tiene una línea del original detrás |
| **un centinela todo el día, no solo a las 15:00** | vigilar solo en la ventana del incidente | en su primera vuelta (10:4x) encontró que nuestra spec decía mal el orden límite/saldo (log 737), y a las 15:59 vio solo el cambio a v2 |

## métricas públicas por categoría → causa
el set: 100 tests, **40 fáciles (1 pedido), 40 regulares (2–5), 20 difíciles (6–12)**; el material decía 40/45/15.

| corrida | categoría | resultado | qué falla y por qué (mecanismo) |
|---|---|---|---|
| 1 · 11:06 · contra v1 · 83/100 | fáciles | 40/40 | nada: la entrada (rutas, token, cuerpo, control) estaba bien desde la mañana |
| | regulares | 33/40 | 14 de las 17 fallas caen **más adelante** en la secuencia (10 por status, 7 por cuerpo). **causa concreta más probable: `NOTAS`**, el comando oculto que el gemelo de esa hora (v5) todavía no conocía. contraste hecho después, sin token y sin el set: el gemelo v5 (commit `373ff1a`) contra las 273 secuencias de la mañana del log falla en 46, **todas más adelante, ninguna en el primer pedido**, y 35 de las 46 son `NOTAS`: el comando en sí (el original 200, v5 400 → **status**) y la sugerencia que lo delata (`TOTAL` → `"sugerencia": "NOTAS"`, que v5 no daba → **cuerpo**). el resto de lo que v5 fallaba es de entrada (`//msg`, `NaN`, chunked, enteros largos, anidamiento), y eso no pesó: los fáciles dieron 40/40. `NOTAS` entró en la v7 y en la corrida 2 las fallas de secuencia desaparecieron. **causa menor:** el redespliegue de la v5 a las 11:07, a mitad de la corrida, que puede romper a lo más el test en curso (cada test empieza con reset). límite: el log no tiene la forma del set (el centinela repite `NOTAS` muchas veces), así que la proporción no se traslada; es la causa más probable, no probada |
| | difíciles | 10/20 | lo mismo: las largas tienen más pasos y más chances de pasar por `NOTAS` o por un comando mal escrito parecido |
| 2 · 16:21 · **contra v2** · **99/100** | fáciles | 40/40 | — |
| | regulares | 40/40 | — |
| | difíciles | 19/20 | **una falla en el primer pedido, por status**: un mensaje suelto. buscada por fuera del set (sol-07, el diferencial de dos gemelos en el primer pedido y uno mutacional: ~6.000 casos), **el único candidato es `pıng`** (i sin punto): python pasa `ı` a `I` con `.upper()` y el gemelo lo tomaba por PING (200, pong); el original solo pasa a mayúsculas en ascii y no lo reconoce (400; log 5680, 5681). arreglado en la v16. si la corrida 3 da 99, la causa queda sin encontrar y se dice así |
| 3 · no se corrió | | — | **decisión de romina (17:1x bog): no hay corrida 3 y el gemelo no se toca más.** la nota final es la del jurado después de las 20:00, con el gemelo **v17**: la v15 que dio 99 más el arreglo de `pıng` (v16) y sin la telemetría (v17). esos dos cambios están probados con el smoke y las pruebas, no con el set |

**hipótesis de fable para el test que falta (17:0x bog), probadas contra el original sin tocar el gemelo:**
1. *`HALT` cambió como el bloqueo y responde 423*: **descartada** por el log: `HALT;SI` sigue dando 409 E520 en v2 (4619, 6234, 6516).
2. y 3. *el tope del cuerpo o el orden entre token y tamaño cambiaron en v2*: **descartadas** (6578–6582): 9.000 bytes sin token o con otro token dan 401, con el token bueno 413; 8.192 bytes pasan y 8.193 dan 413, como en la mañana, y el gemelo calza en los cinco.

## dónde estamos frente a los demás

dato de la organización (10 oct, 14:4x bog): 40 equipos en caja negra; los 15 con resultados promedian **fácil 91 %, regular 73 %, difícil 39 %** (inferencia: fácil = tests de 1 pedido, regular = 2–5, difícil = 6–12). nuestra corrida 1 dio **83/100**, sobre el promedio ponderado (~75), y la corrida 2, ya contra la versión 2, **99/100**: 19 de 20 en las difíciles, donde el promedio es 39 %. lo difícil para todos son las secuencias largas con estado; por eso las medimos aparte: 18 secuencias de 8–12 pedidos que combinan las reglas raras entre sí, y el gemelo calza en las 18 (spec CA-07).

## costo

**0 us$ del presupuesto del evento.** el gemelo no usa modelos: responde con código y datos (`gemelo/modelo.json`), en microsegundos por pedido, sin red. la exploración tampoco gastó en modelos: el dígito de control salió de una búsqueda propia fuera de línea, y los comandos ocultos, de la sugerencia del propio servicio. lo único que se gastó fueron pedidos al original (~6.500 de 8.000 a las 16:5x) y validaciones del portal (2 de 3 a las 16:5x; la tercera, ~19:00).

## límites
- **la falla que queda (corrida 2) no tiene causa probada.** `pıng` es el único candidato que encontramos sin mirar el set; puede ser otro mensaje suelto que ni la spec ni dos gemelos independientes supieron preguntar.
- **lo que no se probó no se sabe:** el id `AC-10000` después de 9.999 cuentas (supuesto, AL-04); si `intentos` tiene tope; si la caja depende del tiempo (minutos u hora del día): el set final corre después de las 20:00 a una hora que no sabemos, y con el token muerto no se puede medir.
- **el gemelo es un solo proceso**: un reinicio a mitad de una secuencia la rompe (en la corrida 1 subimos la v5 con el set corriendo; a lo más rompió el test en curso). el healthcheck de railway ahora evita que un despliegue roto reemplace al bueno, pero no evita un reinicio.
- **la spec dice lo que cada fila prueba, no siempre qué la refutaría**: la confianza (confirmado, probable, supuesto) dice cuánto se repitió, y la regla para refutar es la misma para todas: una repetición exacta de sus ids que dé otra respuesta.

## diseños a ciegas contra la caja real (segunda mitad del experimento)

dos modelos imaginaron qué tendría un banco así sin mirar la caja, y lo contrastamos con lo que la caja hace. la caja gana siempre: lo que no se mide, se inventa.

| quién | qué imaginó | qué hizo la caja real | evidencia |
|---|---|---|---|
| **sol** (`sol-05`) | 60 nombres de comandos de un sistema bancario viejo, cada uno con su hipótesis (detalle, cartola, extracto, ledger, statement…) | **ninguno existe**. el único que sugirió algo fue `NOTA` → `NOTAS`, que ya conocíamos | log 1751–1870, `evals/sol-05.md` |
| **sol** (diseño a ciegas, `evals/linajes/banco-fosil-sol.md`, H6–H10) | comandos con signos (`PING?`), una respuesta que depende de un contador global, un comando que repite la última respuesta (`REPETIR`, `ULTIMO`), un largo máximo con caracteres de control, variantes de `ALTA` | **0 de 5**: los signos solo hacen sugerir el comando (`PING?` → `PING`); `PING` responde igual aunque el contador `X-Req` suba; no hay comando que repita; los caracteres de control en el nombre se aceptan (una tabulación en el comando lo vuelve desconocido); `ALTA` vacío es segmento vacío, y con dígitos o repetido se acepta | log 2561–2575 |
| **claude** (bancotex, diseño a ciegas de otro banco) | abreviaturas de comandos (`CONS`, `DEP`, `TRANS`, `ALT`); huevos de pascua (`XYZZY`, `#VER`, `VERSION`, `ECO`); montos con puntos de miles; cuentas sin guion; nombres largos | **0 de 5 familias**: ni abreviaturas (solo `ALT` sugiere `ALTA`), ni huevos de pascua, ni puntos de miles (E303), ni cuentas sin guion (E401). los nombres largos se aceptan, como ya sabíamos | log 2540–2560 |
| **la caja real** | — | **ocho comandos, dos ocultos** (`HALT`, que la detiene, y `NOTAS`, con una nota interna). ninguno de los dos los adivinó nadie: aparecieron porque el error de comando desconocido **sugiere** el comando más parecido (`HELP` → `HALT`, `TOTAL` → `NOTAS`). y reglas con estado que nadie imaginó: el límite no aplica entre cuentas del mismo titular; tres transferencias rechazadas bloquean la cuenta hasta un depósito | spec CM-02, NO-01, TR-06, TR-08 |

**conclusión del experimento:** los modelos adivinan **la forma** del autor (comandos ocultos, una trampa, un bloqueo por intentos, huecos en la numeración de errores, un límite), **no sus decisiones concretas** (qué comandos, qué trampa, qué límite, qué los desbloquea). **lo concreto salió de medir.**

**salvedad de método (sol, 13:1x bog; `LINAJES.md`):** el pedido de los diseños a ciegas ya traía errores numerados, dígito de control, comandos ocultos, un límite y una trampa. esas coincidencias de forma las puso el pedido, no el modelo. de la forma, lo que adivinaron **sin que se pidiera** es menos: el **bloqueo por tres intentos fallidos** (los dos), los **huecos en la numeración de errores** y **resolver comandos parecidos** (claude). una muestra por linaje: inferencia, no conclusión. la otra mitad de la frase no cambia: ninguna decisión concreta de la caja estaba en los diseños.

**lo que dice:** los diseños a ciegas proponen lo que un autor *podría* haber puesto, y ahí los dos modelos coincidimos con los clichés del dominio (abreviaturas, huevos de pascua, listados, historiales). lo que el autor puso de verdad no estaba en ninguna de las dos listas, y lo encontramos midiendo, no imaginando: con una sugerencia del propio servicio y un centinela que vio una diferencia donde la spec decía otra cosa.

## la pregunta que cambió el ángulo: ¿quién escribió la caja?

**la idea (romina, 12:4x bog):** si la caja la diseñó un modelo, sus reglas tienen la huella de cómo piensa su linaje. en vez de solo preguntarle a la caja *qué hace*, nos preguntamos *quién la pensó*, porque eso dice qué clase de cosas puso y qué clase de cambio traería el incidente. es la lección 18 del ensayo («predecir el código simple del autor») subida un nivel: predecir la cognición del autor.

**cómo se trabajó:** dos muestras a ciegas, una por linaje (`evals/linajes/`): opus 5.5 en ventana sin contexto (bancotex) y sol 6 (banco fósil), ambos con razonamiento alto. sol puso dos reglas de método que se respetaron: las coincidencias que el pedido inducía no cuentan, y **no se les pide a los modelos que expliquen sus elecciones**, porque la explicación posterior contamina lo observado. el detalle está en `LINAJES.md`.

**lo que se vio en las decisiones que nadie pidió:**
- opus puso sus trampas contra **el programador que corrige** (rarezas que parecen bugs, un hueco en la numeración que no hay que «arreglar»).
- sol puso las suyas contra **el agente que investiga**: el mismo mensaje significa cosas distintas en distintos momentos (`SALDO?`, `RUIDO`, `REPETIR`) y una falsa instrucción de sistema dentro de una respuesta (`AUDITA`).
- la lectura de romina, desde su experiencia con los dos labs: los claude conceptualizan a las personas; los gpt piensan desde lo verificable.

**la apuesta, con la caja real delante (claude, 13:3x bog; confianza baja a media):** la caja parece pensada **desde el lado gpt**:
- sus dos trampas apuntan al investigador: `NOTAS` intenta que un agente confunda un dato con una orden y entregue el token; `HALT` prueba si el agente ejecuta algo destructivo porque la caja lo pide.
- **todo es descubrible midiendo**: los ocultos se delatan solos por la sugerencia. coincide con el principio que sol escribió en su diseño: «no castigar al competidor por no adivinar una regla que jamás puede observar».
- el significado depende de la historia: el bloqueo `E510`, `X-Req` que no se reinicia, `HALT` que cambia lo que sigue. (precisión de claude, que lidera: `X-Req` es solo un header; medido después, no cambia ninguna respuesta, ni cruzando el pedido 2.300: spec ME-12, log 2618–2669. la dependencia de la historia está en el bloqueo y en `HALT`.)
- las rarezas que castigan al que corrige (`recieved`, el espacio final, las claves mezcladas) son el estilo de opus, pero también el cliché de cualquier «sistema legado». y `service halted` en inglés, dentro de una caja en español, sugiere otra mano en ese módulo.

**límites, dichos antes de que los pregunten:** una muestra por linaje; parte de la forma la indujo el pedido; quien hace la atribución es un claude, con su propio sesgo para reconocer (o no) lo de su casa. es una inferencia útil, no un hallazgo.

**para qué sirvió:** cambió cómo nos preparamos para las 15:30. si el autor piensa desde el lado gpt, el incidente probablemente cambia **mecánica** (estado, tiempo, autoridad) y no un número; un número se absorbe con un dato, la mecánica pide código. por eso se pensó antes cómo agregar una regla con estado sin romper lo que ya calza, y el centinela vigila el bloqueo y el texto de `NOTAS`. **qué pasó a las 15:30 (escrito a las 16:5x):** la apuesta **no acertó** en lo principal. los tres cambios de la versión 2 fueron **un número** (el límite baja de 100.000 a 50.000), **un código con un contador** (el bloqueo pasa de 409 a 423 y agrega `intentos`) y **un formato** (el saldo pasa de entero a texto con dos decimales). solo el contador es estado nuevo, y la transición del bloqueo no cambió. ninguno toca tiempo ni autoridad. lo que sí se cumplió es el adversario: los tres castigan a un clon fiel a la mañana, como predijeron romina y sol (`PREDICCION_INCIDENTE.md`, acierto parcial). lo que más ayudó no fue la apuesta, sino lo que hicimos por si acaso: el límite y el código de error ya eran datos, y el centinela miraba el bloqueo y los saldos.

**por qué importa:** la mayoría de los equipos va a tratar la caja como un objeto. nosotros la tratamos también como **el producto de una mente**, y usamos los sesgos de los modelos como instrumento de medición en vez de verlos solo como ruido.

## qué haríamos después
- **el centinela en todas las familias desde el principio**, no en las canónicas: el cambio a v2 lo vio primero la repetición de secuencias largas (fable-04, sol-04), y el centinela tardó 2 minutos más.
- **nunca subir durante una validación, por diseño y no por regla**: congelar los despliegues mientras corre el set (hoy lo hicimos a mano después de perder la corrida 1 en eso).
- **cada fila de la spec con su contraejemplo**, no solo con su evidencia, como pide la rúbrica.
- **un generador de primer pedido con unicode desde el día uno**: la única falla que creemos haber encontrado salió de una diferencia entre python y el original en cómo se pasa a mayúsculas, y la sacó un generador mutacional, no la spec.
