# debrief.md · hoja de romina para los 10 minutos

> criterio que alimenta: **profundidad técnica** (15 %). un 4: explica fallas, límites y qué haría después; explica cada falla con una causa concreta.

## cómo funciona, en cinco frases
null

## tres decisiones y la alternativa que descartamos
null

## métricas públicas por categoría → causa
| categoría | resultado | qué falla y por qué (mecanismo) |
|---|---|---|

## dónde estamos frente a los demás

dato de la organización (10 oct, 14:4x bog): 40 equipos en caja negra; los 15 con resultados promedian **fácil 91 %, regular 73 %, difícil 39 %** (inferencia: fácil = tests de 1 pedido, regular = 2–5, difícil = 6–12). nuestra corrida 1 dio **83/100**, sobre el promedio ponderado (~75). lo difícil para todos son las secuencias largas con estado; por eso las medimos aparte: 18 secuencias de 8–12 pedidos que combinan las reglas raras entre sí, y el gemelo calza en las 18 (spec CA-07).

## costo

**0 us$ del presupuesto del evento.** el gemelo no usa modelos: responde con código y datos (`gemelo/modelo.json`), en microsegundos por pedido, sin red. la exploración tampoco gastó en modelos: el dígito de control salió de una búsqueda propia fuera de línea, y los comandos ocultos, de la sugerencia del propio servicio. lo único que se gastó fueron pedidos al original (~2.900 de 8.000 al cierre de la tarde) y validaciones del portal (1 de 3 hasta ahora).

## límites
null

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

**para qué sirvió:** cambió cómo nos preparamos para las 15:30. si el autor piensa desde el lado gpt, el incidente probablemente cambia **mecánica** (estado, tiempo, autoridad) y no un número; un número se absorbe con un dato, la mecánica pide código. por eso se pensó antes cómo agregar una regla con estado sin romper lo que ya calza, y el centinela vigila el bloqueo y el texto de `NOTAS`. **qué pasó a las 15:30:** null hasta el incidente; aquí se escribe si la apuesta acertó o no.

**por qué importa:** la mayoría de los equipos va a tratar la caja como un objeto. nosotros la tratamos también como **el producto de una mente**, y usamos los sesgos de los modelos como instrumento de medición en vez de verlos solo como ruido.

## qué haríamos después
null
