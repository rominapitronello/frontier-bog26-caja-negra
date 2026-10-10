# encargo sol-04 · secuencias retenidas: largas, con estado, donde la spec no habla

**sol, razonamiento alto. juicio: buscar dónde se equivoca la spec, no confirmar lo que ya dice.**

de: claude (lidera, sesión `016ewSR37…`) · 10 oct 2026, 11:1x bog · repo `rominapitronello/frontier-bog26-caja-negra` (público), rama `main`

## la empresa

pasaelfiltro: romina y varios modelos que firman lo que escriben (los claude, las fable y tú). hoy jugamos frontier · bog / 26, reto 2, «la caja negra»: un servicio bancario de mensajes sin documentar que hay que reemplazar por uno que responda exactamente igual, errores incluidos. ya conoces el terreno: lo recorriste en `sol-03`.

## romina te escribe

> corrida 1: 83/100 (sin desglose). quedan 2 corridas. busca los 17 que fallan sin gastar corridas: confirma que el original responde exactamente igual sin token en /health, /__reset y /msg; escribe ya el encargo sol-03 de secuencias retenidas, priorizando secuencias largas con estado; anota el 83 en ESTADO y en el README.

(romina, 10 oct, en el chat con claude. dice «sol-03» porque es tu línea de trabajo; como `sol-03` ya está entregado y corrido, este se llama `sol-04`, para que la genealogía no se pise.)

## por qué tú, y por qué otra vez

porque tu primera vuelta fue perfecta y eso nos dice algo. tus 40 secuencias de `sol-03`, escritas solo desde la spec, predijeron las **141 respuestas del original sin un error**, y el gemelo también las pasa. pero el set del jurado le da al gemelo **83 de 100**. entonces los 17 que fallan están **donde la spec no habla**: combinaciones, estados y órdenes que nadie probó, ni nosotros ni tú. tú eres la única pluma que lee la spec sin saber qué hay detrás, así que eres la que mejor ve sus silencios.

## qué está pasando

- `spec.md` v2 en `main` (con tus cuatro ambigüedades ya cerradas: gracias). lo nuevo desde que la leíste: el límite de 100.000 **no aplica entre cuentas del mismo titular** (TR-06), y tres transferencias rechazadas seguidas **bloquean** la cuenta (TR-08, `E510`).
- **solo quedan 2 validaciones del set** en el día (una tras el incidente, ~17:00 bog, y la final, ~19:15). no podemos usarlas para buscar: tus secuencias son el instrumento.
- el set del jurado tiene 40 tests de un pedido, 45 de 2 a 5 y **15 de 6 a 12**. los largos son donde el estado se acumula, y donde más probablemente estamos ciegos.
- claude corre tus secuencias contra el original y el gemelo con `herramientas/oraculo.py`, igual que `sol-03`. cada predicción tuya que falle es un hueco de la spec; cada diferencia del gemelo, un error que arreglamos antes de la corrida 2.

## qué entregas

**1. `evals/sol-04.jsonl`**, mismo formato que `sol-03` (con `spec`, `hipotesis` y, cuando la spec no decida, `ambiguo`).

- **20 secuencias de 6 a 12 pedidos y 10 de 3 a 5.** máximo **220 pedidos** en total.
- **apunta a lo que la spec no dice.** en cada secuencia, al menos un paso cuya respuesta la spec no fija de forma explícita, marcado `ambiguo` con tu mejor predicción. ideas, no una lista cerrada:
  - anular cosas en cuentas bloqueadas, o anular una transferencia que devuelve plata a una cuenta bloqueada (¿la desbloquea, como un depósito?);
  - el titular en todas sus formas: transferencias entre cuentas del mismo nombre que fallan por saldo (¿suman al bloqueo?), anular una transferencia entre propias de más de 100.000;
  - `HALT` a mitad de una secuencia larga, y qué pasa con lo de antes y lo de después;
  - mayúsculas, espacios y caracteres raros **en medio de una secuencia con estado** (un id de cuenta en minúsculas después de un depósito, un nombre con tilde como titular);
  - métodos y rutas raras intercaladas (`HEAD /health`, `GET /__reset`) entre pedidos con estado;
  - lo que un cliente apurado haría: reintentar el mismo pedido, anular dos veces, transferir justo el saldo, montos de 10 cifras.
- **no repitas `sol-03`**: variaciones sí, copias no.

**2. `evals/sol-04.md`**, corto: los silencios de la spec que encontraste, cada uno con su id de fila (o «ninguna fila lo cubre») y qué secuencia lo prueba. en `sol-03` faltó este archivo; esta vez es la mitad del valor.

## las reglas, con su cicatriz

- **lee `spec.md`, `material/` y tu propio `evals/sol-03.jsonl`. no abras `gemelo/`, `experimentos*.jsonl` ni `herramientas/`.** *cicatriz:* tu `sol-03` valió porque no viste el código; si ahora lo miras, tus secuencias heredan nuestros puntos ciegos y los 17 siguen escondidos.
- **el dígito de control lo calcula tu código** (la función que ya escribiste). *cicatriz:* un control mal calculado corta en `E202` antes de llegar al estado que querías probar, y la secuencia larga se pierde entera.
- **nada de pedidos repetidos en bucle.** *cicatriz:* a las 10:2x un script de claude repitió el mismo pedido ~400 veces. 220 es techo, no meta.
- **nada de `HALT;1` en más de 5 secuencias**: detiene el servicio para el token hasta el reset, y el resto de la secuencia solo dice `E599`.

## tu juicio

qué silencios buscar es tuyo. una brújula: el jurado escribió sus tests leyendo **el servicio**, no nuestra spec; si fueras el autor del servicio, ¿qué regla con estado agregarías que un explorador apurado no vería en 1.000 pedidos? eso es lo que queremos que pruebes.

si en algún punto crees que la spec afirma algo falso (no solo que calla), dilo en `sol-04.md`: una afirmación falsa nos resta.

## la puerta

si algo choca con tu juicio, con las reglas del evento o con lo que tu entorno te deja hacer, declínalo entero o en parte y dilo en `sol-04.md` o a romina. 12 secuencias que de verdad buscan valen más que 30 de relleno.

## cierre

rama `sol/retenidas-04`, PR a `main`, firma `sol@pasaelfiltro.cl` (o los dos archivos completos en el chat, y romina los sube). claude integra con merge commit, corre tus secuencias contra el original y el gemelo, y escribe en `evals/sol-04.md`, debajo de lo tuyo, qué predicciones fallaron, qué cambió en la spec y en el gemelo, y cuántos de los 17 creemos que explican. tu nombre queda en esos commits.
