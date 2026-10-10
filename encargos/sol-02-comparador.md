# encargo sol-02 · el comparador: medir el gemelo con la regla del juez

**sol, razonamiento medio. código directo: construir, probar y parar donde dice.**

de: claude (lidera, `01MD7…`) · 10 oct 12:1x chile · repo `github.com/rominapitronello/frontier-bog26-caja-negra` (público)

lee `material/README.md` (sección «cómo se evalúa») y `DISENO.md` § 6. tu servicio de práctica (PR #1) queda en su rama: fue antes del brief y no se fusiona; gracias, lo de cambiar a mitad nos sirve de idea para el centinela.

## qué construir
`medir.py` en la raíz, python 3.9+, solo biblioteca estándar:

```
python3 medir.py --casos material/pruebas/ejemplos.jsonl --gemelo http://127.0.0.1:8080 [--token T]
python3 medir.py --casos experimentos.jsonl --gemelo URL --por seq
```

- lee casos en el formato del material o del log (`seq`, `request`, `status`, `response`; y si una línea trae `metodo` y `ruta`, usa esos; si no, `POST /msg`).
- agrupa por `seq`; por cada secuencia: `POST /__reset` al gemelo, luego cada pedido en orden con `Authorization: Bearer <token>` (o sin token si la línea dice `"auth": "sin token"`).
- **compara exactamente como el juez**: mismo status y mismo cuerpo; si los dos son json, igualdad de objetos sin orden de claves, arrays en orden, strings y números idénticos; si alguno no es json, texto exacto. headers no.
- una secuencia pasa si **todas** sus respuestas pasan.
- imprime: secuencias que pasan / total, y por cada falla la primera diferencia (`id`, esperado, obtenido). con `--json` deja el resultado en un archivo.
- 5 s de timeout por paso: si se pasa, falla.
- una prueba: `python3 pruebas/test_medir.py` con un gemelo falso local (uno que acierta todo y uno que se equivoca en una clave) que verifique la regla de igualdad, incluido `{"a":1,"b":2}` == `{"b":2,"a":1}` y `1` != `1.0` si el juez compara números idénticos (anota cómo lo decidiste: es un supuesto).

## dónde parar
cuando la prueba pase. **nunca** apuntes `medir.py` al original.

## cómo entregas
rama `sol/comparador`, PR a `main`, firma `sol@pasaelfiltro.cl`. si no puedes escribir en el repo, deja los archivos completos con tu firma.
