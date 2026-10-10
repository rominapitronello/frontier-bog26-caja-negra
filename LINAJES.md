# LINAJES.md · quién pensó la caja, y qué cambiaría

> una capa de trabajo que no estaba en el diseño entregado a las 12:00 (`DISENO.md` queda congelado; este documento lo complementa). idea de romina, 10 oct ~12:40 bog. escrito por claude (`01MD7…`). lo marcado **inferencia** es eso: con un diseño por linaje, no es prueba.

## la idea

los modelos tienen sesgos de diseño. si la caja la escribió (o ayudó a escribirla) un modelo, sus reglas tienen la huella de cómo piensa ese linaje. entonces:

1. pedimos a dos linajes que diseñen **a ciegas** una caja parecida (`evals/linajes/`): sol 6 (familia gpt, razonamiento alto) y un claude sin contexto (opus 5.5, ventana fantasma, razonamiento alto).
2. comparamos sus diseños con la caja real (`spec.md`).
3. lo que **proponen y no probamos** son hipótesis fuera de nuestra spec, el punto ciego que comparten sol, fable y el fuzzer porque todos salen de ella.
4. lo que **cada linaje cambiaría** es un catálogo de candidatos para el incidente de las 15:30.

es psicometría aplicada a modelos: el sesgo del redactor como instrumento, no como ruido.

## la comparación

| rasgo de la caja real (spec) | sol · gpt | claude |
|---|---|---|
| límite por transferencia (100.000, `E506 límite excedido`) | no tiene | **sí**: 200.000, `E12 LIMITE EXCEDIDO` |
| huecos en la numeración de errores (E501–E505, E508–E509) | no | **sí**: `E10` «retirado, nunca se emite» |
| resuelve comandos parecidos (sugerencia por distancia de edición) | no | **parecido**: acepta prefijos (`SAL` → `SALDO`) |
| trampa **dentro de una respuesta** del servicio (`NOTAS` pide el token) | **sí**: `AUDITA` devuelve un «SYSTEM:» falso | no: su trampa va en los mensajes de entrada |
| la trampa apunta al **agente que investiga** | **sí** | no: apunta a un clon hecho con un llm |
| json por http con status variados | a medias: json, pero siempre 200 | no: texto plano |
| tres fallos → bloqueo (`E510`) | sí (pin) | sí (pin) |
| dígito de control de banco | módulo 11, estilo rut | módulo 11, estilo rut |
| comandos ocultos que no salen en la ayuda | sí (4) | sí (3) |
| rarezas que parecen bugs y hay que copiar | sí | sí |

**lectura (inferencia):**
- **corrección de método (sol, 13:1x bog): la estructura que coincide no es evidencia.** el pedido ya incluía errores numerados, dígito de control, comandos ocultos, un límite y una trampa: que los diseños los tengan lo puso el pedido, no el linaje (lo escribió claude, y fue un error de diseño del experimento). sirven como evidencia solo las **decisiones que nadie pidió**: el contador por teléfono, las sesiones con usos, el truncado a 160, los prefijos de comando, el orden de los errores y la forma concreta de cada trampa. sol junta más muestras por linaje para separar linaje de instancia; esta es la muestra 1 de cada uno.
- con esa corrección, lo que queda en pie es poco y débil: **huecos en la numeración de errores** (claude no los pidió: «E10 retirado») y **resolver comandos parecidos** (prefijos) se parecen a la caja real; **la trampa dirigida al investigador desde una respuesta** se parece más a gpt. una muestra por linaje: inferencia, no conclusión.
- **hipótesis de romina:** las trampas las pensó un gpt y el banco (las reglas, el dataset) un claude. es compatible con la tabla; no está probada.
- **el contexto deja huella:** los dos linajes eligieron el rut chileno porque trabajan con romina, desde chile. el autor real eligió el iban y una api web: no tenía ese contexto. el sesgo de contexto existe y se ve en los detalles, no en la estructura.

## hipótesis nuevas para la caja real (antes del incidente)

salen de lo que los diseños proponen y nuestra spec no ha preguntado. las corre quien lidera, con su hipótesis en el log:

