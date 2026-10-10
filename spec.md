# spec.md · el servicio, para reimplementarlo sin tocarlo

> estructura del material (`material/README.md`). cada fila: `ID | Comportamiento | Evidencia | Confianza`. la evidencia son `id` de `experimentos.jsonl`; el ejemplo *k* del material es la línea *k*+1 del log (los 20 se reprodujeron idénticos, 2–21). **confirmado**: probado y se repite · **probable**: visto una vez o inferido · **supuesto**: no probado, es lo que hace el gemelo por defecto. una afirmación falsa resta: ante la duda, se baja la confianza.
>
> versión: 10 oct 2026, 10:5x bog, sobre 928 líneas del log (las 289–686 son una repetición por un error nuestro, sin valor de evidencia). **v2 corrige el orden entre límite y saldo de la v1**, que estaba mal: lo detectó el centinela (737) y lo explican TR-06 a TR-08. el gemelo (`gemelo/servidor.py`, con lo tabular en `gemelo/modelo.json`) implementa esta spec y reproduce todas las secuencias del log (`bash smoke.sh`).

**el camino de un pedido, en orden** (cada paso puede cortar con un error; § 5 tiene la tabla):

```
1. ruta exacta (sin query string): POST /msg · GET /health · POST /__reset      → si no: 404 E404
2. Authorization == "Bearer <token del equipo>"                                  → si no: 401 E001
3. /health → 200 {"ok":true} · /__reset → estado inicial, 200 {"ok":true}
4. /msg: si el token está detenido (HALT)                                       → 503 E599
5. cuerpo > 8192 bytes                                                           → 413 E101
6. el cuerpo no es json                                                          → 400 E100
7. no es un objeto con "m" de tipo string                                        → 400 E102
8. segs = m.split(";")  (sin recortar espacios); menos de 2 segmentos            → 400 E103
9. algún segmento vacío                                                          → 400 E104
10. cmd = segs[0] en mayúsculas. si cmd != PING: control = segs[-1]
      no es 1 o 2 dígitos ascii                                                  → 400 E201
      distinto de control(";".join(segs[:-1])) como texto                       → 400 E202
11. cmd no es PING, ALTA, CONSULTA, DEPOSITO, TRANSFER, ANULA ni HALT            → 400 E301 (+ sugerencia)
12. número de argumentos (segs[1:-1]) distinto de la aridad del comando          → 400 E302
13. el comando: sus propias reglas y su respuesta (§ 3)
```

## 1 · entrada
rutas, métodos, autenticación, forma del cuerpo y límites.

| ID | Comportamiento | Evidencia | Confianza |
|---|---|---|---|
| EN-01 | existen tres rutas: `POST /msg`, `GET /health` y `POST /__reset`. cualquier otra ruta o método responde **404** `{"error":"E404","mensaje":"ruta desconocida"}`: `POST /health`, `GET /msg`, `PUT /msg`, `DELETE /msg`, `OPTIONS /msg`, `GET /`, `GET /no-existe`, `POST /no-existe` | 52–58, 708, 725 | confirmado |
| EN-02 | la ruta se evalúa **antes** que el token: una ruta inexistente sin token da 404, no 401 | 59, 725 | confirmado |
| EN-03 | la ruta se compara exacta: `/msg/` (barra final) y `/MSG` (mayúsculas) dan 404 | 60, 61 | probable |
| EN-04 | la query string se ignora: `POST /msg?x=1` responde como `POST /msg` | 62 | probable |
| EN-05 | autenticación: el header `Authorization` tiene que ser exactamente `Bearer <token del equipo>`. sin header, otro token, `bearer` en minúsculas, el token sin `Bearer ` o `Bearer ` vacío dan **401** `{"error":"E001","mensaje":"no autorizado"}` | 63–67, 712, 724 | confirmado |
| EN-06 | `GET /health` con token: **200** `{"ok":true}`, también con el servicio detenido. sin token o con otro: 401 `E001` | 49, 700, 702; 50, 51 | confirmado |
| EN-07 | `POST /__reset` con token: **200** `{"ok":true}` y el token vuelve al estado inicial (§ 4). sin token o con otro token: 401 `E001` | 1, 22, 48, 143, 701–704, 727–728; 706, 707 | confirmado |
| EN-08 | el cuerpo de `/msg` se lee como json sin mirar el `Content-Type` (`text/plain` o sin header funcionan igual) | 77, 78 | confirmado |
| EN-09 | cuerpo que no es json (texto, vacío) → **400** `{"error":"E100","mensaje":"json inválido"}` | 68, 69 | confirmado |
| EN-10 | json que no es un objeto con la clave `m` de tipo string → **400** `{"error":"E102","mensaje":"falta m"}`: `{}`, un array, `m` número, `m` null, `m` array, la clave `M` en mayúscula, un string json | 70–73, 76, 79, 80 | confirmado |
| EN-11 | claves extra en el objeto se ignoran | 75 | probable |
| EN-12 | tope del cuerpo: **8.192 bytes pasan, 8.193 dan 413** `{"error":"E101","mensaje":"cuerpo demasiado grande"}`. se mira después del token (sin token da 401) y antes de parsear el json (un cuerpo grande que no es json da 413) | 710, 711; 274, 275, 277–288; 712; 713 | confirmado |
| EN-13 | el mensaje `m` no se recorta: un espacio delante cambia el comando (`E301`) y un espacio o salto de línea al final dejan el control mal formado (`E201`) | 252, 253, 254 | confirmado |
| EN-14 | la respuesta trae un header `X-Req` que cuenta los pedidos a `/msg` del token (también los que dan error 400) y **no** se reinicia con el reset. los headers no se comparan en la evaluación; el gemelo lo imita por proceso | 2–21, 62, 68 | probable |

