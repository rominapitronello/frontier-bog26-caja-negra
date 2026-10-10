# encargo fable-01 · la tercera mirada sobre el diseño, y el espacio de los accesos raros

> **reemplazado (10 oct 11:5x chile):** se escribió antes del brief, sobre un supuesto «acceso raro» que el brief del reto 2 no confirma. el reto es clonar un servicio http con estado (`BRIEF.md`, `DISENO.md`). no se ejecuta; queda como genealogía.

**fable, razonamiento alto. juicio, no velocidad: objeta lo que veas, aunque contradiga al que lidera.**

de: claude (lidera, sesión `01MD7…`) · 10 oct 11:5x chile · repo: `rominapitronello/frontier-bog26-caja-negra` (público)

## contexto en cuatro líneas
reto 2, la caja negra. según romina: 5 ejemplos, ~100 tests ocultos; la caja es un **servicio sin documentación con un acceso que no es el común**; **el incidente (15–16 bog) cambia el acceso**. el sistema tiene que aprender del entorno, no memorizar cómo se accede. lo que construyamos cumple un **contrato** para que otros agentes accedan al servicio a través de él. si `BRIEF.md` está en el repo, manda sobre todo esto.

lee `AGENTS.md`, `ESTADO.md`, `DISENO.md` y `RUBRICA.md`. no necesitas ver código: todavía no hay.

## lo que te pido (dos piezas, en este orden)

**1 · objeción al diseño, antes de las 11:30 bog** (el diseño se entrega a las 12:00). en `encargos/fable-01-respuesta.md`:
- lo que no te convence de `DISENO.md`, sobre todo **D0** (el acceso como perfil aprendido) y **D0b** (canario y re-descubrir). ¿dónde se rompe? ¿qué cambio de acceso no lo detectaría el canario?
- qué falta para que la sección de systems design saque 4 en la rúbrica (`RUBRICA.md` § 01): supuestos con su costo, alternativas descartadas, escalabilidad.
- una frase: si tuvieras que apostar, ¿qué cambia el incidente?

**2 · el espacio de los accesos raros** (lección 18 del ensayo, aplicada al acceso): una lista escrita a mano de **cómo programaría un acceso «no común» alguien que arma una caja para una hackatón en una tarde**. no lo que haría un ingeniero de apis serio: lo que haría un autor apurado que quiere que cueste. por cada forma: cómo se ve desde afuera (qué error o qué respuesta da si le hablas como a una api normal) y **qué sonda la distingue** de las vecinas. ordena de más probable a menos. ejemplos de ejes, no exhaustivos: método, ruta, dónde va la credencial, formato del cuerpo, codificación, firma, un desafío previo, paginación o estado entre llamadas, versionado, cabeceras raras, mensajes de error que dan pistas. en `encargos/fable-01-accesos.md`, o mejor como `evals/accesos/espacio.jsonl` si te da para que sea legible por máquina (`{"forma", "como_se_ve", "sonda_que_la_distingue", "probabilidad"}`).

## cómo entregas
rama `fable/objecion-y-accesos`, commits con tu firma (`claude@pasaelfiltro.cl`, en el cuerpo `Claude-Session:` y que eres fable), un PR a `main`. **no fusionas**: la vigilancia del que lidera ve tu push y lo integra. si algo de esto choca con tu juicio, dilo en la respuesta (agents.md § 10).

## qué no hacer
- no toques la caja ni el servicio: las llamadas pueden contar contra un presupuesto.
- nada privado en el repo: es público.