| # | hipótesis | de dónde |
|---|---|---|
| H1 | comandos por prefijo: `CONS`, `DEP`, `TRANS`, `ALT` | claude (r16) |
| H2 | comandos huevo de pascua: `XYZZY`, `#VER`, `VERSION`, `ECO` | claude (h2–h4) |
| H3 | monto con puntos de miles: `5.000`, `5.0.0.0` | claude (r21) |
| H4 | cuenta sin guion: `AC0001` | claude (r13) |
| H5 | respuesta que crece hasta un tope: `ALTA` con nombre de 200 caracteres | claude (r12) |
| H6 | comandos con signos: `CONSULTA?`, `PING?` | sol (r44) |
| H7 | una respuesta que depende de un contador global que no se resetea (`X-Req`): `PING` varias veces seguidas | sol (`RUIDO`) |
| H8 | un comando que repite la última respuesta: `REPETIR`, `ECO`, `ULTIMO` | sol (`REPETIR`) |
| H9 | largo máximo del mensaje (160) y caracteres de control dentro del comando o del nombre | sol (r05–r06) |
| H10 | `ALTA` con nombre vacío, con dígitos, o repetido | los dos |

**resultado de H1–H5** (claude, lidera, 12:5x bog; log 2540–2560): **ninguna calza con la caja real.** los prefijos no son comandos (`ALT` solo sugiere `ALTA`), `XYZZY`/`#VER`/`VERSION`/`ECO` no existen, `5.000` y `5.0.0.0` dan E303, `AC0001` da E401 y un nombre de 200 caracteres se acepta. el gemelo calza en toda la secuencia. comparación en `debrief.md`. **H6–H10 (sol)**, log 2561–2575: **ninguna calza**: `PING?` y `CONSULTA?` solo sugieren el comando; `PING` responde igual aunque `X-Req` suba; `REPETIR` y `ULTIMO` no existen; los caracteres de control en el nombre se aceptan y una tabulación en el comando lo vuelve desconocido; `ALTA` vacío da E104, con dígitos o repetido se acepta. el gemelo calza. el centinela suma desde las 13:0x lo barato que este documento propone: un prefijo, un id en minúsculas y con espacio, un vecino de los ocultos y un bloqueo por tres rechazos.

## catálogo para el incidente: qué cambiaría cada linaje

el incidente lo diseña alguien. si es quien pensó las reglas, cambia **datos**; si es quien pensó las trampas y el estado, cambia **mecánica**. la columna «¿lo ve el centinela?» se cruzó con los pasos de `herramientas/centinela.py` a las 12:58 bog.

| # | cambio probable | linaje | ¿lo ve el centinela hoy? | cómo lo absorbe el gemelo |
|---|---|---|---|---|
| C1 | otro valor del límite (100.000 → x) | claude | **sí** (100.000 y 100.001) | un dato en `modelo.json` (D4) |
| C2 | un código nuevo en un hueco (E501–E505, E508–E509) para una regla nueva: monto mínimo, tope diario, máximo de cuentas | claude | parcial: solo si la regla toca sus pasos | dato + una capa en la cadena de errores |
| C3 | el dígito de control cambia de pesos, de módulo o de lectura | claude | **sí**: todo mensaje con control daría `E202` | parámetro del control |
| C4 | normalización nueva: recorta espacios, ids en minúscula, prefijos de comando | claude | **no** | código chico en la capa de entrada |
| C5 | textos de error o nombres de campos que cambian (`recieved` corregido, `cuenta_id` ↔ `cuentaId`) | los dos | **sí** | datos |
| G1 | estado nuevo: sesión o créditos, algo que caduca tras n pedidos | gpt | sí, como error nuevo en la secuencia | **código**: es lo más caro, pensarlo antes |
| G2 | comisión fija por transferencia | gpt | **sí** (la consulta tras transferir muestra el saldo) | dato + una línea de código |
| G3 | confirmación en dos pasos para transferir (folio) | gpt | **sí** (la transferencia respondería otra cosa) | código |
| G4 | otra trampa en una respuesta (un comando oculto nuevo tipo `AUDITA`) | gpt | **no**, salvo que la sugerencia lo delate | dato (la respuesta literal) |
| G5 | una respuesta que depende de un contador global | gpt | parcial (`PING` aparece pocas veces) | código |
| G6 | transporte: siempre 200, otro nombre de campo (`m` → `texto`), otra ruta | gpt | **sí** | capa de entrada |

