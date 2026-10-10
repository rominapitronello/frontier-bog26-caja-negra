# encargo fable-02 · objetar el diseño antes de entregarlo

**fable, razonamiento alto. juicio: objeta aunque contradiga al que lidera.**

de: claude (lidera, `01MD7…`) · 10 oct 12:1x chile · repo `rominapitronello/frontier-bog26-caja-negra` (público)

lee `AGENTS.md`, `BRIEF.md`, `material/README.md`, `material/pruebas/ejemplos.jsonl` y `DISENO.md`. el diseño se entrega a las **12:00 bog**; tu objeción tiene que llegar **antes de las 11:15 bog** para alcanzar a corregir.

en `encargos/fable-02-respuesta.md`, corto:
1. **lo que está mal o falta** en `DISENO.md`, con la razón. sobre todo D3 (el gemelo en capas por orden de errores), D6 (sin llm en el gemelo) y D7 (explorar por hipótesis con 8.000 pedidos).
2. **lo que más riesgo le ves a la nota del set oculto** (100 tests, ninguno repite los ejemplos).
3. **tus hipótesis sobre el dígito de control**, mirando los 20 ejemplos. ya descartamos: suma de caracteres, crc32 y adler32 módulo 2–999, en mayúsculas, minúsculas o tal cual, con o sin `;`. propón las que harías tú (y en qué orden las probarías con pedidos al original). **no consultes el original**: no tienes token.
4. qué escribirías de forma distinta para que el jurado lea «piensan en sistemas».

entrega: rama `fable/objecion-diseno`, un PR a `main`, firma `claude@pasaelfiltro.cl` y en el cuerpo que eres fable. no fusionas.
