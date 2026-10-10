#!/usr/bin/env bash
# revisar_llms: ¿el repo sigue siendo legible para un modelo? (regla de romina, 10 oct)
#   1. toda cita de spec.md existe en experimentos.jsonl (verificar_spec.py)
#   2. todo enlace de llms.txt apunta a algo que existe
#   3. todo archivo o carpeta de la raíz aparece en llms.txt (si no, falta describirlo)
# sale con 0 si todo está bien; imprime solo lo que falla.
cd "$(dirname "$0")/.." || exit 2
falla=0
python3 -I herramientas/verificar_spec.py >/tmp/verificar_spec.$$ 2>&1 || { echo "spec: citas rotas"; grep -A20 'citas a ids' /tmp/verificar_spec.$$; falla=1; }
rm -f /tmp/verificar_spec.$$
for f in $(grep -oE '\]\(([^)#]+)' llms.txt | sed -E 's/^\]\(//'); do
  [ -e "$f" ] || { echo "llms.txt: enlace roto → $f"; falla=1; }
done
for f in $(ls -A | grep -vE '^(\.git|\.gitignore|__pycache__|llms\.txt|experimentos_crudo\.jsonl|Dockerfile|railway\.json|CLAUDE\.md|RUBRICA\.md|LECCIONES_DEL_ENSAYO\.md)$'); do
  git check-ignore -q "$f" && continue   # lo que git ignora (el candado del turno, cachés) no viaja: no se describe
  grep -qF "$f" llms.txt || { echo "llms.txt: no describe → $f"; falla=1; }
done
exit $falla
