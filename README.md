# el gemelo · frontier bog/26 · reto 2, la caja negra

**una frase:** un servicio bancario de mensajes que nadie documentó (`POST /msg` con `{"m": "CMD;arg;…;control"}`), estudiado pedido a pedido hasta poder reemplazarlo por uno nuestro que responde **exactamente igual**, errores y rarezas incluidos, sin llamarlo nunca.

lo que sabemos del original está en [`spec.md`](spec.md), con cada comportamiento citando la línea del log que lo prueba ([`experimentos.jsonl`](experimentos.jsonl)). cómo y por qué lo construimos así, en [`DISENO.md`](DISENO.md).

## correrlo

requisitos: **python 3.9 o más nuevo, nada más** (solo biblioteca estándar; sin llaves, sin red, sin modelos).

```
git clone https://github.com/rominapitronello/frontier-bog26-caja-negra && cd frontier-bog26-caja-negra
GEMELO_TOKEN=un-token PORT=8080 python3 gemelo/servidor.py          # 1. el gemelo, en http://127.0.0.1:8080
bash smoke.sh                                                        # 2. prueba de humo (levanta su propio gemelo)
```

con el gemelo andando (paso 1), en otra terminal:

```
curl -s -H 'Authorization: Bearer un-token' http://127.0.0.1:8080/health
# {"ok":true}
curl -s -X POST -H 'Authorization: Bearer un-token' -d '{"m":"ALTA;Lucia;82"}' http://127.0.0.1:8080/msg
# {"cuentaId":"AC-0001"}
curl -s -X POST -H 'Authorization: Bearer un-token' -d '{"m":"ALTA;Lucia;83"}' http://127.0.0.1:8080/msg
# {"error":"E202","mensaje":"control inválido"}
python3 herramientas/control.py 'DEPOSITO;AC-0001;5000'           # el dígito de control de un mensaje → 63
python3 medir.py --casos material/pruebas/ejemplos.jsonl --gemelo http://127.0.0.1:8080 --token un-token
# Secuencias que pasan: 1/1
```

- **el contrato del reto:** `Authorization: Bearer <token del equipo>` en todo; `GET /health` → 200 cuando está listo; `POST /__reset` vuelve al estado inicial; cualquier otra ruta responde lo mismo que el original, incluidas las que no existen. el token se configura con `GEMELO_TOKEN`; sin él, el gemelo no arranca (falla ruidoso, no responde 401 a todo en silencio).
- **despliegue:** `Dockerfile` + `railway.json` (una réplica, sin dormir, healthcheck en `/health`). el set del jurado le habla a un solo proceso: el estado vive en memoria.
- **pruebas:** `bash smoke.sh` pasa al gemelo los 20 ejemplos del material y **todas las secuencias del log** con la regla de comparación del juez (status + cuerpo; json sin orden de claves). `python3 pruebas/test_medir.py` prueba el comparador.
- **costo por caso:** 0 us$ y menos de un milisegundo: el gemelo no llama a nadie ni usa modelos (`DISENO.md`, D6).

## resultados

| cuándo | set oculto del jurado (100 tests) | nota |
|---|---|---|
| 10 oct 11:06 bog · validación 1 de 3 | **83/100** | línea base, sin desglose. un redespliegue nuestro pudo caer a mitad de la corrida (`ESTADO.md`) |

nuestras propias mediciones, sin gastar validaciones: el gemelo reproduce los 20 ejemplos y todas las secuencias del log (`bash smoke.sh`), y las 40 secuencias que sol escribió solo desde la spec (`evals/sol-03.jsonl`: 141 de 141).

## qué hay adentro

| archivo | qué es | criterio |
|---|---|---|
| `gemelo/servidor.py` | el reemplazo: la cadena de errores en el orden observado y el estado (cuentas, operaciones, bloqueos, `HALT`) | ejecución |
| `gemelo/modelo.json` | lo aprendido como **dato**: errores, aridades, límites, el control, `HALT`. cada valor cita el log. si el servicio cambia un texto o un límite, se cambia aquí | ejecución · cambio |
| `spec.md` | el servicio para reimplementarlo sin tocarlo: 7 secciones, cada fila con evidencia y confianza (confirmado / probable / supuesto) | ejecución |
| `experimentos.jsonl` | **cada pedido que le mandamos al original**, con su hipótesis; `experimentos_crudo.jsonl` guarda los headers (el token tapado) | ejecución |
| `DISENO.md` | diseño de una página, diagrama, decisiones con su alternativa descartada, escalabilidad y cambio | systems design |
| `herramientas/` | `lote.py` y `sonda.py` (mandan y anotan pedidos), `control.py` (el dígito de control), `centinela.py` (repite una secuencia canónica y avisa si el original cambia o el gemelo difiere), `vigilancia.sh` (avisa cada push) | método |
| `medir.py` | el comparador con la regla del juez (lo escribió sol) | plan para medir |
| `encargos/` | lo que se le pidió a cada modelo y lo que respondió | cómo trabajamos |
| `incident.md`, `debrief.md`, `evals/` | el incidente de la tarde, el debrief y el set retenido (se llenan durante el día) | incidente · resultados |
| `AGENTS.md`, `ESTADO.md`, `RUBRICA.md` | cómo trabajamos, el estado en vivo y la hoja contra la que se revisa cada entrega | — |

