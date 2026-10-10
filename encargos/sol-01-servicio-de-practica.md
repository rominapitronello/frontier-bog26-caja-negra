# encargo sol-01 · un servicio de práctica con acceso raro que cambia a mitad

> **reemplazado (10 oct 11:5x chile):** se escribió antes del brief, sobre un supuesto «acceso raro» que el brief del reto 2 no confirma. el reto es clonar un servicio http con estado (`BRIEF.md`, `DISENO.md`). no se ejecuta; queda como genealogía.

**sol, razonamiento medio. código directo: construir, probar y parar donde dice.**

de: claude (lidera, sesión `01MD7…`) · 10 oct 11:5x chile · repo: `rominapitronello/frontier-bog26-caja-negra` (público)

## por qué tú
el sistema tiene que **aprender** cómo se accede a un servicio sin documentación, y volver a aprenderlo cuando el incidente (15–16 bog) cambie el acceso. para medirlo antes de tocar el servicio real necesitamos un servicio de práctica **escrito por alguien que no escribe el que aprende**. en el ensayo lo hiciste tú (`ensayo/publico/` del repo del ensayo) y fue lo que nos dejó medir. si `BRIEF.md` está en el repo, léelo primero; si no, esto no depende del brief.

## qué construir
`practica/servicio.py`, python 3.9+, solo biblioteca estándar (`http.server`), un comando:

```
python3 practica/servicio.py --puerto 8765 --acceso A --cambia-a C --cambia-tras 40 --semilla 7
```

- **varias formas de acceso no comunes**, elegibles con `--acceso` (al menos 5; tú decides cuáles: por ejemplo la credencial en un lugar raro, un desafío previo que entrega un token de un solo uso, el cuerpo codificado, una firma con el cuerpo, un método o una ruta que no son los esperables). cada una, si le hablas mal, responde con un error **que da una pista pero no la solución**.
- **el cambio:** con `--cambia-a C --cambia-tras N`, después de N llamadas válidas el acceso pasa a la forma C, sin aviso.
- **detrás del acceso, una decisión simple** sobre una entrada json (lo que quieras, determinista) para que haya algo que aprender.
- `practica/LEEME.md`: cómo se corre, y **en un archivo aparte que el que aprende no lee** (`practica/SOLUCIONES.md`) qué es cada forma. el que aprende no debe conocerlas.
- una prueba mínima: `python3 practica/probar.py` levanta el servicio y verifica que cada forma acepta lo correcto, rechaza lo incorrecto y que el cambio ocurre en la llamada N+1.

## dónde parar
cuando `probar.py` pase. no escribas el cliente que aprende: eso es de otra pluma, a propósito.

## cómo entregas
si puedes escribir en el repo: rama `sol/servicio-de-practica`, commits con tu firma (`sol@pasaelfiltro.cl`), un PR a `main`; el que lidera lo integra. si no puedes, deja los archivos completos en tu respuesta con tu firma y romina los trae.
