# incident.md · el cambio de las 15:30 bog

> criterio que alimenta: **respuesta al incidente** (ejecución). un 4: detectan el cambio, se adaptan y lo explican. lo que dice «null» se llena cuando ocurra; el protocolo de abajo se escribió **antes** del cambio (10 oct 11:3x bog), para que se vea qué teníamos preparado y qué improvisamos.

**hora del cambio (según el juez):** 15:30 bog (ticket #FR-0153, «el proveedor desplegó la versión 2 del servicio sin avisar»: **3 comportamientos** cambiaron, el resto igual; los tests del set corren contra v2) · **cómo se anunció:** el ticket en el portal (`frontier.lab10.ai/evento/reto/incidente`), recibido por romina a las 15:30

## cómo lo vamos a detectar (preparado antes)
- **el centinela** (`herramientas/centinela.py`) repite una secuencia canónica de 58 pedidos (eran 34 a las 11:3x; crecieron antes del incidente con el bloqueo E510, `NOTAS`, las cuatro piezas del preregistro y los cinco cambios de sol-06: los comandos de la mañana, cada familia de error, el límite, el bloqueo y `HALT`) cada 15 minutos todo el día, y **cada 5 minutos entre las 14:50 y las 16:40 bog**. cada vuelta queda en `experimentos.jsonl` como `centinela-HHMM` (hora utc).
- compara cada vuelta con la anterior: **solo una repetición exacta que cambia acredita un cambio** (`DISENO.md` § 7). también la compara con el gemelo: si el original y la vuelta anterior coinciden pero el gemelo no, el error es del gemelo, no un cambio.
- la falsa alarma de la mañana (spec CA-03: el centinela creyó ver un cambio que era el titular de la cuenta) dejó la regla: **antes de llamar «cambio» a una diferencia, se repite exacta la secuencia vieja** (como 776–806 repitió 81–111).

## protocolo cuando el centinela avise (preparado antes)
1. **confirmar:** repetir exacta la última secuencia canónica y la secuencia del log que cubra lo que cambió. si la repetición vieja da lo de antes, no es un cambio: es contexto.
2. **congelar la mañana:** copiar `gemelo/modelo.json` a `gemelo/modelo-manana.json` y anotar aquí la última línea del log anterior al cambio. lo aprendido antes no se borra: queda como la versión de la mañana.
3. **explorar la diferencia por hipótesis**, con pedidos que separen lecturas (`lote.py`), igual que en la mañana. presupuesto reservado: ~2.000 pedidos.
4. **adaptar el gemelo como dato** primero (`modelo.json`: textos, códigos, límites, el control) y en código solo si la regla nueva es lógica con estado.
5. **volver a medir con la versión nueva:** las líneas del log anteriores al cambio que el cambio contradice se marcan `"fase": "manana"` (`python3 herramientas/fase.py --hasta <último id antes del cambio> --marcar`: marca la secuencia entera, porque el estado de un paso depende de los anteriores, y comprueba que esas secuencias calzan con `modelo-manana.json`) y el smoke las corre contra el modelo de la mañana; las secuencias canónicas (`repro-1`, `cmd-1`, `sol-03`, el centinela) se vuelven a correr contra el original para tener la versión de la tarde como referencia.
6. **la spec:** § 6 dice qué cambió, desde cuándo y con qué ids; las filas que ya no valen se marcan «hasta las HH:MM», no se borran.
7. **validación 2 (~17:00 bog):** solo con el gemelo adaptado, smoke en verde y romina avisada (`ESTADO.md`, reglas de las validaciones).
8. **congelar a las 19:55 bog** (romina, 15:0x): después de las 20:00 el set corre una vez más a una hora que no sabemos y railway redespliega con cada push a `gemelo/`. desde las 19:55 hasta el resultado final no se sube nada a `gemelo/`, `Dockerfile` ni `railway.json`: una adaptación que llegue tarde se queda en una rama y se anota aquí, no se despliega.

## si el incidente cambia mecánica: cómo entra una regla nueva con estado (pensado antes, sin implementar)

lectura de romina y del otro claude (13:2x bog): la caja parece pensada desde el lado gpt (trampas contra quien investiga, todo descubrible, significado que cambia con el tiempo). si es así, el cambio será de **mecánica** (estado, tiempo, autoridad) y no un número. el plan para absorberlo sin romper lo que ya calza:

1. **medir antes de tocar.** el centinela y una repetición exacta delimitan la regla: qué comando, desde qué pedido, qué la dispara. tres preguntas de entrada: ¿depende de **cuántos pedidos** (desde el reset, o en total), del **tiempo**, o de **quién** (token, titular, una confirmación)? hoy sabemos que el contador global `X-Req` no cambia ninguna respuesta (H7: 2254 → 2303 sin un efecto, log 2618–2669).
2. **la regla es una capa con nombre, apagada por defecto.** entra en la cadena de errores (D3) en el lugar que muestre el log, y se prende con un dato de `gemelo/modelo.json` (`"reglas": {"<nombre>": {…parámetros…}}`). con la regla apagada el gemelo es exactamente el de la mañana: el mismo código sirve para las dos versiones.
3. **dos modelos, un servidor.** al confirmar el cambio se congela `gemelo/modelo-manana.json` (protocolo, paso 2) y el servidor lee el modelo de una variable (`GEMELO_MODELO`). el smoke corre las líneas `"fase": "manana"` contra el modelo de la mañana y el resto contra el de la tarde: lo que calzaba sigue probado, no se borra.
4. **estado nuevo con valor neutro y que el reset borra**, como lo demás del `Banco`: contadores en 0, sin vencimientos, sin sesiones abiertas. una regla de tiempo se modela con reloj **solo si el log lo exige** (la misma secuencia con pausas distintas da respuestas distintas); si no, se cuenta en pedidos, que es determinista y reproducible. un test del set dura a lo sumo 12 pedidos y 5 s por paso: una regla de minutos casi nunca se ve dentro de un test, pero una de «n pedidos desde el reset» sí.
5. **autoridad como dato.** si aparece un rol, otro token con permisos o una confirmación nueva (como la de `HALT`), sus valores van en `modelo.json`; el gemelo solo conoce el token del equipo, y «con otro token responde como el original».
6. **volver a medir con la versión nueva:** las secuencias reproducibles (`repro-1`, `cmd-1`, `sol-03`, `fable-04`, `sol-04`, el centinela) se corren de nuevo contra el original con `herramientas/oraculo.py`, y el gemelo de la tarde tiene que calzar en las líneas nuevas y el de la mañana en las viejas.
7. **subir solo fuera de una validación y antes de las 19:55 bog** (congelado hasta el resultado final), con `X-Gemelo-Version` nuevo, y confirmar en el header de railway antes de la validación 2.

## interruptores preparados (gemelo v10, apagados hoy; `pruebas/test_piezas.py` prueba cada uno encendido)

si el centinela muestra uno de estos cambios, adaptarse es **cambiar un dato** en `gemelo/modelo.json`, correr el smoke y las pruebas, y subir fuera de una validación:

| si la caja… | dato a cambiar | además |
|---|---|---|
| cambia el valor del límite | `estado.limite.monto` | — |
| vuelve el límite acumulado por origen (sol-06 #1) | `estado.limite.acumulado.activo = true`, su `monto` y `codigo`; agregar `"acumulado"` a `orden.transfer` antes de `"saldo"` | si el código es nuevo, su status y texto en `errores` |
| rechaza anular si deja saldo negativo (sol-06 #2) | `estado.anula.permite_saldo_negativo = false`, `codigo_si_negativo` | el status y texto del código en `errores` |
| deja de desbloquear con un depósito (sol-06 #3) | sacar `"deposito"` de `estado.bloqueo.reinician` | — |
| cambia cuántas fallas bloquean o cuáles suman | `estado.bloqueo.tras_fallas`, `estado.bloqueo.suman` | — |
| cobra comisión por transferencia (sol-06 #4) | `estado.comision.monto` (y `solo_titulares_distintos`) | — |
| cambia la tabla de letras del control (sol-06 #5) | `control.letras = "iban"` (A=10…Z=35) o `"ascii"` | si es otra tabla, una línea en `control_esperado()` |
| cambia el módulo, el multiplicador o la comparación del control | `control.modulo`, `multiplicador`, `resta`, `formato`, `compara` | — |
| cambia el orden de los errores | `orden.http`, `orden.mensaje`, `orden.deposito`, `orden.transfer` | — |
| empieza a recortar espacios o a ignorar mayúsculas | `normalizacion.<parte>` (`recortar`, `mayusculas`, `minusculas`, `recortar_mayusculas`) | — |
| cambia un texto o un código de error | `errores` | — |
| cambia la confirmación de `HALT` | `estado.halt.confirmacion` | — |

lo que no está preparado y sería código: sesiones o créditos que vencen, confirmación en dos pasos, un comando nuevo con efecto propio, reglas que dependen del tiempo.

## detección
- primera señal, con consulta y hora: el ticket (15:30), no el original. **hasta las 15:40 bog el original sigue respondiendo como v1** para nuestro token: el centinela de las 15:33 y las 15:38 sin cambios (3769–3826, 4156–4213) y dos tandas de **repetición exacta** de secuencias de la mañana (`evals/v2/tanda-1.jsonl` y `tanda-2.jsonl`, seq `v2-*`): 316 pedidos (3827–4155: los 20 ejemplos, control, entrada, comandos, sugerencias, orden de errores, bordes, titular, bloqueo, HALT) y 217 (4214–4447: sin token, búsquedas de entrada, comandos ocultos, `NOTAS`, huecos E503/E508/E509, E507, bloqueo largo, parser). **0 diferencias en 533 pedidos**; los headers del original tampoco cambian. lectura: v2 todavía no llegó a nuestro token, o sus tres cambios están en rincones que nada de lo grabado toca.
- qué la detectó: el juez (el ticket) avisó; **en el original, la repetición exacta de `fable-04` y `sol-04` con el oráculo** (propuesta de fable en el issue #12) a las 15:57–15:58 bog (4630: el primer E510 con 423), y **el centinela solo** a las 15:59 (5082–5139: saldo, límite y la cascada). el cambio llegó a nuestro token entre las 15:54:21 (4621, último v1) y las 15:57:47 (4630, primer v2): 24 min después del ticket

## qué cambió (mecanismo, con evidencia)
tres comportamientos, como dijo el ticket, y nada más: en 460 pedidos que repiten exacto `fable-04` y `sol-04` (4622–5081), cada diferencia es de una de estas tres clases (27, 15 y 3).
1. **el límite entre titulares distintos baja de 100.000 a 50.000** (TR-15): 50.000 pasa (5147) y 50.001 no (5184; búsqueda acotada que acertó al primer paso); 99.999 y 100.000 dan E506 (5145, 5146). el mismo titular sigue exento (5148, 5149). antes: 100.000 pasaba (2020, 2045).
2. **el bloqueo responde 423 y cuenta los intentos** (TR-16, ER-23): `{"error":"E510","mensaje":"cuenta bloqueada","intentos":n}`. `intentos` sube con cada intento de transferir desde la cuenta bloqueada (5161–5163, 5165), no suma un E401 (5164), es por cuenta (5170) y vuelve a 1 cuando un depósito desbloquea y la cuenta se bloquea otra vez (5171–5176). cuándo se bloquea (tres E506/E507) y qué desbloquea no cambiaron. antes: 409 sin `intentos` (1913, 2222).
3. **el saldo de `CONSULTA` es texto con dos decimales** (CO-05): `250000` → `"2500.00"`, `-80` → `"-0.80"`, `10000049999` → `"100000499.99"` (4743, 4975, 5153). los montos de entrada siguen en enteros.

## cómo se adaptó
- qué hizo el sistema solo: el centinela avisó a las 15:59 («CAMBIO DEL ORIGINAL» y «GEMELO DIFIERE», con los ids); `fase.py` separó solo la mañana de la tarde (167 secuencias, 3045 líneas marcadas `"fase": "manana"`, y las 167 calzan con `modelo-manana.json`).
- qué hicimos nosotros (16:0x–16:1x bog): congelamos `gemelo/modelo-manana.json`; en `gemelo/modelo.json`, **dos datos** (límite 50.000, status 423 del E510) y **dos interruptores nuevos** con su código (`estado.bloqueo.informa_intentos`, `saldo_formato: "decimal2"`; ~15 líneas en `servidor.py`). smoke con los dos modelos (tarde 172/172, mañana 167/167) y pruebas 23/23, con una clase nueva para la tarde. **gemelo v15**. de lo preparado, el límite y el código de error eran datos; el contador y el formato no estaban previstos.

## lo que queda sin separar
- si `intentos` tiene tope o vuelve a empezar por otra causa (anular, recibir): no se probó.
- si el saldo con texto aparece en alguna otra respuesta: hoy solo `CONSULTA` muestra saldos; `NOTAS` no cambió (5136).
- el límite nuevo con montos de 50.001 a 99.999 entre titulares distintos: probado en los bordes (50.001, 99.999), no en el medio.
