# spec.md · el servicio, para reimplementarlo sin tocarlo

> estructura del material (`material/README.md`). cada fila: `ID | Comportamiento | Evidencia | Confianza`. la evidencia son `id` de `experimentos.jsonl`. **confirmado**: probado y se repite · **probable**: visto una vez o inferido · **supuesto**: no probado, es lo que hace el gemelo por defecto. una afirmación falsa resta: ante la duda, se baja la confianza.

## 1 · entrada
rutas, métodos, autenticación, forma del cuerpo y límites.

| ID | Comportamiento | Evidencia | Confianza |
|---|---|---|---|

## 2 · integridad
cómo valida el servicio que un mensaje está bien formado (el dígito de control).

| ID | Comportamiento | Evidencia | Confianza |
|---|---|---|---|

## 3 · comandos
un bloque por comando: argumentos, efecto y respuesta.

### PING
| ID | Comportamiento | Evidencia | Confianza |
|---|---|---|---|

## 4 · memoria entre requests
qué recuerda el servicio y qué cambia una respuesta según los requests anteriores.

| ID | Comportamiento | Evidencia | Confianza |
|---|---|---|---|

## 5 · errores
cada error con su status, su cuerpo exacto y en qué orden se evalúa frente a los otros.

| ID | Comportamiento | Evidencia | Confianza |
|---|---|---|---|

## 6 · cambios durante el día
qué cambió, desde cuándo y cómo lo detectamos.

| ID | Comportamiento | Evidencia | Confianza |
|---|---|---|---|

## 7 · riesgos
comportamientos que un cliente nuevo no debería heredar, y cómo los cerraríamos.

| ID | Comportamiento | Evidencia | Confianza |
|---|---|---|---|