## 2 · integridad
cómo valida el servicio que un mensaje está bien formado (el dígito de control).

el mensaje son **segmentos separados por `;`**; el primero es el comando y **el último es un dígito de control** de los mensajes bancarios: **ISO 7064 MOD 97-10, el mismo del iban**.

```
N        = el mensaje sin su último segmento, leído como número decimal:
           cada dígito ascii vale lo que es; cada letra ascii, su posición en el alfabeto (A=1 … Z=26,
           sin importar mayúsculas); cualquier otro carácter (; - espacio . tab é ñ emoji) no aporta nada
control  = 98 − (100 · N mod 97)          → un número de 2 a 98
válido   ⇔ el último segmento es ese número escrito en decimal, sin ceros a la izquierda
ejemplo  ALTA;Lucia → A L T A L U C I A → 1 12 20 1 12 21 3 9 1 → N = 1122011221391
         100·N mod 97 = 16 → control = 82 → "ALTA;Lucia;82" (ejemplo 3: 201) y "ALTA;Lucia;83" da E202 (ejemplo 2)
         PING → 16 9 14 7 → N = 169147 → 64            CONSULTA;AC-0001 → 14
```

`herramientas/control.py` lo calcula (`python3 herramientas/control.py 'ALTA;Lucia'` → `82`).

| ID | Comportamiento | Evidencia | Confianza |
|---|---|---|---|
| IN-01 | un mensaje con menos de dos segmentos (sin ningún `;`, o `m` vacío) → **400** `{"error":"E103","mensaje":"falta control"}`, sea cual sea el comando | 41, 74, 249, 250, 251 | confirmado |
| IN-02 | un segmento vacío en cualquier posición (`CONSULTA;;99`, `;PING;64`, `PING;;64`, control vacío `CONSULTA;AC-0001;`) → **400** `{"error":"E104","mensaje":"segmento vacío"}` | 36, 210, 211, 212 | confirmado |
| IN-03 | el control tiene que ser **1 o 2 dígitos ascii**; si no → **400** `{"error":"E201","mensaje":"control mal formado"}`: `5X`, `XX`, `014`, `111`, `-83`, `+14`, ` 14`, `14 `, `14\n`, `14.0` | 18, 28, 31–35, 37, 213, 214, 253, 254 | confirmado |
| IN-04 | el control bien formado que no coincide → **400** `{"error":"E202","mensaje":"control inválido"}` | 3, 24, 26, 29, 42, 43, 46 | confirmado |
| IN-05 | la fórmula de arriba: calza los 16 controles válidos de los ejemplos, y mensajes nuevos calculados con ella son aceptados | 2–21; 23, 25, 27, 30, 44, 45, 47, 82–87, 716, 717 | confirmado |
| IN-06 | el rango es **2 a 98**, no 0 a 96: cuando 100·N mod 97 es 1, el control es `97` (y `00` da E202); cuando es 0, el control es `98` (y `1` da E202) | 24–27 | confirmado |
| IN-07 | se compara **como texto**: para un control de una cifra, `2` vale y `02` da E202 (bien formado pero inválido) | 29, 30; 5 (`ALTA;Mateo;3`) | confirmado |
| IN-08 | las letras cuentan sin importar mayúsculas: `CONSULTa;AC-0001;14` y `CONSULTA;ac-0001;14` pasan el control | 12, 38 | confirmado |
| IN-09 | los caracteres que no son letra ni dígito ascii no aportan a N: espacio, `é`, `ñ`, tabulación, emoji, punto, guion y `;` | 44, 45, 47, 264, 265, 716 | confirmado |
| IN-10 | **`PING` no valida el control**: `PING;65` y `PING;XX` responden pong. sí valida la aridad (§ 3) | 39, 40, 714 | confirmado |
| IN-11 | el control se valida **antes** que el comando y la aridad: un comando desconocido o con aridad mala y control malo da el error de control (E201 o E202), no E301 ni E302 | 42, 43, 213, 214 | confirmado |
| IN-12 | mensajes largos también pasan el control (300 y 5.000 caracteres): N se reduce módulo 97 dígito a dígito | 262, 263 | probable |

