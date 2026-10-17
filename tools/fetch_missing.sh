#!/usr/bin/env bash
# Récupère les 8 sections manquantes depuis d'autres captures de la Wayback Machine.
# Usage : bash tools/fetch_missing.sh [dossier_sortie]   (défaut : pages_manquantes)
# Pour chaque section : liste toutes les captures « 200 » (API CDX), essaie de la plus récente à la plus ancienne,
# garde la première page qui contient bien <section class="contenu">. Ne modifie pas le dépôt.
OUT="${1:-pages_manquantes}"; BASE="melenchon2027.fr/programme2025/livre"
SECTIONS="7/6 7/8 8/3 8/5 14/4 15/3 16/2 16/7"
mkdir -p "$OUT"; ok=0; ko=0
for sec in $SECTIONS; do
  c="${sec%/*}"; s="${sec#*/}"; slug="chapitre$c/s$s"; file="$OUT/chapitre${c}_s${s}.html"
  caps=$(curl -s --compressed "https://web.archive.org/cdx/search/cdx?url=$BASE/$slug&matchType=prefix&filter=statuscode:200&fl=original,timestamp" \
        | awk -v re="/chapitre$c/s$s/?$" '$1 ~ re {print $2}' | sort -ru | head -8)
  if [ -z "$caps" ]; then echo "AUCUNE capture 200 : $slug"; ko=$((ko+1)); sleep 2; continue; fi
  found=""
  for ts in $caps; do
    curl -sL --compressed -o "$file" "https://web.archive.org/web/${ts}id_/https://$BASE/$slug"
    if grep -q 'class="[^"]*contenu' "$file" 2>/dev/null; then found="$ts"; break; fi
    sleep 2
  done
  if [ -n "$found" ]; then echo "OK $slug (capture $found)"; ok=$((ok+1)); else echo "ÉCHEC $slug (captures sans contenu)"; rm -f "$file"; ko=$((ko+1)); fi
  sleep 2
done
echo "=> $ok récupérée(s), $ko manquante(s). Étape suivante : python3 tools/merge_missing.py $OUT"
