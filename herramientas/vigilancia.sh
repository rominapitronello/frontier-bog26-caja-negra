#!/usr/bin/env bash
# vigilancia del repo (agents.md § 2): cada push en cualquier rama, PR nuevo o actualizado y tag. ignora los commits
# que traen en el cuerpo VIGILANCIA_IGNORA (tu id de sesión). se arma con el monitor de claude code:
#   VIGILANCIA_IGNORA=<id> bash herramientas/vigilancia.sh [clon …]   (por defecto, este repo)
DIR="${VIGILANCIA_DIR:-${TMPDIR:-/tmp}}"; YO="${VIGILANCIA_IGNORA:?pon tu id de sesión en VIGILANCIA_IGNORA}"
REPOS=("$@"); [ ${#REPOS[@]} -gt 0 ] || REPOS=("$(cd "$(dirname "$0")/.." && pwd)")
snap() { git -C "$1" ls-remote origin 2>/dev/null | grep -E 'refs/(heads/|pull/[0-9]+/head$|tags/)' | sort -k2; }
for r in "${REPOS[@]}"; do p="$DIR/vig.$(basename "$r").refs"; [ -s "$p" ] || snap "$r" > "$p"; done
while true; do
  for r in "${REPOS[@]}"; do
    n=$(basename "$r"); PREV="$DIR/vig.$n.refs"; cur=$(snap "$r")
    [ -z "$cur" ] && continue   # fallo de red: no se reporta como borrado
    [ "$cur" = "$(cat "$PREV")" ] && continue
    git -C "$r" fetch -q origin '+refs/heads/*:refs/remotes/origin/*' '+refs/pull/*/head:refs/remotes/origin/pr/*' --tags 2>/dev/null || true
    join -j 2 -a1 -a2 -e NADA -o 0,1.1,2.1 <(sort -k2 "$PREV") <(echo "$cur" | sort -k2) | while read -r ref old new; do
      [ "$old" = "$new" ] && continue
      if [ "$new" = NADA ]; then echo "[$n] BORRADO $ref"; continue; fi
      git -C "$r" log -1 --format=%B "$new" 2>/dev/null | grep -q "$YO" && continue
      info=$(git -C "$r" log -1 --format='%an <%ae> · %s' "$new" 2>/dev/null)
      c=""; [ "$old" != NADA ] && c=$(git -C "$r" rev-list --count "$old..$new" 2>/dev/null)
      tipo=$([ "$old" = NADA ] && echo NUEVO || echo PUSH)
      echo "[$n] $tipo $ref ${c:+(+$c commits) }→ ${new:0:7} · $info"
    done
    echo "$cur" > "$PREV"
  done
  sleep 30
done