## 3 · comandos
un bloque por comando: argumentos, efecto y respuesta. el comando no distingue mayúsculas (`CONSULTa`, `ping`, `alta`); los ids de cuenta y de operación sí. la **aridad** es el número de segmentos entre el comando y el control; si no calza → **400** `{"error":"E302","mensaje":"aridad inválida"}`.

| ID | Comportamiento | Evidencia | Confianza |
|---|---|---|---|
| CM-01 | el nombre del comando no distingue mayúsculas | 12, 133, 244 | confirmado |
| CM-02 | aridades: `PING` 0, `ALTA` 1, `CONSULTA` 1, `DEPOSITO` 2, `TRANSFER` 3, `ANULA` 1, `HALT` 1. cualquier otra cantidad → E302 | 21, 88, 89, 90, 99, 118, 137, 215, 217, 222, 714, 718 | confirmado |

### PING
| ID | Comportamiento | Evidencia | Confianza |
|---|---|---|---|
| PI-01 | `PING;<control>` → **200** `{"pong":true}`, sin estado y sin validar el control | 2, 39, 40, 138, 144, 728 | confirmado |
| PI-02 | `PING` con argumentos (`PING;a;b;64`) → E302 | 714 | probable |

### ALTA;nombre
| ID | Comportamiento | Evidencia | Confianza |
|---|---|---|---|
| AL-01 | crea una cuenta con saldo 0 → **201** `{"cuentaId":"AC-0001"}`; los ids son `AC-` + 4 dígitos, correlativos desde `AC-0001` tras cada reset | 4, 5, 6, 23, 82–87 | confirmado |
| AL-02 | el nombre no se valida: cualquier segmento no vacío sirve, incluidos repetidos, solo dígitos, una letra, guion, espacio, un espacio solo, tildes, `ñ`, tabulación, emoji y 5.000 caracteres. no aparece en ninguna respuesta, **pero se guarda: decide si una transferencia tiene límite** (TR-06) | 84, 85, 86, 87, 44, 717, 45, 47, 264, 265, 262, 263 | confirmado |
| AL-03 | la clave es `cuentaId` (camelCase), distinta de `cuenta_id` de CONSULTA | 4, 6 | confirmado |
| AL-04 | sobre `AC-9999` el gemelo escribe `AC-10000` | — | supuesto |

### CONSULTA;cuenta
| ID | Comportamiento | Evidencia | Confianza |
|---|---|---|---|
| CO-01 | → **200** `{"cuenta_id":"AC-0001","saldo":0}`: el saldo es un entero json y puede ser negativo o pasar de 2³¹ | 6, 9, 12, 20, 117, 230, 273 | confirmado |
| CO-02 | cuenta que no existe → **404** `{"error":"E401","mensaje":"cuenta inexistente"}` | 16, 25, 27, 30, 143 | confirmado |
| CO-03 | el id se compara exacto, sin normalizar: `ac-0001`, `AC-1`, `AC-00001` y ` AC-0001` (con espacio) no existen | 38, 239, 240, 241, 255 | confirmado |

