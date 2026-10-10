# RUBRICA.md · lo que mira el jurado, entrega por entrega

> regla de la casa (mandato de romina, 10 oct 11:2x chile): **ninguna entrega sale sin pasar por esta hoja.** quien entrega, sea la pluma que sea, recorre la tabla de su entrega y responde cada pregunta de control con un archivo, no con una intención. si una respuesta es «no», se arregla o se escribe como límite conocido (eso también puntúa: «incluido lo que no salió»).

fuente: rúbrica del portal, copiada en `contexto-evento.md` § 7 del ensayo. escala 1 a 4 por criterio. «evaluamos lo que entregan, lo que despliegan y lo que explican. no recolectamos sesiones ni transcripts.» → **lo que no está en un archivo del repo, el video o el debrief no existe para el jurado.**

si el brief del día dice otra cosa, el brief manda y esta hoja se corrige.

## 01 · systems design · 30 % · cierre 12:00 bog
se alimenta de: `DISENO.md` + diagrama de arquitectura.

**lo que miran a priori (romina, 10 oct 11:3x):** cuánto se piensa en **sistemas**: cómo escala, qué trade-offs se tomaron y cuál es el costo de cada uno. no basta un diagrama de lo que vamos a construir: tiene que verse por qué esta forma y no otra, qué pasa con 10× casos, 10× consultas o una caja que cambia, y dónde se rompe.

| criterio | un 4 se ve así | dónde vive | pregunta de control antes de entregar |
|---|---|---|---|
| entendimiento del problema | nombra supuestos, casos difíciles y lo que deja fuera, con razones | `DISENO.md` § 1–4 | ¿hay al menos un supuesto que, si es falso, nos rompe? ¿cada «fuera de alcance» dice por qué? ¿algo de esto no es repetir el brief? |
| arquitectura y trade-offs | cada decisión dice qué alternativa descartó y por qué | `DISENO.md` § 5–6 | ¿cada fila de decisiones tiene alternativa descartada y costo? ¿el diagrama muestra lo que de verdad corre? |
| plan para medir | casos de prueba y métricas concretas desde el diseño | `DISENO.md` § 7, `evals/` | ¿hay un set propio con casos fáciles, difíciles, borde y nuevos? ¿un comando que lo corre? ¿un umbral para decir «funciona»? |
| escalabilidad y cambio (lente de romina, no fila del portal) | dice cómo crece el costo con los casos, qué parte no gasta tokens, y cómo absorbe el incidente sin reescribirse | `DISENO.md` § 8–9 | ¿hay una frase con el costo por caso y cómo crece? ¿lo que aprendimos de la caja es dato (un modelo que se vuelve a investigar) y no reglas escritas en el código? ¿qué pasa si mañana la caja cambia una regla? |

## 02 · ejecución · 40 % · cierre 20:00 bog
se alimenta de: repo, entrypoint, video de 2 min, `spec.md` + `log.jsonl` (reto 2).

| criterio | un 4 se ve así | dónde vive | pregunta de control antes de entregar |
|---|---|---|---|
| resultado en el set oculto | resuelve la mayoría de casos, **incluidos los nuevos** | el entrypoint | ¿`smoke.sh` pasa en `main` y hay tag verde? ¿probamos con casos que no se parecen a los ejemplos del brief? ¿el costo por caso cabe en la reserva de us$ 5? ¿falla ruidoso (no vacío con código 0) si la llave o la caja fallan? |
| respuesta al incidente | detectan el cambio, se adaptan y lo explican | `incident.md`, `log.jsonl` | ¿dice a qué hora y con qué consulta se detectó? ¿qué cambió, con evidencia citada? ¿qué hizo el sistema solo y qué hicimos nosotros? ¿lo que no se separó está escrito como desconocido? |
| calidad del repo | corre siguiendo el README y el código se explica solo | `README.md` | ¿una persona sin contexto lo corre copiando los comandos del README? ¿están requisitos, `OPENROUTER_API_KEY`, comando exacto, ejemplo de entrada y salida, cómo correr las pruebas, costo por caso, límites? ¿no hay llaves, uuid personales ni datos de personas? |

**reto 2, además:** `spec.md` separa **observado** (con la consulta que lo prueba y el contraejemplo que lo refutaría) / **inferido** / **desconocido**. cada afirmación cita el log. la confianza dice lo que no significa.

## 03 · demo day · 15 % · 21:15–22:15 bog
se alimenta de: pitch y material opcional. también el video de 2 min.

| criterio | un 4 se ve así | pregunta de control |
|---|---|---|
| claridad | en minutos queda claro el problema, la solución y la evidencia | ¿se entiende en la primera frase qué servicio clonamos, cómo, y con qué evidencia? |
| evidencia | resultados reales, **incluido lo que no salió** | ¿mostramos una corrida de verdad, con números? ¿hay al menos una falla nuestra contada con su causa? |

## 04 · profundidad técnica · 15 % · debrief 20:00–21:00 bog
se alimenta de: debrief individual de 10 min (romina, oral). ahí el juez corre el set oculto con nuestro entrypoint.

| criterio | un 4 se ve así | qué le dejamos preparado a romina |
|---|---|---|
| explicación de decisiones | explica fallas, límites y qué haría después | una hoja `debrief.md`: cómo funciona en cinco frases, tres decisiones con su alternativa, límites, qué haríamos después |
| lectura de resultados | **explica cada falla con una causa concreta** | por categoría de las métricas públicas: qué falla y por qué (mecanismo, no «el modelo se equivocó») |

## transversal (vale para todas)

- **el repo es legible para un modelo, todo el día** (romina, 10 oct). quien agrega un archivo o carpeta en la raíz lo describe en `llms.txt`; quien escribe en `spec.md` cita ids que existen en el log. `bash herramientas/revisar_llms.sh` lo comprueba y debe salir en 0 antes de cada push que toque la raíz, la spec o `llms.txt`.

0. **el incidente llega entre las 15:00 y las 16:00 bog (el portal dice 15:30) y cambia el entorno.** nada se sobreajusta a lo que la caja hace en la mañana: lo aprendido vive como datos que se vuelven a investigar, no como reglas en el código. la pregunta de cada entrega es «¿esto sobrevive a que la caja cambie?».

1. **lo que no está escrito no existe.** decisión, supuesto, falla o hallazgo → a un archivo. lo que no sabemos, como «no sé»; lo inferido, como inferencia.
2. **mostrar lo que no salió suma.** un límite escrito con su causa vale más que esconderlo.
3. **casos nuevos, no los del brief.** generalizar el mecanismo; no calcar los ejemplos.
4. **costo por caso medido**, no estimado, antes del cierre de ejecución.
5. **la tarea es la del brief.** el repo del jurado habla del reto (clonar el servicio), no de pasaelfiltro ni de sus usuarios: eso es contexto de la casa, no de la entrega. (corrección de romina, 10 oct: venía arrastrado del ensayo, donde la caja era un ats.)
6. **el repo muestra cómo trabajamos**, no solo qué ganamos: la casa (romina y las plumas), la genealogía en los merge commits, las cicatrices como reglas, el desacuerdo entre modelos como señal. y **corre**: sin eso, lo demás no se sostiene.
7. **sin secretos ni datos personales en el repo del jurado**: ni llaves, ni el uuid de romina, ni datos de usuarios de pef que no sean públicos.
