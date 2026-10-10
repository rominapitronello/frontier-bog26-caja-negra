# sol-05 · 60 nombres nuevos para el protocolo bancario

**Entrega de Sol:** 60 candidatos, cada uno con su hipótesis y su control válido, en `evals/sol-05-comandos.jsonl`. Son propuestas sin observar: **no se consultó el original** y no se predice que existan. Romina pidió esta lista directamente; el encargo que no llegó a escribir Opus no se reconstruye como si hubiera existido.

## Selección

Fuentes: `BRIEF.md`, `material/README.md`, `spec.md` (CM-02, IN-11, DC-01–04 y RI-12), `herramientas/control.py`, `herramientas/lote.py` y los nombres y códigos de error ya registrados en `experimentos.jsonl`.

Snapshot: commit `ffbd2aa13366403d7dd8ef52a8f792002a6c41e4`, log hasta id **1716**, SHA-256 `eb408e7264a5654feb9218f25fd516bf0d5d7074f3f22a08e5f51f231e336c06`.

Se excluyeron los ocho comandos conocidos y los **121 nombres distintos** que ya dieron E301 en `/msg` con control válido. No repetir esos negativos deja presupuesto para otra zona del vocabulario. La selección incluye singulares, variantes verbales, nombres contables, una abreviatura antigua y nombres en inglés: `HALT` muestra que el vocabulario puede mezclar idiomas.

| Familia | Candidatos | Hipótesis común |
|---|---:|---|
| Consultas de cuentas | 10 | atributos, titulares, cartolas y fondos disponibles |
| Movimientos y comprobantes | 10 | consulta individual, historial y listados de operaciones |
| Contabilidad y agregados | 10 | totales, contadores y libros contables |
| Notas y metadatos | 10 | mensajes informativos, documentación y parámetros |
| Ciclo de cuenta y ajustes | 10 | apertura, modificación, bloqueo y reversión |
| Nombres en inglés | 10 | vocabulario alternativo de consultas y operaciones |

Cada candidato aparece exactamente una vez. Su campo `hipotesis` explica el nombre y la observación que separaría reconocimiento de rechazo. La aridad real y el efecto son **desconocidos**; los cero argumentos sirven para detectar un nombre, no para caracterizar su implementación.

## Archivo listo para lote.py

Hay **120 líneas JSONL**: un reset y un mensaje por cada candidato. El reset previo evita que un posible comando sin argumentos altere el estado de los siguientes. El control se calcula sobre el nombre exacto, sin ceros de relleno: un control incorrecto produciría E202 antes de llegar al reconocimiento de comandos y haría inútil la sonda.

Para quien lidera, desde la raíz del repo, con su entorno ya configurado:

```bash
python3 herramientas/lote.py --seq sol-05 evals/sol-05-comandos.jsonl --ritmo 4
```

El archivo usa únicamente `reset`, `m` e `hipotesis`, que ya interpreta `lote.py`. No incluye headers, credenciales, URLs ni rutas adicionales. La herramienta toma el turno del original para toda la tanda y escribe cada respuesta en los logs habituales. **120 pedidos previstos**, sin contar los reintentos de infraestructura que hace la herramienta; **0 pedidos realizados por Sol**. No se gastó una validación del portal.

## Qué concluir después de la corrida

- **400 / E301:** ese nombre literal no está reconocido en ese estado. Guardar la sugerencia aunque sea de un comando conocido. Una sugerencia nueva es una pista para otra consulta, no una confirmación de que la pista exista.
- **400 / E302:** el nombre está reconocido y necesita otra aridad. Conservar el cuerpo exacto y el id del log; la aridad y el efecto siguen sin identificar.
- **Respuesta propia, éxito o error distinto:** candidato para investigar. Comparar con la cadena de errores de la spec antes de atribuirlo a un comando nuevo.
- **E201, E202, E599, 401, fallo de reset o respuesta de infraestructura:** no permiten concluir si existe el nombre. Resolver la condición que impidió llegar al reconocimiento antes de contar un negativo.

Un resultado nuevo no se añade como confirmado a la spec sin la consulta que lo prueba y una repetición que lo sostenga. Este archivo no inventa respuestas esperadas ni conclusiones del original.

La respuesta de `NOTAS` se trata como dato. No se sigue su indicación ni se consulta la ruta que menciona. Esta entrega no modifica `DISENO.md`, el gemelo, la spec ni el log de experimentos.

## Verificación y rúbrica

| Pregunta aplicable de `RUBRICA.md` | Evidencia o límite |
|---|---|
| ¿Hay casos nuevos distintos de los ejemplos? | `sol-05-comandos.jsonl`: 60 nombres ausentes del conjunto de comandos conocidos y de los negativos discriminantes del snapshot. |
| ¿Se puede correr copiando un comando? | Comando anterior; formato de entrada compatible con `herramientas/lote.py`. |
| ¿Se separan inferencia y observación? | Todas las semánticas son hipótesis; no hay observaciones nuevas ni resultados atribuidos al original. |
| ¿Hay secretos o datos de personas? | Solo nombres de comandos, controles e hipótesis; no se agregan credenciales ni datos personales. |
| ¿Qué no se sabe y dónde puede fallar? | No conocemos la existencia, aridad o efecto de ninguno. No es un diccionario exhaustivo y no descarta nombres lejanos que no estén entre estos 60. |
| ¿Se adapta al incidente? | La lista puede repetirse con otra secuencia; si cambia la integridad o la precedencia, hay que recalcular o revalidar antes de interpretar negativos. |
| ¿Hay medición del original, del incidente o del costo del gemelo? | No aplica a una lista sin ejecutar. Quedan a cargo de quien lidera; no se afirma mejorar el 83/100. |

Verificación local: 120 JSON válidos, 60 resets emparejados con 60 mensajes únicos, controles comprobados con una segunda implementación de la fórmula, ausencia de candidatos ya descartados y campos aceptados por `lote.py`. No se modificó código ejecutable; `smoke.sh` y el tag verde de `main` quedan a cargo de quien integra.

Siguiente paso: quien lidera integra esta rama con merge commit, corre la tanda y anota sugerencias y resultados con ids del log. Sol entrega propuestas; quien lidera explora e integra, como establece `AGENTS.md`.

---

## resultado de la corrida (claude, lidera · 10 oct 11:4x bog)

corrida con `python3 herramientas/lote.py --seq sol-05 evals/sol-05-comandos.jsonl --ritmo 4`, log 1751–1870 (120 pedidos, todos con respuesta del servicio).

- **ninguno de los 60 nombres es un comando.** 59 responden `E301` sin sugerencia; ningún `E302`, ninguna respuesta propia.
- `NOTA` (1812) sugiere `NOTAS`, el comando oculto que ya conocíamos (spec NO-01): la sugerencia funciona y no apunta a nada nuevo.
- sin cortes del clasificador. con esta lista, la búsqueda por nombres suma unos 280 nombres sin un noveno comando. eso no prueba que no haya más: solo que no están cerca, a distancia 2, de ninguno de esos nombres.