### DEPOSITO;cuenta;monto
| ID | Comportamiento | Evidencia | Confianza |
|---|---|---|---|
| DE-01 | suma el monto al saldo → **200** `{"status":"recieved","operacionId":"OP-0001"}` (sic: `recieved`) | 7, 19, 97, 100, 225, 260, 261, 269, 270, 273 | confirmado |
| DE-02 | monto válido: entero de **1 a 10 cifras sin cero a la izquierda** (`^[1-9][0-9]{0,9}$`). si no → **400** `{"error":"E303","mensaje":"monto inválido"}`: `0`, `-5`, `10.5`, `abc`, `0100`, `1e3`, `+100`, ` 100`, 11 cifras o más | 91–96, 233, 234, 235, 237, 257, 259, 271, 272 | confirmado |
| DE-03 | los depósitos **no tienen límite** (solo el de cifras): 999.999.999 y 9.999.999.999 pasan | 97, 270 | confirmado |
| DE-04 | cuenta inexistente → 404 `E401` (después de validar el monto, DE-02) | 98, 218 | confirmado |

### TRANSFER;origen;destino;monto
| ID | Comportamiento | Evidencia | Confianza |
|---|---|---|---|
| TR-01 | mueve el monto del origen al destino → **200** `{"status":"recieved","operacionId":"OP-0002"}` | 8, 9, 11, 12, 106–108, 112, 113, 226, 227 | confirmado |
| TR-02 | monto inválido (mismas reglas que DE-02) → 400 `E303` | 109, 110, 220 | confirmado |
| TR-03 | origen igual a destino → **400** `{"error":"E304","mensaje":"origen y destino iguales"}` | 101, 219 | confirmado |
| TR-04 | origen o destino inexistente → 404 `E401` | 102, 103, 104, 221 | confirmado |
| TR-05 | saldo del origen menor que el monto → **422** `{"error":"E507","mensaje":"saldo insuficiente"}`. un saldo igual al monto alcanza; un saldo negativo no alcanza para nada | 17, 111, 231; 226 | confirmado |
| TR-06 | monto **mayor que 100.000** **entre cuentas de titulares distintos** → **422** `{"error":"E506","mensaje":"límite excedido"}`. 100.000 pasa. el límite es **por operación, no acumulado**: tres transferencias seguidas de 100.000 pasan. **entre cuentas con el mismo nombre de titular no hay límite** (150.000 de «Lucia» a «Lucia» pasa); el nombre se compara exacto («Lucia» y «lucia» son titulares distintos) | 10, 105, 766, 768, 814, 816; 11, 106, 107, 108; 813, 817; 815 | confirmado |
| TR-07 | orden dentro de TRANSFER: monto (E303) → origen = destino (E304) → existencia (E401) → bloqueo (E510, TR-08) → límite (E506, solo entre titulares distintos) → saldo (E507). por eso una transferencia sin fondos y sobre el límite da E506 entre titulares distintos (766, 816) y E507 entre cuentas del mismo titular (111, repetida idéntica en 806) | 220, 219, 221, 881–883, 771, 766, 816, 111, 806 | confirmado |
| TR-08 | **bloqueo**: cada cuenta lleva la cuenta de sus transferencias seguidas rechazadas por límite (E506) o saldo (E507), mezcladas o no. con **tres**, toda transferencia **desde** esa cuenta → **409** `{"error":"E510","mensaje":"cuenta bloqueada"}`, y sigue así. lo **reinician** un depósito a la cuenta o una transferencia exitosa desde ella; **no** lo reinician recibir una transferencia ni anular. los errores E303, E304 y E401 no suman. el bloqueo no afecta consultar, depositar ni recibir. es por cuenta: las fallas de otra cuenta no suman ni cortan la racha | 771, 824–827, 837–840, 893–896; 879, 880, 898; 885, 886, 926–928, 858–862; 907, 908, 917, 918; 867–871; 828–832; 847–853 | confirmado |

### ANULA;operacion
| ID | Comportamiento | Evidencia | Confianza |
|---|---|---|---|
| AN-01 | revierte la operación → **200** `{"ok":true,"anulada":"OP-0003"}` | 14, 116, 228 | confirmado |
| AN-02 | anular un depósito resta el monto de la cuenta, **aunque quede negativa** | 116, 117 | probable |
| AN-03 | anular una transferencia devuelve el monto al origen y lo resta del destino, **aunque el destino quede negativo** | 14 y 20 (ejemplos 13 y 19), 228, 229, 230 | confirmado |
| AN-04 | anular dos veces → **200** (no es error) `{"ok":false,"motivo":"ya anulada"}` | 15, 232 | confirmado |
| AN-05 | operación que no existe (`OP-0099`, `op-0001` en minúsculas, un id de cuenta, una que todavía no ocurrió) → **404** `{"error":"E402","mensaje":"operación inexistente"}` | 114, 115, 119, 245 | confirmado |

