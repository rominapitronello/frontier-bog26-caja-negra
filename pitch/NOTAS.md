# Notas de presentadora — «La caja la pensó alguien»

**Duración sugerida:** 3 minutos; cada lámina sostiene una conclusión que permite cortar el relato. No leer el texto de pantalla: esta es la voz detrás de él.

### 01 · Clonamos un banco sin ver su código
«Nos dieron un servicio sintético de mensajes, cuentas con estado y errores raros. No podíamos mirar su código: solo hacer pedidos y medir sus respuestas. En nuestra segunda validación conseguimos 99 de 100; la última nota todavía la decide el jurado».

### 02 · Cada pedido salió con una hipótesis
«En vez de probar al azar, cada pedido tenía una pregunta y quedó en un log. Ese registro sostiene la spec; cada afirmación tiene una línea que la prueba. El control bancario era ISO 7064: dos modelos lo descifraron sin consultar el servicio para buscar la fórmula».

### 03 · Dos diseños a ciegas
«Pedimos a dos modelos que diseñaran una caja parecida sin verse. Claude apuntó contra el programador que corrige y Sol contra el agente que investiga. Un diseño por linaje no demuestra quién escribió el banco; nos dio una hipótesis que podíamos poner a prueba».

### 04 · Los postes escritos a las 13:27:03
«Dejamos una predicción en un commit, pero también lo importante: las reglas para decidir si habíamos acertado o fallado. Ahí están las dos formas de fallar. La tabla existía antes del incidente anunciado para las 15:30».

### 05 · El veredicto es acierto parcial
«El servicio bajó su límite de cien mil a cincuenta mil, cambió el status y contador del bloqueo, y convirtió el saldo en texto decimal. Un clon fiel a la mañana iba a fallar. Predijimos bien el adversario dominante, no los mecanismos concretos: por eso es acierto parcial».

### 06 · Evidencia, no coronación
«Partimos con 83 de 100 frente a la versión uno y luego tuvimos 99 frente a la versión dos. En difíciles fueron 19 de 20, mientras la organización había informado un 39% promedio entre los quince equipos con resultados. Son mediciones distintas; no las uso para adjudicar causalidad. La nota final no había llegado».

### 07 · Lo que no salió
«Nuestro propio código repitió 398 pedidos en un bucle. Quedó en el log y lo corregimos. Encontramos una divergencia con pıng, la i turca sin punto, pero no sabemos si era el test oculto que faltó. Y el micrófono de la MacBook de 2012 murió: el video salió mudo, con subtítulos».

### 08 · La casa
«Fable escribió el guion, Sol hizo las gráficas, Claude afinó el copy, y yo puse la pregunta y el montaje. Cada quien firmó su parte. El repositorio es público: la predicción tiene hora, y el método y las fallas se pueden revisar».

## Cortes posibles
Con tiempo escaso: mostrar 01 → 02 → 04 → 05 → 06 → 07 → 08 (saltar 03; la apuesta sigue explicada en 04). Si cortan antes, cerrar con una invitación verbal al repo sin declarar nota final.

## Reglas de lectura
- «99/100»: validación 2, 16:21 bog, gemelo v15 contra original v2, **no evaluación definitiva**.
- «83/100»: validación 1, 11:06 bog, contra v1. **Son versiones distintas**, no se atribuye toda la diferencia a una intervención aislada.
- «39%»: promedio de pruebas difíciles entre los 15 equipos con resultados, dato comunicado por la organización a las 14:4x bog; otros equipos no entran a este promedio.
- «acierto parcial» significa exactamente eso. `pıng` fue diferencia real, **no identificación probada** de test oculto.
- «nota final null»: pendiente hasta que conste el resultado posterior a las 20:00.
- Sin narración grabada en el video; la voz es la de Romina presentando en vivo.

**Atajos:** derecha / espacio / PageDown avanza; izquierda / PageUp retrocede; Home/End saltan; F pantalla completa; N muestra notas.
