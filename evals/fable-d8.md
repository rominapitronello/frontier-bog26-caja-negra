# fable-d8 · el segundo gemelo, escrito solo desde la spec, y el diferencial entre los dos

**autoría:** fable (claude fable 5.1, claude code con terminal, sesión `012YBokg…`) · 10 oct 2026, 16:xx bog · `DISENO.md` D8, repartido en el issue #12.

**qué es.** `gemelo_fable/servidor.py` es una segunda implementación del servicio escrita **solo desde `spec.md`** (v2 en `main`, `d2bb463`, con las filas de la tarde: anidamiento, enteros largos, chunked, latin-1), sin abrir `gemelo/` ni `gemelo/modelo.json`. la única línea del log que leí antes de medir es la 1663, por el texto literal de la nota de `NOTAS` (NO-01), que la spec no trae. cada decisión del código cita su fila. `gemelo_fable/diferencial.py` sortea secuencias con estado y se las manda a los dos gemelos en local, sin token del original, y corta cada secuencia en la **primera** discrepancia.

**para qué sirve.** la rúbrica pide que otro ingeniero pueda reimplementar el servicio con la spec: esto lo mide en vez de afirmarlo. y después de las 20:00, cuando el token muera, el diferencial entre dos lecturas independientes es el único oráculo que sigue vivo.

## resultado

| medición | resultado |
|---|---|
| los 20 ejemplos del material (`medir.py`) | 20/20, a la primera |
| **todo el log del original** (273 secuencias, `medir.py --casos experimentos.jsonl`), primera medición, sin haber visto el log | **267/273**. las 6 que fallan son **4 causas, todas de borde http**, ninguna de reglas del banco (abajo) |
| lo mismo tras corregir las 4 | **272/273**. la que queda (`http-chunked`, 2469) es una sonda que el propio log declara mal armada: su conclusión dice que mandó `Content-Length` y `chunked` a la vez y que el borde respondió 400; al replicarla, el comparador la manda igual que la 2471 (bien armada, pong), así que ningún gemelo puede responder las dos |
| diferencial contra `gemelo/` (v14), semillas 1, 2 y 3: 2.000 secuencias de 1 a 14 pedidos, **14.361 pedidos** con estado (altas, rachas, bloqueos, anulaciones, titulares con espacio y tilde, HALT, NOTAS, dobles fallas, errores de forma, anomalías de entrada, resets a mitad) | **0 discrepancias** |

**lo que esto dice de la spec.** dos instancias distintas, una sin ver el código de la otra, implementaron el mismo servicio desde el mismo texto y responden igual en todo lo sorteado y en 272 de 273 secuencias reales. las reglas con estado (§ 3 y § 4) están completas: ni una falla vino de ahí. lo que la spec cita pero no detalla lo suficiente para reimplementar a ciegas está en la capa de entrada:

| causa | fila | qué faltaba en la spec | arreglo en `gemelo_fable` |
|---|---|---|---|
| `POST //msg` (doble barra) da 404 en el original; mi servidor devolvía 401 o pong | EN-03 nombra `/msg/` y `/MSG`, no `//msg`; y el `http.server` de python colapsa `//` en `/` antes de entregar la ruta | leer la ruta de la **línea cruda** del pedido (`raw_requestline`), no de `self.path`. vale la pena una frase en EN-03 o EN-16: «la ruta se compara tal cual llegó, también `//msg`» |
| método inexistente (`FOO`): el borde de railway responde 400 con el texto `Bad Request` | EN-01b lo dice, pero no el cuerpo exacto ni que es texto plano con `Connection: close` | el servidor imita al borde para métodos fuera de la lista http y webdav (`TRACE` y `PROPFIND` sí pasan, 1658 y 1660) |
| `Transfer-Encoding: chunked` **y** `Content-Length` a la vez: 400 del borde | solo está en la conclusión de la fila 2469, no en una fila de la spec | imitado; es el caso irreplicable de arriba |
| `Transfer-Encoding: chunked` solo | EN-19, bien | lectura de chunks |

**lo que el diferencial no encontró, y por qué puede ser.** cero discrepancias en 14.361 pedidos quiere decir que, dentro de lo que el generador sortea, las dos lecturas de la spec coinciden. el límite es el generador: no sortea cuerpos de más de 8 kb, ni 20 niveles de anidamiento con `m` adentro, ni headers raros, ni más de 14 pasos. los dos gemelos comparten además una decisión que no se puede decidir desde la spec (qué hace cada uno con lo que la spec llama «supuesto»), y donde los dos eligieron igual, el diferencial calla aunque el original haga otra cosa.

## un dato para el incidente (issue #12)

al medir contra todo el log, las **30 secuencias ya replicadas contra la v2** (`v2-*`, 563 pedidos, ids 3827–4447: los 20 ejemplos, control, entrada, comandos, sugerencias, orden, bordes, titular, bloqueo, HALT, NOTAS, huecos de códigos, parser) **pasan enteras con mi gemelo de la mañana**, salvo las dos que caen en la doble barra, que caen igual en la v1. es decir: en nada de lo replicado hasta esa hora la v2 responde distinto de la spec de la mañana. los tres cambios están fuera de ese territorio: en condiciones que la mañana nunca produjo (acumulados, cupos, tiempo, un comando nuevo), no en respuestas conocidas que cambiaron. lo escribo como inferencia desde el log, no como observación mía: no tengo token.

## cómo correrlo

```
GEMELO_TOKEN=t PORT=8081 python3 gemelo/servidor.py &                 # a: el gemelo de quien lidera
GEMELO_TOKEN=t PORT=8082 python3 gemelo_fable/servidor.py &           # b: este
python3 medir.py --casos experimentos.jsonl --gemelo http://127.0.0.1:8082 --token t
python3 gemelo_fable/diferencial.py --a http://127.0.0.1:8081 --b http://127.0.0.1:8082 --token t --semilla 4 --secuencias 500
```

las discrepancias salen en el formato de `evals/sol-03.jsonl` (predicción = lo que dijo b, la respuesta de a en la hipótesis), listas para `herramientas/oraculo.py` contra el original: solo esas valen un pedido. hoy el archivo quedó vacío. `gemelo_fable/` no está en los `watchPatterns` de railway: fusionarlo no redespliega nada.

## para romina (agents.md § 4 y rúbrica)

- **qué pasó:** otra instancia reimplementó el servicio desde la spec sin ver el código: 272 de 273 secuencias del original a la segunda medición, y cero diferencias con el gemelo en 14.361 pedidos sorteados. las seis fallas de la primera medición eran todas de borde http, ninguna del banco.
- **qué significa:** para la nota, la spec cumple lo que pide la rúbrica del reto 2 (que otro ingeniero la reimplemente) y ahora está medido, no afirmado; cubre «plan para medir» y «especificación». queda flojo: el diferencial no encontró nada nuevo que preguntarle al original, así que no aporta a los 17; y la spec debería decir en una frase lo de `//msg` y el cuerpo exacto del 400 del borde.
- **qué tienes que hacer tú:** nada.
- **pendiente y de quién:** quien lidera decide si las dos frases entran en EN-03/EN-16 y EN-01b. cuando se adapte `gemelo/` a la v2, el diferencial se vuelve a correr contra este gemelo de la mañana: cada discrepancia que aparezca es uno de los tres cambios, nombrado por la regla que lo produce.
