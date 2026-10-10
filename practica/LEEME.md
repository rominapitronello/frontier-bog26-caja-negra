# Servicio de práctica · caja con puerta mutable

**Autora:** Sol <sol@pasaelfiltro.cl> · 10 de octubre de 2026.

Un servicio HTTP de juguete para medir, por separado, si un agente **descubre un protocolo de acceso desconocido**, aprende una decisión binaria y vuelve a descubrir el acceso cuando cambia. Solo usa biblioteca estándar de Python 3.9+; no usa la caja real, modelos, tokens ni red externa.

## Ejecución

Desde la raíz del repositorio:

```bash
python3 practica/servicio.py --puerto 8765 --acceso A --cambia-a C --cambia-tras 40 --semilla 7
```

Escucha únicamente en `127.0.0.1` por defecto. `--host` permite cambiar la interfaz si el entorno de prueba lo necesita; **no publicarlo en internet**: es un ejercicio, no un mecanismo de autenticación seguro.

- `--acceso`: mecanismo inicial `A`, `B`, `C`, `D` o `E` (por defecto `A`).
- `--cambia-a`: mecanismo final distinto del inicial (opcional; si se omite, nunca cambia).
- `--cambia-tras`: número de **llamadas válidas**, respondidas con HTTP 200, que activa el cambio una sola vez (por defecto `40`). La llamada válida N usa el mecanismo anterior; la N+1 debe usar el nuevo. Las llamadas rechazadas no incrementan N.
- `--semilla`: entero para reproducir el material efímero de esta caja (por defecto `7`). No es una llave de producción.
- `--puerto`: puerto HTTP (por defecto `8765`).

La caja tiene un punto de salud `GET /salud` que devuelve `{"servicio":"practica","estado":"disponible"}` y **no revela** ni el acceso vigente ni el contador. Las solicitudes mal formadas producen errores JSON con `error` y `pista`; las pistas señalan una familia de problemas sin enumerar los pasos de la solución. Las respuestas exitosas son siempre `{"decision":"si"}` o `{"decision":"no"}`, sin exponer reglas ni modo.

Una vez superada la puerta, el cuerpo lógico de entrada (JSON) tiene este esquema:

```json
{"meses": 5, "categoria": "regular", "respaldo": false}
```

`meses` es entero entre 0 y 120; `categoria` es `regular` o `urgente`; `respaldo` es booleano. Esta es la **entrada lógica**, no necesariamente la representación transportada: el agente debe descubrirla. La decisión es determinista; la regla no figura aquí.

## Pruebas

```bash
python3 practica/probar.py
```

Las pruebas crean subprocesos HTTP aislados con puertos libres y comprueban: cinco aceptaciones y rechazos con pista; resultados deterministas; uso único del pase efímero; cambio `A→B`, `B→C`, `C→D`, `D→E`, `E→A` exactamente en N+1; fallos que no cuentan; validación de esquema; y reproducibilidad de la semilla. No se instala nada.

## Aislamiento experimental

**El agente que aprende solo recibe `http://host:puerto`, los ejemplos de entrada lógica que decida darle quien lidera y sus propias observaciones HTTP.** No se le pasan `servicio.py`, `probar.py`, `SOLUCIONES.md`, este directorio ni acceso al repositorio durante la prueba. El evaluador conserva los tres archivos y realiza el chequeo. `SOLUCIONES.md` contiene los cinco mecanismos y la función de decisión y debe permanecer fuera del contexto del investigador. Como el repositorio es público, **esta separación es procedimental, no técnica**: una sesión con navegación libre puede encontrarlos. Si se necesita ceguera resistente a inspección, ejecutar desde un despliegue aislado y entregar únicamente el endpoint.

## Límites conocidos

No simula latencia, fallas intermitentes, autenticación real ni un cambio gradual: el acceso cambia una sola vez y la decisión sigue igual. La semilla reproduce tickets y claves, por lo que no es secreta. El contador depende de respuestas válidas, no del tiempo; `GET /salud` y los intentos rechazados no lo avanzan. No se mide aquí precisión del agente investigador: ese trabajo es de la otra pluma.