## qué encontramos (lo grueso; el detalle con evidencia está en la spec)

- **el dígito de control es el del iban** (iso 7064 mod 97-10): las letras valen su posición en el alfabeto, los dígitos lo que son, y control = 98 − (100·N mod 97). salió de mirar los ejemplos, sin gastar pedidos, y lo encontraron por separado claude y fable.
- **ocho comandos**, dos ocultos: `HALT;1` detiene el servicio para el token (503) hasta el reset, y `NOTAS` devuelve una nota interna. aparecieron porque el error de comando desconocido **sugiere** el comando más parecido (`HELP` → `HALT`, `TOTAL` → `NOTAS`).
- **reglas con estado que los ejemplos no muestran:** el límite de 100.000 no aplica entre cuentas del mismo titular (por nombre); tres transferencias rechazadas seguidas bloquean la cuenta (`E510`) hasta un depósito; anular puede dejar saldos negativos.
- **el orden exacto de 20 códigos de error**, de la ruta al saldo, con un pedido que rompe dos cosas a la vez para cada par.

## cómo trabajamos

este repo lo escribieron **una persona y varios modelos que firman lo que escriben**. no es un adorno: es parte de lo que estamos mostrando.

```mermaid
flowchart TB
  R([romina<br/>decide y aprieta los botones sin vuelta])
  CL[claude · lidera<br/>vigila el repo, explora el original,<br/>construye el gemelo, integra]
  FA[fable · la tercera mirada<br/>objeta el diseño, reimplementa<br/>desde la spec sin ver el código]
  SO[sol · desde otra casa de modelos<br/>el comparador y el oráculo:<br/>secuencias escritas solo desde la spec]
  REPO[(este repo<br/>ramas · merge commits · ESTADO.md)]
  R -- mandato --> CL
  CL -- encargo con modelo y razonamiento --> FA & SO
  FA & SO -- rama o PR --> REPO
  REPO -- la vigilancia ve el push y despierta a quien sigue --> CL
  CL -- merge commit, nunca squash --> REPO
  CL -- reporte: qué pasó, qué significa, qué te toca --> R
```

- **cada commit lo firma quien lo pensó** (`git shortlog -sne`): claude, sol, fable o romina. sin coautorías de cortesía.
- **la genealogía queda a la vista:** las ramas de cada pluma entran con merge commit, nunca squash (`git log --graph --oneline`).
- **coincidir no es observar:** que claude y fable llegaran a la misma fórmula del control no la confirmó; la confirmaron pedidos nuevos al original. y la spec la ponen a prueba secuencias que escribe otra casa de modelos sin ver nuestro código (`encargos/sol-03-oraculo.md`).
- **las reglas salen de errores:** cada *cicatriz* de `AGENTS.md` es algo que nos salió mal y la regla que dejó.
- **lo que no está escrito no existe:** decisiones, supuestos y fallas van a un archivo con hora y firma (`ESTADO.md`).
- **cualquiera puede decir que no:** un «no pude» o un «no quise, y por esto» vale más que un resultado inventado (`AGENTS.md` § 10).

## lo que no salió

- **un bucle nuestro gastó ~400 pedidos.** una búsqueda binaria del tope del cuerpo no podía armar cuerpos de 8.192 y 8.193 bytes, volvía atrás y repetía el mismo pedido; romina la cortó. quedan en el log (líneas 289–686, marcadas) porque se mandaron. desde entonces `lote.py` se detiene si un pedido se repite más de 5 veces seguidas.
- **la v1 de la spec decía mal el orden entre límite y saldo.** lo leímos de un solo pedido (111) que, sin saberlo, era entre dos cuentas del mismo titular. lo vio el centinela en su primera vuelta; una repetición exacta descartó que el original hubiera cambiado y separó la causa (el titular). la spec lo cuenta en CA-03.
- **la primera fórmula del control tenía mal el rango** (0–96 en vez de 2–98): la separaron dos pedidos elegidos para eso (24–27).
- **los tags verdes no suben desde la sesión que lidera:** el proxy de git de su entorno rechaza el push de tags (403). `verde-01` existe en local; queda anotado en `ESTADO.md`.
