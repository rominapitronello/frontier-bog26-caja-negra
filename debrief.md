# debrief.md · hoja de romina para los 10 minutos

> criterio que alimenta: **profundidad técnica** (15 %). un 4: explica fallas, límites y qué haría después; explica cada falla con una causa concreta.

## cómo funciona, en cinco frases
null

## tres decisiones y la alternativa que descartamos
null

## métricas públicas por categoría → causa
| categoría | resultado | qué falla y por qué (mecanismo) |
|---|---|---|

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

**lo que dice:** los diseños a ciegas proponen lo que un autor *podría* haber puesto, y ahí los dos modelos coincidimos con los clichés del dominio (abreviaturas, huevos de pascua, listados, historiales). lo que el autor puso de verdad no estaba en ninguna de las dos listas, y lo encontramos midiendo, no imaginando: con una sugerencia del propio servicio y un centinela que vio una diferencia donde la spec decía otra cosa.

## qué haríamos después
null
