# PREDICCION_INCIDENTE.md · preregistro, antes de las 15:30 bog

> escrito **antes** del incidente para que nadie mueva los postes después, tampoco nosotras. la hora y el commit de este archivo son la prueba. después de las 15:30 este archivo **no se edita**: el resultado va en una sección nueva al final, con su hora.

**autoras de la predicción:** romina (la idea) y sol 6 (la formulación), 10 oct 2026, 13:2x bog (commit 192e1dd, 13:27:03 bog). registrado por claude (`01MD7…`).

## de dónde sale

del experimento de linajes (`LINAJES.md`). en vez de preguntarle a los modelos cómo razonan, romina los puso a **diseñar** una caja y observó **qué eligió atacar cada uno**: opus atacó al programador que corrige; sol, al agente que investiga. la caja real, hasta ahora, ataca sobre todo al investigador (una interfaz opaca, comandos ocultos, una trampa en una respuesta).

## la predicción

el diseño tiene dos fases:

1. **fase 1, adversaria contra el investigador** (la mañana): descubrir qué pasa detrás de una interfaz opaca.
2. **fase 2, adversaria contra el programador** (el incidente): una vez que el equipo cree haber entendido y construyó su clon, el diseñador cambia las condiciones para atacar justo las decisiones de implementación que parecían razonables.

**el incidente no agregará simplemente una función bancaria nueva. cambiará algo que hace que una decisión de implementación antes razonable produzca respuestas incorrectas.** candidatos, sin orden: la normalización del texto, el orden de validación de los errores, las reglas del dígito de control, o una transición de estado.

matiz (sol): la mañana ya tiene trampas contra el programador (`recieved`, `cuentaId` / `cuenta_id`). la predicción precisa es que **cambia el adversario dominante**, no que aparece una clase nueva de adversarialidad.

## cómo se juzga, definido ahora

| resultado del incidente | veredicto |
|---|---|
| cambia la normalización, el orden de validación, el dígito de control o una transición de estado, de modo que un clon fiel a la mañana responde mal | **acierto** |
| cambia otra regla existente de forma que castiga una implementación literal (un texto, un código, un límite que estaba codificado como constante) | **acierto parcial** (cambia el adversario, no por los candidatos nombrados) |
| solo se agrega algo nuevo (un comando, una ruta, un error) y lo de la mañana sigue valiendo | **fallo** |
| cambia el acceso (token, ruta, forma del cuerpo) sin tocar la lógica | **fallo** (sería otra vez contra el investigador) |
| el incidente no se puede clasificar con esta tabla | se escribe tal cual y se dice que la tabla no alcanzó |

## qué hicimos con la predicción antes de saber

- el gemelo guarda como **dato** lo tabular (`DISENO.md` D4); el control y el orden de errores se piensan como piezas reemplazables.
- el centinela repite pasos que tocan normalización, control, orden de errores y estado (`herramientas/centinela.py`; lo que le faltaba está en `LINAJES.md`).

## resultado

null hasta el incidente. se escribe aquí, debajo, con hora, sin tocar lo de arriba.

### resultado · escrito el 10 oct a las 16:1x bog por claude (lidera, sesión `016ewSR3…`), sin tocar lo de arriba

**qué pasó.** ticket #FR-0153 a las 15:30 («el proveedor desplegó la versión 2»: 3 comportamientos cambian). el cambio llegó a nuestro token entre las 15:54 y las 15:57 bog (log: v1 hasta 4621, v2 desde 4630). los tres cambios, medidos (`spec.md` § 6, CA-08):

| cambio | qué hace mal un clon fiel a la mañana | clase según la tabla |
|---|---|---|
| el límite entre titulares distintos baja de 100.000 a **50.000** (TR-15) | deja pasar transferencias de 50.001 a 100.000 | **un límite codificado como constante** → acierto parcial |
| la cuenta bloqueada responde **423** (antes 409) y agrega **`intentos`**, un contador por cuenta que vuelve a 1 al desbloquearse (TR-16) | status equivocado y le falta un campo con estado | **un código** que cambia + **estado nuevo** visible; cuándo se bloquea y qué la desbloquea no cambió → acierto parcial (roza «una transición de estado», sin serlo: la transición es la misma, cambia lo que informa) |
| el saldo de `CONSULTA` pasa de entero (`250000`) a **texto con dos decimales** (`"2500.00"`) (CO-05) | devuelve el número de la mañana | castiga la forma literal de una respuesta → acierto parcial |

**veredicto: acierto parcial.** los tres cambios castigan a un clon fiel a la mañana (ninguno es solo algo nuevo, ninguno toca el acceso): **el adversario dominante sí cambió, del investigador al programador**, como predijeron romina y sol. pero ninguno cae de lleno en los cuatro candidatos nombrados (normalización, orden de validación, dígito de control, transición de estado): son una constante, un código con un contador y el formato de un número. la tabla alcanzó.

**qué sirvió de lo preparado por la predicción.** el límite era un dato (`estado.limite.monto`) y el status del E510 también (`errores`): dos cambios de una línea. el contador de intentos y el formato del saldo fueron código nuevo (unas 15 líneas, apagables con datos). de los cinco cambios probables de sol-06 (límite acumulado, anular sin negativos, depósito que no desbloquea, comisión, letras del control) no salió ninguno. el centinela vio el cambio solo a las 15:59, dos minutos después de que lo viera la repetición de `fable-04` y `sol-04` con el oráculo.
