# sol-06 · pensar como quien escribió la caja

**Pluma:** Sol, familia GPT. **Encargo:** juicio de autor, dos entregas; sin consultar el servicio. **Base leída:** `spec.md`, `AGENTS.md` y `LINAJES.md` en [`b3aaa54`](https://github.com/rominapitronello/frontier-bog26-caja-negra/tree/b3aaa54dd87c9a34c1190ce33046c05adc7c93cb). También `ESTADO.md`, `RUBRICA.md`, el brief, el README del material, `incident.md` y el calculador local, para respetar el contrato. No leí el código del gemelo ni el log crudo. Los ids de evidencia que siguen son las referencias que ofrece la spec.

**Mi apuesta:** el autor separó validación, búsqueda y negocio, y conservó un catálogo de errores más grande que la implementación final. Los huecos parecen más compatibles con reglas reservadas o retiradas que con ocho comportamientos todavía ocultos. Para el incidente, yo cambiaría primero qué recuerda una operación: eso rompe a un clon correcto de la mañana sin cambiar la gramática.

Todo lo que atribuyo al autor es **inferencia**, no observación ni una modificación propuesta para producción. La numeración no identifica por sí sola el significado de un código: podría haber asignaciones arbitrarias. El mapa siguiente es mi reconstrucción preferida, con confianza baja en la correspondencia **código → regla**. No incorporar estos errores al gemelo ni a la tabla de confirmados sin evidencia nueva. El orden de cambios de la segunda entrega tampoco es una probabilidad medida.

## 1 · qué habría habido en los huecos

### La mesa de trabajo del autor

Si yo hubiera escrito esta caja, habría hecho primero una tabla de errores por capa y después simplificado el banco:

| Familia | Lo que conserva la spec | Qué me sugiere como autor |
|---|---|---|
| E1xx | cuerpo, JSON y segmentos | problemas del sobre y del parser |
| E2xx | formato y valor del control | integridad del mensaje |
| E3xx | comando, aridad, monto, origen = destino | argumentos que no llegan a ejecutar negocio |
| E401–E402 | cuenta y operación inexistentes, ambos HTTP 404 | búsqueda de recursos; el número no es el status HTTP |
| E5xx | límite, saldo, bloqueo, confirmación, detenido | precondiciones y estados del banco |

`E404` es además el código de ruta desconocida. Esa coincidencia con HTTP hace tentador leer `E403` como «prohibido», pero no lo demuestra. Mi reconstrucción de E501–E505 sigue el orden ALTA → DEPOSITO → TRANSFER; E508–E509 siguen a las dos restricciones de TRANSFER y preceden al bloqueo. Es una economía de diseño plausible, no una recuperación del código fuente.

### Ocho huecos, una hipótesis principal por hueco

Los `m` son cadenas exactas para el cuerpo `{"m":"…"}` de `POST /msg`. Cada secuencia empieza tras un `POST /__reset` autorizado. El reset **no** es un mensaje con control. Las preparaciones completas están debajo de la tabla. Los textos y status de los errores desconocidos son **null**: no invento una respuesta literal que no hemos visto.

| Hueco | Regla que más probablemente habría escrito y luego reservado o retirado | `m` candidato y precondición | Lo que permite decir la spec de la mañana |
|---|---|---|---|
| **E501** | **Titular inválido:** rechazar nombres sin contenido tras recortar espacios. Una validación semántica del alta, distinta del segmento vacío. | `ALTA; ;85`, desde estado vacío. El segundo segmento es **un espacio ASCII U+0020**, no vacío. | AL-02 acepta un espacio (717). Esta forma de E501 estaría **retirada**: hoy el alta crea AC-0001. Un nombre literalmente vacío cae antes en E104 y no sirve de test de E501. |
| **E502** | **Titular duplicado:** una cuenta por nombre. Después el autor permitió varias cuentas del mismo titular para introducir la excepción al límite. | `ALTA;Lucia;82`, después de otro `ALTA;Lucia;82` exitoso. | AL-02 acepta repetidos; TR-06 usa dos cuentas de «Lucia» (813, 817). La prohibición general está **retirada**, si existió. Hoy el segundo alta crea AC-0002. |
| **E503** | **Cupo de cuentas por token.** Es una restricción fácil de dejar en el catálogo y omitir del banco mínimo. | `ALTA;Cuenta11;46`, después de diez altas exitosas Cuenta01…Cuenta10, **bajo la hipótesis adicional cupo = 10**. | AL-04 solo deja abierto el crecimiento del id después de 9999; no prueba un cupo ni su ausencia. **Existencia y umbral desconocidos.** El 10 es un valor de trabajo para concretar el test, no algo deducido del código E503. Si el cupo fuera K, el disparador sería el alta K+1. |
| **E504** | **Monto mínimo de negocio**, mayor que un peso, separado de la sintaxis positiva de E303. | `DEPOSITO;AC-0001;1;28`, después de crear AC-0001. Un peso discrimina cualquier mínimo entero mayor que uno. | DE-02 permite 1; RI-11 registra que depositar 1 desbloquea (885–886, 926–928). Un mínimo universal mayor que 1 está **retirado**, si existió. |
| **E505** | **Tope de depósito por operación:** la primera versión habría aplicado el mismo techo de 100.000 a las entradas y a las salidas; después dejó ilimitados los depósitos para facilitar estados de prueba. | `DEPOSITO;AC-0001;100001;3`, después de crear AC-0001; techo hipotético 100.000. | DE-03 acepta 999.999.999 y 9.999.999.999 (97, 270). Este techo estaría **retirado**. La igualdad de su valor con el límite de TRANSFER es una conjetura de diseño. |
| **E508** | **Operación ya anulada:** originalmente un error de negocio; luego se volvió una respuesta idempotente de aplicación, HTTP 200 y `ok:false`. Es el hueco con el vestigio más visible. | `ANULA;OP-0001;72`, después de crear OP-0001 con un depósito y anularla una vez. | AN-04 da exactamente `{"ok":false,"motivo":"ya anulada"}` (15, 232). La condición sigue existiendo; su presentación como **E508** estaría retirada. La asociación al número sigue siendo inferencia. |
| **E509** | **Anulación que dejaría saldo negativo:** guardar invariantes contables en el reverso. El autor pudo quitarla para hacer del saldo negativo una rareza deliberada del reto. | `ANULA;OP-0001;72`, después de depositar 100 en AC-0001 y transferir esos 100 a AC-0002. | AN-02 permite el reverso del depósito aun quedando negativo (116–117); AN-03 permite lo mismo en transferencias (228–230). La prohibición general estaría **retirada**, si existió. |
| **E403** | **Recurso ajeno / acceso prohibido:** un banco anterior con almacén compartido distinguía «no existe» de «existe, pertenece a otro cliente». Al pasar a estado por token quedó inalcanzable. | Forma léxica candidata: `CONSULTA;AC-0001;14`, **solo si** AC-0001 existiese en un almacén común y fuese ajena al token autorizado. **Disparador construible con la spec actual: null.** | ME-01 y el material separan el estado por token; CO-02 da E401 si el id no existe en ese estado. No hay comando conocido para crear la relación «recurso ajeno». Un token inválido da E001 antes de leer `m`. La hipótesis tiene **confianza muy baja**: el bloque E4xx también podría reservar otro recurso inexistente. |

No pondría ocho comandos inventados detrás de estos huecos. La evidencia contra reglas universales retiradas ya está en la spec; un número libre no la revoca. E503 es el candidato principal de esta tabla que podría seguir vivo sin contradecir las filas citadas. E403 exige una estructura de autorización que el contrato conocido no ofrece. E508 y E509 son las mejores pistas de una decisión anterior del autor porque la anulación actual conserva precisamente los comportamientos que un banco convencional rechazaría.

### Preparaciones exactas

**E501:** solo el mensaje de la tabla. No sustituir el espacio por un segmento vacío.

**E502:** dos mensajes iguales; el segundo es el candidato.

```json
{"m":"ALTA;Lucia;82"}
{"m":"ALTA;Lucia;82"}
```

**E503:** once altas; el último mensaje discrimina exclusivamente el cupo hipotético de diez. No presupongo que la onceava alta falle hoy.

```json
{"m":"ALTA;Cuenta01;76"}
{"m":"ALTA;Cuenta02;73"}
{"m":"ALTA;Cuenta03;70"}
{"m":"ALTA;Cuenta04;67"}
{"m":"ALTA;Cuenta05;64"}
{"m":"ALTA;Cuenta06;61"}
{"m":"ALTA;Cuenta07;58"}
{"m":"ALTA;Cuenta08;55"}
{"m":"ALTA;Cuenta09;52"}
{"m":"ALTA;Cuenta10;49"}
{"m":"ALTA;Cuenta11;46"}
```

**E504 / E505:** secuencias independientes, cada una tras reset. Primero `ALTA;Lucia;82`; después el depósito correspondiente de la tabla. No acumular ambos depósitos para probar un tope de saldo por accidente.

**E508:** el cuarto mensaje es el candidato; ANULA no consume otro id de operación (ME-04).

```json
{"m":"ALTA;Lucia;82"}
{"m":"DEPOSITO;AC-0001;100;82"}
{"m":"ANULA;OP-0001;72"}
{"m":"ANULA;OP-0001;72"}
```

**E509:** cinco mensajes, con titulares distintos y monto bajo el límite; no hay rechazos que pudieran bloquear la cuenta. OP-0001 es el depósito, OP-0002 la transferencia.

```json
{"m":"ALTA;Lucia;82"}
{"m":"ALTA;Mateo;3"}
{"m":"DEPOSITO;AC-0001;100;82"}
{"m":"TRANSFER;AC-0001;AC-0002;100;24"}
{"m":"ANULA;OP-0001;72"}
```

En la mañana el último mensaje tiene éxito y deja saldos **−100 / 100**. Bajo E509 rechazaría sin modificar saldos ni marcar la operación anulada: quedarían **0 / 100**. Así se distingue un rechazo de una respuesta cuyo texto cambió pero cuyos efectos siguen iguales.

**E403:** no hay preparación conocida con un solo token. El texto de CONSULTA está calculado, pero no afirmar que el texto solo crea el permiso que le falta al estado. No propongo consultar cuentas ni tokens de otro equipo.

### Control calculado, no adivinado

Se aplicó literalmente spec § 2: dígitos ASCII tal cual; letras ASCII A=1…Z=26, sin distinguir caja; los demás caracteres no aportan; concatenación decimal N; `c = 98 - (100*N % 97)`, decimal sin relleno. Por ejemplo:

| Cuerpo sin control | N mod 97 | 100·N mod 97 | Control | `m` completo |
|---|---:|---:|---:|---|
| `ALTA; ` | 69 | 13 | 85 | `ALTA; ;85` |
| `ALTA;Lucia` | 70 | 16 | 82 | `ALTA;Lucia;82` |
| `ALTA;Cuenta11` | 82 | 52 | 46 | `ALTA;Cuenta11;46` |
| `DEPOSITO;AC-0001;1` | 88 | 70 | 28 | `DEPOSITO;AC-0001;1;28` |
| `DEPOSITO;AC-0001;100001` | 64 | 95 | 3 | `DEPOSITO;AC-0001;100001;3` |
| `ANULA;OP-0001` | 41 | 26 | 72 | `ANULA;OP-0001;72` |
| `CONSULTA;AC-0001` | 28 | 84 | 14 | `CONSULTA;AC-0001;14` |

`3` es correcto; `03` fallaría E202 aunque esté bien formado (IN-07). Se contrastaron fuera de línea los controles del documento con `herramientas/control.py` y con una segunda implementación que construye N completo y hace la operación modular directamente. Esto verifica la aritmética; **no verifica la existencia de ningún error**.

## 2 · los cinco cambios que yo haría para el incidente

Orden de **plausibilidad de autor**, de mayor a menor, combinando continuidad con las reglas existentes, costo de implementarlo y cuántas secuencias correctas de la mañana dejarían de serlo. Cada fila es un cambio independiente, sobre la versión de la mañana; los ejemplos **no** suponen que se aplicaron los cinco a la vez. Los números nuevos concretan el diseño que yo elegiría: no son predicciones observadas. Todos los ejemplos entran en los tests de hasta doce mensajes del material.

### 1. Mantener 100.000, pero volverlo acumulado por origen

**Lo que haría:** además del límite individual existente, sumar las transferencias exitosas a titulares distintos desde cada cuenta. Rechazar si `salidas_acumuladas + monto > 100000`, antes del saldo y después del límite individual; asignaría E508 a esa restricción nueva. Mismo titular sigue exento. Solo `/__reset` borra el acumulador; ANULA devuelve dinero pero no cupo. Los rechazos por este nuevo límite alimentarían la racha de bloqueo como E506/E507.

**Por qué lo elegiría:** cierra exactamente el fraccionamiento de RI-04; el estado ya guarda cuentas y operaciones, y basta un contador por cuenta. El clon que aprendió perfectamente «por operación, no acumulado» (TR-06, 106–108) es el que se equivoca. Reutilizar E506 también sería plausible: ver el mismo código no bastaría para concluir que solo cambió el número.

**Secuencia que rompe:** altas Lucia/Mateo, `DEPOSITO;AC-0001;200000;27`, y dos veces `TRANSFER;AC-0001;AC-0002;60000;32`. En la mañana ambas tienen éxito, OP-0002 y OP-0003, saldos **80.000 / 120.000**. Con mi cambio falla la segunda, sin consumir OP-0003, saldos **140.000 / 60.000**. Una transferencia aislada no delata el cambio. Hay que aprender también si el cupo es por cuenta o titular y si el reverso lo repone; no inferirlo del nombre «diario».

### 2. Rechazar ANULA cuando el reverso dejaría algún saldo negativo

**Lo que haría:** calcular todos los saldos resultantes antes de tocar el estado; si alguno sería negativo, respondería E509, HTTP 422, sin anular ni mutar nada. Mantendría la respuesta idempotente actual si la operación ya estaba anulada.

**Por qué lo elegiría:** es un parche pequeño a la rareza más bancaria del servicio (RI-03). Cambia la conservación de estado en todas las secuencias que gastaron un depósito o volvieron a gastar una transferencia. A diferencia de corregir una errata, la primera diferencia contamina varias respuestas posteriores.

**Secuencia que rompe:** la preparación E509 de arriba. El clon de la mañana anula y crea −100; mi versión rechaza y deja 0. AN-02/AN-03 son las reglas antiguas que caducarían. También aplicaría a revertir una transferencia cuyo destino ya gastó el dinero; no basta comprobar depósitos.

### 3. Hacer que depositar dinero ya no quite el bloqueo

**Lo que haría:** retirar exclusivamente el efecto de DEPOSITO sobre la racha/bloqueo. El depósito seguiría sumando dinero y creando operación. Se mantienen el umbral de tres, el ámbito por cuenta, los errores que suman y las demás reglas de TR-08. Una cuenta ya bloqueada solo volvería a estar disponible tras reset, dentro de los comandos actuales.

**Por qué lo elegiría:** una edición mínima elimina el desbloqueo por un peso de RI-11. La misma respuesta de depósito seguiría siendo correcta: falla la transferencia posterior. Eso castiga copiar respuestas sin reconstruir las transiciones, y también rompe a quien reconstruyó correctamente la transición antigua.

**Secuencia que rompe:** altas Lucia/Mateo; tres veces `TRANSFER;AC-0001;AC-0002;1;41` con saldo cero; `DEPOSITO;AC-0001;1;28`; otra vez `TRANSFER;AC-0001;AC-0002;1;41`. En la mañana: tres E507, depósito OP-0001, transferencia exitosa OP-0002, saldos **0 / 1**. Con mi cambio: mismo depósito, después E510, saldos **1 / 0**. Son siete mensajes; no hace falta esperar un reloj.

### 4. Cobrar una comisión fija de un peso en TRANSFER entre titulares distintos

**Lo que haría:** conservar el monto acreditado al destino, pero exigir y debitar `monto + 1` al origen. Mismo titular sin comisión. Mantendría E507 para fondos insuficientes y la racha correspondiente. Guardaría la comisión en la operación: un reverso exitoso devuelve al origen monto + comisión y resta al destino solo el monto. El límite individual seguiría midiendo el monto transferido.

**Por qué lo elegiría:** no exige otro comando ni cambia el sobre HTTP; consulta y anulación ya dan observabilidad a la nueva contabilidad. Rompe saldos exactos, transferencias que vacían la cuenta y reversos. Lo pongo por debajo de las correcciones anteriores porque inventa una regla sin un vestigio tan claro en la spec.

**Secuencia que rompe:** altas Lucia/Mateo; `DEPOSITO;AC-0001;101;79`; `TRANSFER;AC-0001;AC-0002;100;24`; `CONSULTA;AC-0001;14`; `CONSULTA;AC-0002;11`. En la mañana ambas consultas muestran **1 / 100**; con comisión **0 / 100**. La transferencia responde el mismo éxito. Con depósito de 100, la versión nueva daría E507 donde antes transfería por el saldo exacto.

### 5. Cambiar la lectura de letras del control: A=10…Z=35

**Lo que haría:** sustituir solo la tabla A=1…Z=26 por A=10…Z=35; mantener MOD 97, lectura de dígitos, descarte de puntuación, comparación textual y la excepción PING. El autor puede presentarlo como una migración de integridad bancaria. Es una variante concreta; no estoy afirmando que spec § 2 deba «corregirse» hoy.

**Por qué lo elegiría:** una tabla nueva invalida los mensajes bancarios correctamente construidos con la versión anterior; PING y `/health` siguen pasando. El clon puede parecer vivo y estar roto en casi todo el negocio. Lo pongo quinto porque el fallo masivo E202 se reconoce y adapta rápido, y el autor tendría que generar controles nuevos para sus casos de evaluación. Los cambios de estado anteriores hacen trabajar más al equipo.

**Par exacto que rompe:** `ALTA;Lucia;82` pasa en la mañana y daría E202 con la tabla nueva; `ALTA;Lucia;42` daría E202 en la mañana y crearía la cuenta con la tabla nueva. Para el control nuevo, N mod 97 = **51**, 100·N mod 97 = **56**, control = **42**. **42 se calculó bajo el cambio hipotético, no bajo la spec vigente.** `PING;64` seguiría respondiendo pong en ambos modelos.

Mi elección como autor sería primero el acumulador, y después la anulación: aprovechan reglas que el equipo ya cree haber entendido. Una mera sustitución del valor del límite cuesta menos al autor, pero también menos al equipo que hizo su modelo configurable. Una confirmación en dos pasos o sesiones nuevas costaría más construir y revalidar sin que se escape el incidente de la ventana disponible. Esta preferencia no depende de que el autor sea GPT o Claude: LINAJES advierte que una muestra y rasgos pedidos no identifican un linaje.

## Entrega, límites y rúbrica

| Control relevante de RUBRICA.md | Respuesta concreta |
|---|---|
| Separar observado, inferido y desconocido | La evidencia indirecta está en las filas citadas de la spec; la tabla de huecos y el ranking son inferencias; status/texto desconocidos, umbral de E503 y preparación de E403 quedan declarados. |
| Casos nuevos y comportamiento con memoria | Preparaciones de ocho huecos y secuencias con primera divergencia, ids y saldos para los cuatro cambios de negocio; dos controles para la migración de integridad. |
| Respuesta al incidente con evidencia | **No se detectó ni se observó un incidente en este encargo.** El catálogo es previo; quien lidera debe contrastarlo con el servicio y registrar cualquier cambio real en `incident.md`. |
| Que la entrega sobreviva a un cambio | Cada hipótesis describe su mecanismo y la condición que la distingue de la mañana; no se codificó ninguna como si fuese verdadera. |
| Corrida real, costos y límites | Cálculo de controles fuera de línea, por dos métodos; **0 consultas al original, 0 al gemelo, 0 validaciones del portal, 0 llamadas pagadas a modelos** dentro del encargo. No hubo ejecución del set ni de smoke: el cambio es documental y el entrypoint no se modificó. |
| Genealogía y continuidad | Autoría Sol; informe en rama con PR; integración por quien lidera, con merge commit según AGENTS.md. `ESTADO.md` registra el relevo. |

**Siguiente paso de quien lidera:** usar este informe como catálogo de decisiones del autor, no como lista de descubrimientos. E503 necesita un umbral medido; E403 no tiene un disparador construible con el contrato conocido. Si el incidente cambia estado, las primeras apuestas son acumulación, reverso y desbloqueo. No hace falta una acción de Romina para terminar este encargo.
