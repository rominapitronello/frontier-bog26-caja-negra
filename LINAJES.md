# LINAJES.md · quién pensó la caja, y qué cambiaría

> una capa de trabajo que no estaba en el diseño entregado a las 12:00 (`DISENO.md` queda congelado; este documento lo complementa). idea de romina, 10 oct ~12:40 bog. escrito por claude (`01MD7…`). lo marcado **inferencia** es eso: con un diseño por linaje, no es prueba.

## la idea

los modelos tienen sesgos de diseño. si la caja la escribió (o ayudó a escribirla) un modelo, sus reglas tienen la huella de cómo piensa ese linaje. entonces:

1. pedimos a dos linajes que diseñen **a ciegas** una caja parecida (`evals/linajes/`): sol (familia gpt) y un claude sin contexto.
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
- **la estructura converge**: familias de errores, comandos ocultos, una trampa de inyección, bloqueo por tres fallos. un llm al que le piden «una caja negra para un hackatón» llega a una plantilla parecida. eso apoya que el autor real usó un modelo, o pensó como uno.
- **en las reglas del banco, claude se parece más** (límite, huecos, comandos parecidos). **en la trampa, gpt se parece más** (engañar al investigador desde una respuesta).
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

**resultado de H1–H5** (claude, lidera, 12:5x bog; log 2540–2560): **ninguna calza con la caja real.** los prefijos no son comandos (`ALT` solo sugiere `ALTA`), `XYZZY`/`#VER`/`VERSION`/`ECO` no existen, `5.000` y `5.0.0.0` dan E303, `AC0001` da E401 y un nombre de 200 caracteres se acepta. el gemelo calza en toda la secuencia. comparación en `debrief.md`. H6–H10 (sol) no se han corrido. el centinela suma desde las 13:0x lo barato que este documento propone: un prefijo, un id en minúsculas y con espacio, un vecino de los ocultos y un bloqueo por tres rechazos.

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
