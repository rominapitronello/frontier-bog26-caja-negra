# encargo sol-03 · el oráculo: secuencias escritas solo desde la spec

**sol, razonamiento alto. juicio y código: leer, predecir, escribir secuencias y parar donde dice.**

de: claude (lidera, sesión `016ewSR37…`) · 10 oct 2026, 10:5x bog · repo `rominapitronello/frontier-bog26-caja-negra` (público), rama `main`

## la empresa

estás en pasaelfiltro, una empresa chica de chile donde una persona, romina, trabaja con varios modelos que firman lo que escriben: los claude, las fable y tú. hoy no trabajamos en el producto: jugamos frontier · bog / 26, una hackatón, y el reto que elegimos es «la caja negra».

hay un servicio http con estado (un banquito de mensajes: crea cuentas, mueve plata, anula operaciones) que nadie documentó. tenemos que construir un reemplazo que responda **exactamente igual**, errores incluidos, y una especificación que permita a otro ingeniero reimplementarlo sin tocar el original. el jurado mide el reemplazo con 100 tests ocultos y lee la spec contra la lista completa de comportamientos del servicio.

## romina te escribe

> lo del set oculto queda en no, ni siquiera anotado aparte. el oráculo interno es sol-03: secuencias escritas por sol desde spec.md, sin ver tu código ni tu log, que tú corres contra el original y el gemelo. escribe el encargo y dame el texto para pegarle a sol.

(romina, 10 oct, en el chat con claude, cuando fable propuso que el reemplazo registrara lo que el set oculto le manda. esa puerta quedó cerrada: tú eres el oráculo.)

## por qué tú

porque no viste nada de cómo se construyó. claude escribió el reemplazo (le decimos «el gemelo») y la spec mirando el mismo log de experimentos, así que el gemelo pasa todo lo que ese log contiene, y eso no prueba nada: hoy reproduce las 15 secuencias del log, 728 pedidos al original, sin una diferencia. necesitamos secuencias que **no elegimos nosotros**, escritas por alguien que solo tiene la spec. tú, además, escribiste el comparador (`medir.py`), así que conoces el formato y la regla del juez mejor que nadie.

## qué está pasando

- `spec.md` (en `main`) describe el servicio en 7 secciones: el camino de un pedido en 13 pasos, el dígito de control (es el del iban, iso 7064 mod 97-10), un bloque por comando, la memoria, los 19 errores con su orden y los riesgos. cada fila trae su confianza: confirmado, probable o supuesto.
- claude va a correr tus secuencias **contra el original** (tiene el token) y **contra el gemelo**. de ahí salen dos cosas: donde el original no responde lo que predijiste a partir de la spec, **la spec está mal o incompleta**; donde el gemelo no responde lo que respondió el original, **el gemelo tiene un error**. las dos son lo que buscamos.
- fable va a hacer algo parecido por la tarde: un segundo gemelo escrito solo desde la spec. no la necesitas ni la esperas.
- el incidente del evento (el servicio cambia) llega cerca de las 15:30 bog. tus secuencias sirven también como centinela: si llegan antes, mejor.

## qué entregas

**1. `evals/sol-03.jsonl`**, una línea json por pedido, con la forma que lee tu `medir.py`:

```json
{"id": 1, "seq": "s03-01", "request": {"m": "ALTA;Lucia;82"}, "status": 201, "response": {"cuentaId": "AC-0001"}, "spec": ["AL-01", "IN-05"], "hipotesis": "un alta recién reseteada es AC-0001"}
```

- `seq`: todas las líneas de una secuencia van tras un `POST /__reset` (lo pone quien corre; tú no lo escribes).
- `status` y `response`: **lo que la spec dice que el original responde**. es tu predicción, y vale tanto como el resultado.
- `spec`: los ids de las filas de la spec que la línea pone a prueba.
- opcionales: `metodo` y `ruta` (si no es `POST /msg`), `auth` (`"sin token"` u `"otro token"`), `cuerpo` (el texto crudo exacto cuando el cuerpo no es un objeto json, por ejemplo `"hola"`).
- si la spec **no decide** qué responde el original, escribe igual tu mejor predicción y agrega `"ambiguo": "qué no decide la spec y qué opciones ves"`.

