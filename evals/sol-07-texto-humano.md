# sol-07 · texto humano cruzado con estado

Sol · mandato de Romina en chat · 10 oct 2026. **Todos los nombres son inventados**; no representan clientes ni personas reales. Ningún nombre se obtuvo de un directorio o dataset.

**30 secuencias independientes, 165 pedidos: 17 de 6, 11 de 5 y 2 de 4.** El oráculo agrega un reset por secuencia: **195 llamadas** en total. 16 secuencias de identidad del titular y 14 de montos. Son predicciones, no mediciones: **0 llamadas al original, 0 al gemelo y 0 validaciones del portal**.

Fuentes: [spec.md en 0e798d25753e6cb017ac6c4ea0319e64e72b4833](https://github.com/rominapitronello/frontier-bog26-caja-negra/blob/0e798d25753e6cb017ac6c4ea0319e64e72b4833/spec.md), blob `49802ebfa1a532cdc02b64e26529e6451a199622`; [LECCIONES_DEL_ENSAYO.md, lección 18](https://github.com/rominapitronello/frontier-bog26-caja-negra/blob/0e798d25753e6cb017ac6c4ea0319e64e72b4833/LECCIONES_DEL_ENSAYO.md). También se leyeron AGENTS.md, ESTADO.md y RUBRICA.md. Se inspeccionó oraculo.py solo para verificar el contrato de ejecución. No se usaron el código del gemelo ni el log para generar predicciones. Esta ventana ya participó en sol-05 y sol-04: **no se declara cegamiento completo**.

La lección 18 se concreta en alternativas de implementación: igualdad literal, NFC/NFKC, reemplazo de puntuación, colapsar `\\s+`, eliminar caracteres de formato, mapas de homoglifos, `[0-9]` frente a `\\d`, eliminación de separadores, lectura decimal o captura parcial. Las formas con coma/punto y los nombres copiados están escritos a mano; no son mutaciones aleatorias.

## Cómo correrlo

Quien lidera integra el PR con merge commit y, con las variables del original ya cargadas en su entorno, ejecuta:

```sh
python3 herramientas/oraculo.py evals/sol-07-texto-humano.jsonl
```

El oráculo agrupa por `seq`, hace `POST /__reset` antes de cada grupo y preserva el string `request.m` con JSON UTF-8. **No agregar otro reset ni normalizar los nombres o los montos antes del pedido.** Registrar la fase y versión vigentes: las predicciones corresponden al snapshot citado de la spec, previo al incidente. El reset no figura como fila del catálogo y sí cuenta en el presupuesto. El resultado observado debe añadirse como evidencia aparte; conservar las predicciones originales.

## Cómo leer las dudas

Cada fila conserva el contrato `id, seq, request, status, response, spec, hipotesis`. `status/response` contienen una **predicción concreta**, aun donde existe incertidumbre. `observado:false` evita confundirla con respuesta real. `ambiguo`, `tipo_ambiguedad`, `desconocidos` y `alternativa` señalan las generalizaciones no comprobadas para estos literales. Las filas posteriores llevan `depende_de`: si falla un alta o cambia el movimiento, sus saldos e IDs ya no pueden interpretarse como errores independientes. Los casos 04 y 06 son testigos con titulares exactamente repetidos; no se les inventa un silencio de identidad.

`texto_humano.literal` es el argumento enviado. `escapado` y `no_ascii` permiten identificar tildes combinables, espacios invisibles y homoglifos, con posición y nombre Unicode. La representación escapada sirve para auditar; **no se envía en lugar del literal**. En el cuadro se muestran escapes para que las diferencias no desaparezcan al leer.

El control sigue IN-05/IN-09: se toman letras y dígitos **ASCII del mensaje original**, las letras A=1…Z=26, todo lo demás se ignora, y se aplica `98 - (100*N mod 97)`. No se hace NFC/NFKC antes del cálculo. Un `é` ignorado y un `e + U+0301` cuentan diferente; que dos mensajes tengan el mismo control tampoco significa que el titular o el monto sean iguales. Si llega E202 en vez del error de monto esperado, investigar primero la lectura del control para ese carácter.

## Catálogo

| Nº | Texto humano (escape de revisión) | Regla de estado | Pedidos |
|---|---|---|---|
| 01 | `L\u00eda Nublario` / `Li\u0301a Nublario` | identidad del titular + límite + anular depósito gastado | 6 |
| 02 | `I\u00f1aki Brumal` / `In\u0303aki Brumal` | identidad del titular + límite + anular depósito gastado | 6 |
| 03 | `L\u00fcna Cenizal` / `Lu\u0308na Cenizal` | identidad del titular + límite + anular depósito gastado | 6 |
| 04 | `\u00c1mbar Pe\u00f1a-Luz` / `\u00c1mbar Pe\u00f1a-Luz` | titular repetido + límite | 5 |
| 05 | `No\u00e9 O'Brum` / `No\u00e9 O\u2019Brum` | identidad del titular + límite + anular depósito gastado | 6 |
| 06 | `Ma\u00ebl O\u2019Nube` / `Ma\u00ebl O\u2019Nube` | titular repetido + límite | 5 |
| 07 | `Nora-Luz Pomal` / `Nora\u2011Luz Pomal` | identidad del titular + límite + anular depósito gastado | 6 |
| 08 | `Nora-Luz Pomal` / `Nora\u2013Luz Pomal` | identidad del titular + límite + anular depósito gastado | 6 |
| 09 | `In\u00e9s  Nacaral` / `In\u00e9s Nacaral` | titular repetido + límite | 5 |
| 10 | `Sol\u00e9n\u00a0Brumario` / `Sol\u00e9n Brumario` | identidad del titular + límite + anular depósito gastado | 6 |
| 11 | `L\u00eda\u202fNublario` / `L\u00eda Nublario` | identidad del titular + límite + anular depósito gastado | 6 |
| 12 | `No\u200bra Nublario` / `Nora Nublario` | titular repetido + límite | 5 |
| 13 | `I\u00f1aki\u200d Brumal` / `I\u00f1aki Brumal` | identidad del titular + límite + anular depósito gastado | 6 |
| 14 | `Nora\u2060 Nacaral` / `Nora Nacaral` | identidad del titular + límite + anular depósito gastado | 6 |
| 15 | `\u0391lma Brumario` / `Alma Brumario` | titular repetido + límite | 5 |
| 16 | `Nor\u0430 Nublario` / `Nora Nublario` | titular repetido + límite | 5 |
| 17 | `\uff11\uff12` | rechazos de monto y racha de transferencias | 6 |
| 18 | `1\uff12` | rechazos de monto y racha de transferencias | 6 |
| 19 | `\uff11\uff12` | rechazo sin abono ni consumo de id de operación | 4 |
| 20 | `\u0661\u0662` | rechazos de monto y racha de transferencias | 6 |
| 21 | `1.000` | rechazo sin abono ni consumo de id de operación | 5 |
| 22 | `1,000` | rechazo sin abono ni consumo de id de operación | 6 |
| 23 | `1\u00a0000` | rechazo sin abono ni consumo de id de operación | 5 |
| 24 | `1\u202f000` | rechazo sin abono ni consumo de id de operación | 6 |
| 25 | `1  000` | rechazo sin abono ni consumo de id de operación | 5 |
| 26 | `1,50` | rechazo sin abono ni consumo de id de operación | 6 |
| 27 | `1.50` | rechazo sin abono ni consumo de id de operación | 5 |
| 28 | `1.234,56` | rechazo sin abono ni consumo de id de operación | 5 |
| 29 | `1,234.56` | rechazo sin abono ni consumo de id de operación | 6 |
| 30 | `10\u200b0` | rechazo sin abono ni consumo de id de operación | 4 |

Los casos de nombres contrastan primero la transferencia financiada de 150001: E506 bajo igualdad literal para nombres diferentes, éxito para los idénticos. Diez continúan anulando el depósito que la financiaba y consultando el saldo; seis consultan el destino directamente. Si una normalización equipara nombres diferentes, también cambia el balance posterior a ANULA. El caso 23 agrega U+00AD (guion blando) en el nombre inventado.

En los montos se separan dos efectos: producir un movimiento y consumir un ID. En 19/30 el depósito ASCII posterior debe ser OP-0001; en 21–29 debe ser OP-0002. Los candidatos de TRANSFER de 22/24/26/29 van entre titulares exactamente repetidos y con fondos para quitar el límite y el saldo como explicaciones alternativas.

17/18/20 parten de dos E507. El candidato Unicode se predice E303 y el intento ASCII siguiente se predice E507. Si el candidato se interpreta como entero, sería una tercera falla de saldo y el siguiente intento daría E510. **Este diseño no distingue conservar de reiniciar la racha cuando el candidato se rechaza**; no se afirma que pruebe ambas cosas.

## Verificación y rúbrica

Verificación fuera de línea: 165 controles mediante dos implementaciones independientes (acumulador módulo 97 y expansión ASCII a entero), con cuatro referencias conocidas; formato JSONL y compatibilidad del contrato del oráculo; 30 grupos de 4–6 pedidos; referencias de spec existentes; saldos, IDs y rachas comprobados con un libro mayor separado; ida y vuelta de JSON, escapes y puntos Unicode; cuerpos muy por debajo de 8192 bytes. Ninguna verificación usó red hacia el servicio.

RUBRICA.md, ejecución y transversales: casos nuevos frente al material, hipótesis con regla de estado, incertidumbre primaria separada de sus consecuencias y comando reproducible. Límites: no se midió al original ni se ejecutó el gemelo; no se afirma mejora de puntaje, respuesta al incidente ni descubrimiento de fallos ocultos. Es un catálogo documental, sin cambio del entrypoint; smoke.sh y el despliegue corresponden a quien integra. El costo real de generación en llamadas al original/gemelo y validaciones es cero; 195 es el costo futuro exacto de ejecutar una vez con el oráculo. No contiene credenciales ni datos de personas reales.

Siguiente: quien lidera registra las respuestas reales y separa diferencias de predicción, diferencias del gemelo y divergencias causadas por el incidente. Romina no necesita hacer ningún paso técnico para integrar este catálogo.
