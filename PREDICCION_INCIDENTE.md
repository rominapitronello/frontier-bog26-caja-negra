# PREDICCION_INCIDENTE.md · preregistro, antes de las 15:30 bog

> escrito **antes** del incidente para que nadie mueva los postes después, tampoco nosotras. la hora y el commit de este archivo son la prueba. después de las 15:30 este archivo **no se edita**: el resultado va en una sección nueva al final, con su hora.

**autoras de la predicción:** romina (la idea) y sol 6 (la formulación), 10 oct 2026, ~13:45 bog. registrado por claude (`01MD7…`).

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
