# brief del reto 2 · la caja negra

> copiado del portal (frontier.lab10.ai/evento/reto) por romina, sáb 10 oct 2026 ~09:47 bog. horas en bogotá (utc-5). el material (readme con el formato de spec y log) se libera al elegir el reto y va en `material/`.

## resumen
descubrir cómo se comporta un servicio sin documentación y construir un reemplazo que responda exactamente igual.

## brief
heredamos un servicio que lleva 10 años en producción. nadie sabe qué hace exactamente. no hay código fuente, no hay documentación y las dos personas que lo escribieron ya no están. sabemos que recibe mensajes y responde, y que si lo apagamos la empresa se cae. necesitamos entenderlo por completo y construir un reemplazo que se comporte **exactamente igual, incluidos sus errores**.

## restricciones
- no usar herramientas que hagan el trabajo por ti. **scripts y fuzzers propios sí.**
- el reemplazo **no puede llamar al original ni a otro reemplazo**.
- entregables: el reemplazo desplegado, la especificación y el log de experimentos. el formato de los tres está en el readme del material.
- (romina, 10 oct) no se puede importar código escrito antes del evento. tokens fuera del presupuesto del evento, permitidos.

## contrato del entrypoint
desplegado por el equipo, accesible desde internet **desde las 20:00 hasta que termine el demo day**. despliegue donde quieras.

| elemento | comportamiento |
|---|---|
| `Authorization: Bearer <token>` | todas las llamadas incluyen el token del equipo en este header. |
| `GET /health` | responde 200 cuando el servicio está listo. |
| `/*` (url base) | acepta exactamente los mismos requests que el servicio original, **incluidas las rutas que no existen**. |
| `POST /__reset` | vuelve el reemplazo a su estado inicial. lo llaman antes de cada test. **con otro token o sin token, responde como el original.** |

## entregables
- **systems design, 12:00:** doc de diseño (una página, pdf o enlace) y diagrama de arquitectura.
- **ejecución, 20:00:** repo (url pública), entrypoint (url pública con `GET /health` y el token del equipo), video de 2 min, **especificación del servicio**, **log de experimentos**.
- **demo day:** material del pitch, opcional.

## rúbrica (lo nuevo frente a la del portal general: ver `RUBRICA.md`)
- set oculto: <25 % de casos = 1 · hasta 50 % = 2 · hasta 75 % = 3 · más = 4. corre en cada validación del día y una vez más tras las 20:00.
- **especificación (reto 2):** que otro ingeniero pueda reimplementar el servicio con la spec, y que **cada comportamiento cite la línea del log que lo prueba**. un 4: cubre la mayoría, cada uno con su línea del log, y **marca qué es confirmado y qué es supuesto**.
- incidente a las **15:30**.