### HALT;confirmacion (oculto)
no aparece en los ejemplos: lo reveló la sugerencia del error de comando desconocido (`HELP` → `HALT`).

| ID | Comportamiento | Evidencia | Confianza |
|---|---|---|---|
| HA-01 | `HALT` con un argumento distinto de `1` (`AC-0001`, `CONFIRMAR`, `CONFIRMO`, `SI`, `CONFIRM`, `YES`, `OK`, `TRUE`) → **409** `{"error":"E520","mensaje":"operación destructiva: detiene el servicio; reenvía con confirmación"}` y no cambia nada | 145, 689–695 | confirmado |
| HA-02 | `HALT;1` **detiene el servicio para el token** → **503** `{"error":"E599","mensaje":"service halted"}` | 696, 719 | confirmado |
| HA-03 | detenido, **todo** `/msg` responde 503 `E599` (PING, CONSULTA, ALTA, json inválido, sin `m`, sin control, cuerpo grande), hasta el próximo `/__reset`, que lo repara | 697–699, 720–723, 726; 701–704, 727, 728 | confirmado |
| HA-04 | `HALT` sin argumentos o con dos → E302 | 137, 141, 718 | confirmado |
| HA-05 | otras confirmaciones posibles (`0`, `2`, `01`, `true` en minúsculas) no se probaron: el gemelo solo acepta `1` | — | supuesto |

### comando desconocido
| ID | Comportamiento | Evidencia | Confianza |
|---|---|---|---|
| DC-01 | → **400** `{"error":"E301","mensaje":"comando desconocido "}`, con **un espacio al final** del mensaje | 13, 120–126, 129–132, 154, 161–206 | confirmado |
| DC-02 | si hay un comando (de los siete, incluido `HALT`) a **distancia de edición (levenshtein) ≤ 2** del comando en mayúsculas, la respuesta agrega `"sugerencia":"<COMANDO>"`; a distancia 3, no | 127, 128, 147–153, 155–160, 209, 242, 252; 154 | confirmado |
| DC-03 | gana la **menor distancia** (`HALA` → `HALT` a 1, no `ALTA` a 2); en un empate, el primero en orden alfabético (`PITA` → `ALTA` sobre `PING`; `HANG` → `HALT` sobre `PING`; `ALT` → `ALTA` sobre `HALT`) | 715; 208, 256, 151 | probable |
| DC-04 | 57 nombres probados (RETIRO, SALDO, LISTA, BAJA, STOP, DEBUG, ADMIN…) no son comandos ni sugieren nada: los comandos son siete | 120–126, 129–132, 161–206 | probable |

## 4 · memoria entre requests
qué recuerda el servicio y qué cambia una respuesta según los requests anteriores.

| ID | Comportamiento | Evidencia | Confianza |
|---|---|---|---|
| ME-01 | el estado es **por token**: cuentas con su saldo, operaciones con su monto, tipo y si están anuladas, y si el servicio está detenido | material; 696–699 | confirmado (por token: material) |
| ME-02 | `/__reset` borra todo: las cuentas dejan de existir, los ids vuelven a `AC-0001` y `OP-0001`, y el servicio deja de estar detenido | 143; 23, 82, 135, 216, 248, 268, 704, 709; 97, 136, 225; 701–704 | confirmado |
| ME-03 | los ids son correlativos y **solo los consume lo que tuvo éxito**: un ALTA fallido no consume `AC-`, una transferencia fallida no consume `OP-` | 222, 223; 10, 11 | confirmado |
| ME-04 | depósitos y transferencias comparten la numeración `OP-`; **ANULA no crea operación** (tras anular `OP-0003`, el depósito siguiente es `OP-0004`) | 7, 8, 11, 19; 14 | confirmado |
| ME-05 | cada CONSULTA refleja todas las operaciones anteriores, incluidas las anuladas | 9, 12, 20, 112, 113, 117, 229, 230 | confirmado |
| ME-06 | una operación anulada lo sigue estando (la segunda anulación lo dice) | 15, 232 | confirmado |
| ME-07 | el límite no acumula: cada transferencia se mira sola | 106, 107, 108 | confirmado |
| ME-09 | cada cuenta guarda el **nombre del alta** (decide el límite, TR-06) y su **racha de transferencias fallidas** por límite o saldo (decide el bloqueo, TR-08) | 813–816; 824–827, 885–886, 926–928 | confirmado |
| ME-08 | el saldo no tiene piso: puede quedar negativo por anulaciones y entonces ninguna transferencia sale de esa cuenta | 117, 230, 231 | confirmado |

