# incident.md · el cambio de las 15:30 bog

> criterio que alimenta: **respuesta al incidente** (ejecución). un 4: detectan el cambio, se adaptan y lo explican. lo que dice «null» se llena cuando ocurra; el protocolo de abajo se escribió **antes** del cambio (10 oct 11:3x bog), para que se vea qué teníamos preparado y qué improvisamos.

**hora del cambio (según el juez):** null · **cómo se anunció:** null

## cómo lo vamos a detectar (preparado antes)
- **el centinela** (`herramientas/centinela.py`) repite una secuencia canónica de 34 pedidos (los comandos de la mañana, `NOTAS`, cada familia de error, el límite, el bloqueo y `HALT`) cada 15 minutos todo el día, y **cada 5 minutos entre las 14:50 y las 16:40 bog**. cada vuelta queda en `experimentos.jsonl` como `centinela-HHMM` (hora utc).
- compara cada vuelta con la anterior: **solo una repetición exacta que cambia acredita un cambio** (`DISENO.md` § 7). también la compara con el gemelo: si el original y la vuelta anterior coinciden pero el gemelo no, el error es del gemelo, no un cambio.
- la falsa alarma de la mañana (spec CA-03: el centinela creyó ver un cambio que era el titular de la cuenta) dejó la regla: **antes de llamar «cambio» a una diferencia, se repite exacta la secuencia vieja** (como 776–806 repitió 81–111).

## protocolo cuando el centinela avise (preparado antes)
1. **confirmar:** repetir exacta la última secuencia canónica y la secuencia del log que cubra lo que cambió. si la repetición vieja da lo de antes, no es un cambio: es contexto.
2. **congelar la mañana:** copiar `gemelo/modelo.json` a `gemelo/modelo-manana.json` y anotar aquí la última línea del log anterior al cambio. lo aprendido antes no se borra: queda como la versión de la mañana.
3. **explorar la diferencia por hipótesis**, con pedidos que separen lecturas (`lote.py`), igual que en la mañana. presupuesto reservado: ~2.000 pedidos.
4. **adaptar el gemelo como dato** primero (`modelo.json`: textos, códigos, límites, el control) y en código solo si la regla nueva es lógica con estado.
5. **volver a medir con la versión nueva:** las líneas del log anteriores al cambio que el cambio contradice se marcan `"fase": "manana"` y el smoke las salta; las secuencias canónicas (`repro-1`, `cmd-1`, `sol-03`, el centinela) se vuelven a correr contra el original para tener la versión de la tarde como referencia.
6. **la spec:** § 6 dice qué cambió, desde cuándo y con qué ids; las filas que ya no valen se marcan «hasta las HH:MM», no se borran.
7. **validación 2 (~17:00 bog):** solo con el gemelo adaptado, smoke en verde y romina avisada (`ESTADO.md`, reglas de las validaciones).

## detección
- primera señal, con consulta y hora: null
- qué la detectó: el sistema solo / una pluma / el juez: null

## qué cambió (mecanismo, con evidencia)
null

## cómo se adaptó
- qué hizo el sistema solo: null
- qué hicimos nosotros: null

## lo que queda sin separar
null