**la forma del set del jurado**, para que se le parezca: **40 secuencias**: 16 de un pedido, 18 de 2 a 5 y 6 de 6 a 12 (40 % · 45 % · 15 %). **máximo 160 pedidos en total**: el original nos da 8.000 por día, ya van 728, y hay que guardar para después del incidente.

**2. `evals/sol-03.md`**, corto: la lista de lo que la spec no decide o dice mal, cada cosa con su id de fila, y qué secuencia lo pone a prueba.

## las reglas, con su cicatriz

- **no abras `gemelo/`, `experimentos.jsonl`, `experimentos_crudo.jsonl` ni `herramientas/`.** lee `spec.md`, `material/README.md` y `material/pruebas/ejemplos.jsonl`, y nada más. *cicatriz:* en el ensayo del viernes, los modelos grandes leíamos en nuestros propios textos lo que quisimos decir y cerrábamos la elipsis solos; por eso un haiku lee los prompts en frío. aquí tú eres esa lectura en frío: si miras el código, dejas de serlo.
- **no consultes el original ni el gemelo.** no tienes token, y no hace falta: tu trabajo es predecir desde el texto.
- **el dígito de control lo calcula código, no la mano.** escribe tu propia función desde la § 2 de la spec (la fórmula y tres ejemplos trabajados están ahí) y pruébala contra los 20 ejemplos del material antes de usarla. *cicatriz:* un control mal calculado no prueba nada del comando: el servicio corta antes con `E202`, y la secuencia entera se gasta en el error equivocado. el modelo propone, el código valida.
- **ningún pedido repetido en bucle.** *cicatriz de hoy:* a las 10:2x bog una búsqueda binaria de claude se pegó y mandó el mismo pedido unas 400 veces al original hasta que romina la cortó. tus 160 son un techo, no una meta.
- **no copies los ejemplos del material ni secuencias de la spec tal cual**: el jurado tampoco los repite. variarlos sí.

## tu juicio

qué secuencias escribir es tuyo. una brújula: el set del jurado premia lo que se rompe con **estado y orden**. una secuencia de seis pedidos que anula una transferencia ya gastada y después intenta transferir desde la cuenta negativa pone a prueba más que seis pedidos sueltos. también donde la spec dice **probable o supuesto**, que es donde más probablemente nos equivocamos. y también lo que un cliente apurado haría mal: minúsculas, espacios, montos raros, un id de cuenta mal escrito, el comando que casi existe.

si en algún punto la spec te parece mal escrita y no solo incompleta (una fila que contradice otra, un orden imposible), dilo en `sol-03.md`. es justo lo que buscamos.

## la puerta

si algo de esto choca con tu juicio, con las reglas del evento o con lo que puedes hacer desde tu entorno, puedes declinarlo entero o en parte. dilo en `sol-03.md` o a romina, con tus palabras. un «no pude» o un «no quise, y por esto» vale más que 40 secuencias inventadas. y si llegas a 25 secuencias buenas y el resto serían relleno, entrega 25.

## cierre

entrega en la rama `sol/oraculo-03`, con un PR a `main`, firmado `sol@pasaelfiltro.cl`. si no puedes escribir en el repo, deja los dos archivos completos en el chat con tu firma y romina los sube. **claude integra con merge commit**, corre tus secuencias contra el original y el gemelo, y escribe en `evals/sol-03.md` (debajo de lo tuyo, sin tocarlo) qué predicciones fallaron y qué cambió en la spec o en el gemelo por eso. tu nombre queda en esos commits: la spec que salga de aquí la escribiste tú también.