## 5 · errores
cada error con su status, su cuerpo exacto y en qué orden se evalúa frente a los otros. todos los cuerpos son json `{"error": <código>, "mensaje": <texto>}`; E301 puede traer además `"sugerencia"`.

| ID | Comportamiento | Evidencia | Confianza |
|---|---|---|---|
| ER-01 | `E404` · 404 · `ruta desconocida` | 52–61, 708, 725 | confirmado |
| ER-02 | `E001` · 401 · `no autorizado` | 50, 51, 63–67, 706, 707, 712, 724 | confirmado |
| ER-03 | `E599` · 503 · `service halted` (solo con el token detenido por `HALT;1`) | 696–699, 719–723, 726 | confirmado |
| ER-04 | `E101` · 413 · `cuerpo demasiado grande` | 274, 275, 711, 713 | confirmado |
| ER-05 | `E100` · 400 · `json inválido` | 68, 69 | confirmado |
| ER-06 | `E102` · 400 · `falta m` | 70–73, 76, 79, 80 | confirmado |
| ER-07 | `E103` · 400 · `falta control` | 41, 74, 249–251 | confirmado |
| ER-08 | `E104` · 400 · `segmento vacío` | 36, 210–212 | confirmado |
| ER-09 | `E201` · 400 · `control mal formado` | 18, 28, 31–35, 37, 213, 214, 253, 254 | confirmado |
| ER-10 | `E202` · 400 · `control inválido` | 3, 24, 26, 29, 42, 43, 46 | confirmado |
| ER-11 | `E301` · 400 · `comando desconocido ` (espacio final) | 13, 120–132, 147–206, 208, 209 | confirmado |
| ER-12 | `E302` · 400 · `aridad inválida` | 21, 88–90, 99, 118, 137, 215, 217, 222, 714, 718 | confirmado |
| ER-13 | `E303` · 400 · `monto inválido` | 91–96, 109, 110, 218, 220, 233–235, 237, 257, 259, 271, 272 | confirmado |
| ER-14 | `E304` · 400 · `origen y destino iguales` | 101, 219 | confirmado |
| ER-15 | `E401` · 404 · `cuenta inexistente` | 16, 25, 98, 102–104, 143, 221, 239–241 | confirmado |
| ER-16 | `E402` · 404 · `operación inexistente` | 114, 115, 119, 245 | confirmado |
| ER-17 | `E506` · 422 · `límite excedido` | 10, 105 | confirmado |
| ER-18 | `E507` · 422 · `saldo insuficiente` | 17, 111, 231 | confirmado |
| ER-22 | `E510` · 409 · `cuenta bloqueada` | 771, 827, 840, 852, 879, 880, 896, 898, 908, 918 | confirmado |
| ER-19 | `E520` · 409 · `operación destructiva: detiene el servicio; reenvía con confirmación` | 145, 689–695 | confirmado |
| ER-20 | **orden de evaluación** (el primero que falla responde): ruta (E404) → token (E001) → detenido (E599) → tamaño (E101) → json (E100) → `m` (E102) → menos de 2 segmentos (E103) → segmento vacío (E104) → formato del control (E201, no en PING) → valor del control (E202, no en PING) → comando (E301) → aridad (E302) → reglas del comando (TRANSFER: TR-07, con E510 y E506 antes que E507; DEPOSITO: E303 → E401; ANULA: E402) | E404 antes que E001: 59, 725 · E001 antes que E101: 712 · E599 antes que E101, E100, E102, E103: 726, 720, 721, 722 · E101 antes que E100: 713 · E104 antes que E202: 210 · E201 antes que E302 y E301: 213, 214 · E202 antes que E301 y E302: 42, 43 · E302 antes que E303: 217 · E303 antes que E401: 218 · TR-07 | confirmado (cada par, una o dos veces) |
| ER-21 | E103 antes que E104 cuando hay un solo segmento vacío (`m` = `""`) | 74 | probable |