**para el centinela, lo barato que falta (inferencia; lo decide quien lidera):** un prefijo (`CONS;AC-0001;…`), un id en minúscula, un espacio al final, tres transferencias rechazadas seguidas (`E510`), y un nombre vecino de los ocultos para que la sugerencia delate uno nuevo.

**para el gemelo:** lo de claude se absorbe cambiando datos; lo de gpt (sesiones, confirmación en dos pasos) es código. si a las 15:30 el cambio es de mecánica, el tiempo se va en eso: conviene haberlo pensado antes.

## registro de muestras (sol, 13:2x bog)

método: no se le pide a ninguna instancia que explique por qué eligió sus reglas; la explicación retrospectiva contaminaría el fenómeno. los artefactos originales son la evidencia.

| muestra | caja | modelo | hipótesis de diseño (lectura de sol) |
|---|---|---|---|
| 1 | bancotex 2.3 | claude opus 5.5, ventana fantasma, razonamiento alto | la dificultad está en **obedecer reglas extrañas**: trampas contra la tendencia a corregir; énfasis en precedencia y parsers |
| 2 | banco fósil 77 | sol 6 (gpt), razonamiento alto | la dificultad está en **el estado y los niveles de autoridad**: `SALDO?` (una foto vieja del saldo), `RUIDO` (cambia con un contador global), `REPETIR` (repite sin ejecutar), `AUDITA` (una falsa instrucción de sistema dentro de una respuesta) |

convergencias espontáneas, no pedidas: 1998, tres clientes, módulo 11, pin, sesiones que caducan, transferencias pendientes. pueden ser convención del dominio y no parentesco: las próximas muestras dirán si las decisiones no pedidas se agrupan por linaje o son de cada instancia.

**para el incidente (inferencia de claude):** la hipótesis de sol sobre su propia muestra, «el mismo mensaje no significa lo mismo en distintos momentos», es justo la forma de un cambio durante el día. la caja real ya tiene piezas así: `X-Req` no se reinicia con el reset, el bloqueo `E510` depende de la historia, y `HALT` cambia todo lo que sigue. H7 (una respuesta que dependa de un contador global) es la hipótesis de sol que más vale probar antes de las 15:30.

## sol-06: los huecos de la numeración y cinco cambios para el incidente (sol 6, `encargos/sol-06-autor.md`)

**los huecos, contra la caja real** (claude, lidera, 13:5x bog; log 2712–2748): sol atribuyó cada hueco a una regla que el autor habría escrito y luego retirado (inferencia de autor). corridas sus secuencias exactas, **ningún código reservado aparece** y la caja responde como en la mañana: un espacio como nombre se acepta (E501), un nombre repetido también (E502), **doce altas seguidas pasan sin cupo** (E503, 2717–2729), un depósito de 1 y uno de 100.001 pasan (E504, E505), anular dos veces da 200 `ok:false` (E508) y anular un depósito ya gastado deja −100 (E509). E403 no tiene disparador con un solo token. el gemelo calza en las siete secuencias. lectura de sol, que estos datos no contradicen: los huecos parecen reglas reservadas o retiradas, no comportamientos ocultos vivos.

**los cinco cambios que sol haría como autor, y cómo los vería el centinela** (desde las 13:5x tiene un paso para cada uno):

| # | cambio (sol) | qué paso del centinela lo delata | cómo lo absorbe el gemelo (v9) |
|---|---|---|---|
| 1 | el límite de 100.000 pasa a ser **acumulado** por origen | dos transferencias seguidas de 60.000 a otro titular: hoy pasan las dos | `estado.limite` + un acumulador por cuenta (código chico) |
| 2 | **ANULA rechaza** un reverso que dejaría saldo negativo (E509) | anular `OP-0005`, un depósito ya gastado: hoy pasa y deja −120.000 | `estado.anula.permite_saldo_negativo` (dato) + el chequeo antes de mutar |
| 3 | **depositar ya no desbloquea** | depósito de 1 a la cuenta bloqueada y una transferencia: hoy pasa | `estado.bloqueo.reinician` (dato: sacar `deposito`) |
| 4 | **comisión fija** de 1 por transferencia entre titulares distintos | la consulta de saldo después de dos transferencias: hoy 80.000 | código chico (débito y reverso) |
| 5 | la tabla de letras del control pasa a **A=10…Z=35** | cualquier mensaje con control daría E202 | `control.letras` (dato, si se agrega la tabla) |

