#!/usr/bin/env python3
"""Fusionne des sections récupérées après coup dans data/programme.json (remplace les « section pas encore importée »).
Usage: python3 tools/merge_missing.py <dossier_pages> [data/programme.json] [--force]
Le dossier contient des fichiers chapitreN_sM.html (voir tools/fetch_missing.sh).
Même extraction que build_data.py. Une section sans mesure extraite n'est JAMAIS écrite (on ne publie pas du vide).
--force : remplace aussi une section déjà importée."""
import sys, os, re, json, glob
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from build_data import read, parse_section

args = [a for a in sys.argv[1:] if not a.startswith("--")]
force = "--force" in sys.argv
folder = args[0]; path = args[1] if len(args) > 1 else "data/programme.json"
data = json.load(open(path, encoding="utf-8"))
index = {(c["n"], s["n"]): s for p in data["parts"] for c in p["chapters"] for s in c["sections"]}
done, skipped = [], []

for f in sorted(glob.glob(os.path.join(folder, "chapitre*_s*.html"))):
    r = re.search(r"chapitre(\d+)_s(\d+)\.html$", f)
    key = (int(r[1]), int(r[2])); slug = f"chapitre{key[0]}/s{key[1]}"
    S = index.get(key)
    if not S: skipped.append((slug, "section inconnue dans le JSON")); continue
    if not S.get("missing") and not force: skipped.append((slug, "déjà importée (--force pour remplacer)")); continue
    m = read(f).find("main"); box = m and m.find("section", class_="contenu")
    if not box: skipped.append((slug, "page sans <section class=\"contenu\"> (page d'erreur ?)")); continue
    new = {"n": S["n"], "title": S["title"], "intro": "", "items": []}
    parse_section(new, m, box)
    if not new["items"]: skipped.append((slug, "aucune mesure extraite (structure HTML différente ?)")); continue
    S.clear(); S.update(new)
    if slug in data["meta"]["missing"]: data["meta"]["missing"].remove(slug)
    done.append((slug, S))

data["meta"]["count"] = sum(len(s["items"]) for p in data["parts"] for c in p["chapters"] for s in c["sections"])
if done: json.dump(data, open(path, "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))

for slug, S in done:
    k = sum(i.get("k", 0) for i in S["items"]); sub = sum(len(i.get("sub", [])) for i in S["items"])
    print(f"IMPORTÉE {slug} « {S['title']} » : {len(S['items'])} mesures ({k} phares, {sub} sous-mesures)")
    print(f"   intro : {S['intro'][:90]}…\n   1re   : {S['items'][0]['t'][:90]}…\n   dern. : {S['items'][-1]['t'][:90]}…")
for slug, why in skipped: print(f"IGNORÉE  {slug} : {why}")
print(f"=> {len(done)} importée(s), {len(skipped)} ignorée(s) ; total {data['meta']['count']} mesures ; encore manquantes : {data['meta']['missing'] or 'aucune'}")
print("À FAIRE : comparer chaque section avec la source, puis python3 tools/validate_data.py")