## 6 · cambios durante el día
qué cambió, desde cuándo y cómo lo detectamos.

| ID | Comportamiento | Evidencia | Confianza |
|---|---|---|---|
| CA-01 | **sin cambios hasta las 10:5x bog**: los 20 ejemplos (grabados con la versión de la mañana) se reprodujeron idénticos a las 10:1x, y la secuencia `cmd-1` de las 10:1x repetida exacta a las 10:4x dio las mismas 31 respuestas | 2–21; 81–111 contra 776–806 | confirmado |
| CA-03 | una falsa alarma que no fue cambio: la v1 de esta spec decía «saldo antes que límite» por la línea 111, y el centinela vio lo contrario en 737. la repetición exacta (806) mostró que el original no había cambiado: la diferencia era el titular (TR-06) | 111, 737, 806 | confirmado |
| CA-02 | cómo se detecta un cambio: un **centinela** repite secuencias canónicas del log (los 20 ejemplos y una por familia de error) y compara con la regla del juez; solo una **repetición exacta que cambia** acredita un cambio. el detalle irá en `incident.md` | — | (método) |

## 7 · riesgos
comportamientos que un cliente nuevo no debería heredar, y cómo los cerraríamos.

| ID | Comportamiento | Evidencia | Confianza |
|---|---|---|---|
| RI-01 | **un comando oculto apaga el servicio**: `HALT;1` lo detiene, sin más autorización que el token de cliente. cerrarlo: sacarlo del canal de clientes; si hace falta, un endpoint de administración con otra credencial y confirmación de dos pasos | 145, 696–699 | confirmado |
| RI-02 | **la sugerencia filtra comandos ocultos**: `HELP` responde «¿quisiste decir HALT?». cerrarlo: sugerir solo comandos públicos, o no sugerir | 128, 158, 159, 256 | confirmado |
| RI-03 | **anular deja saldos negativos**: se puede gastar un depósito y después anularlo, o anular una transferencia que el destino ya gastó. cerrarlo: rechazar la anulación si deja una cuenta bajo cero, o anular solo dentro de una ventana y con fondos | 116, 117, 228–231 | confirmado |
| RI-04 | **el límite es por operación**: fraccionar evita el tope (tres de 100.000 pasan). cerrarlo: límite diario por cuenta | 106–108 | confirmado |
| RI-05 | **los depósitos no tienen límite** (9.999.999.999 en un pedido) | 270 | confirmado |
| RI-10 | **el límite se evita con un nombre**: entre cuentas del mismo titular no hay límite, y el titular es solo el texto del alta, sin verificar. cualquiera abre `ALTA;<el mismo nombre>` y mueve montos sin tope. cerrarlo: titular verificado (un id de cliente), no un nombre libre | 813, 817 | confirmado |
| RI-11 | **el bloqueo se levanta con un depósito de 1**: tres intentos fallidos bloquean, pero cualquier depósito, de cualquier monto, desbloquea. cerrarlo: desbloqueo por un canal aparte, o tras un tiempo | 885, 886, 926–928 | confirmado |
| RI-06 | **el dígito de control no es seguridad**: es una suma de verificación pública (la del iban), y `PING` ni la mira. no autentica ni impide fraude: solo detecta errores de tipeo | 2–21, 39, 40 | confirmado |
| RI-07 | **cualquier cuenta del token se consulta y se mueve por su id correlativo** (`AC-0001`, `AC-0002`…): no hay dueño de cuenta. cerrarlo: ids no adivinables y autorización por cuenta | 6, 9, 102–104 | probable |
| RI-08 | **el nombre no se valida** (5.000 caracteres, emoji, tabulaciones, un espacio). cerrarlo: largo máximo y caracteres permitidos | 263, 264, 265, 717 | confirmado |
| RI-09 | **rarezas de contrato que los clientes ya consumen**: `recieved` mal escrito, `cuentaId` en el alta y `cuenta_id` en la consulta, `"comando desconocido "` con espacio final, y la anulación repetida que responde 200 con `ok:false`. no se corrigen en silencio: se versiona la api y se avisa | 7, 4, 6, 13, 15 | confirmado |
