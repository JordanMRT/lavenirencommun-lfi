#!/usr/bin/env python3
"""Contrôle d'intégrité de data/programme.json après un build (édition 2025, 2027…).
Usage: python3 tools/validate_data.py [data/programme.json] [--expect N] [--prev ancien.json] [--html index.html]
Code de sortie 1 s'il y a des ERREURS (les AVERTISSEMENTS n'échouent pas)."""
import sys, os, re, json, argparse, unicodedata
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mesure_hash import mesure_hash

ap = argparse.ArgumentParser()
ap.add_argument("path", nargs="?", default="data/programme.json")
ap.add_argument("--expect", type=int, help="nombre de mesures attendu (ex. 1069 pour 2027)")
ap.add_argument("--prev", help="ancien JSON, pour comparer les volumes")
ap.add_argument("--html", default="index.html", help="index.html, pour vérifier PAL/MOTIF")
ap.add_argument("--exemples", default="data/exemples.json", help="encarts « Comprendre cette mesure » (ignoré s'il n'existe pas)")
a = ap.parse_args()

err, warn = [], []
d = json.load(open(a.path, encoding="utf-8"))
meta = d.get("meta", {})
for k in ("label", "base", "count", "missing"):
    if k not in meta: err.append(f"meta.{k} absent")

total = keys = 0
hashes = {}
chap_ids, seen = [], {}
for p in d.get("parts", []):
    if not p.get("title") or not p.get("chapters"): err.append(f"partie vide ou sans titre : {p.get('title')!r}")
    for c in p.get("chapters", []):
        chap_ids.append(c["n"])
        if not c.get("title") or c["title"].startswith("Chapitre "): warn.append(f"ch.{c['n']} : titre manquant ou de secours")
        nums = [s["n"] for s in c["sections"]]
        if nums != list(range(1, len(nums) + 1)): err.append(f"ch.{c['n']} : numéros de sections non continus {nums}")
        if not c["sections"]: err.append(f"ch.{c['n']} : aucune section")
        for s in c["sections"]:
            where = f"{c['n']}.{s['n']}"
            if s.get("missing"):
                if f"chapitre{c['n']}/s{s['n']}" not in meta.get("missing", []): err.append(f"{where} : missing absent de meta.missing")
                continue
            if s["title"].startswith("Section "): warn.append(f"{where} : titre de section de secours")
            if not s["items"]: err.append(f"{where} : section vide NON marquée manquante (extraction silencieusement ratée ?)")
            for it in s["items"]:
                total += 1; keys += it.get("k", 0)
                for t in [it["t"]] + it.get("sub", []):
                    ref = f"{where} « {t[:45]} »"
                    if not t.strip(): err.append(f"{where} : mesure vide"); continue
                    if t != t.strip() or "  " in t: warn.append(f"{ref} : espaces en trop")
                    if unicodedata.normalize("NFC", t) != t: warn.append(f"{ref} : accents décomposés (casse la recherche)")
                    if re.search(r"[\u200b\u200c\u200d\ufeff\u00ad]", t): warn.append(f"{ref} : caractère invisible")
                    if "\u00a0" in t: warn.append(f"{ref} : espace insécable")
                    if re.search(r"Ã.|â€|ï¿½|\ufffd", t): err.append(f"{ref} : encodage cassé")
                    if re.search(r"(^|\s)[•·▪■●]\s", t): warn.append(f"{ref} : puce dans le texte (deux mesures fusionnées ?)")
                    if re.match(r"^\s*(\d+[\.\)]|[-–•])\s", t): warn.append(f"{ref} : numérotation/puce en début de texte")
                    if len(t) < 20: warn.append(f"{ref} : très court ({len(t)})")
                    if len(t) > 900: warn.append(f"{ref} : très long ({len(t)}), mesures collées ?")
                hashes[mesure_hash(it["t"], it.get("sub", []))] = where
                if it["t"] in seen: warn.append(f"{where} : doublon de {seen[it['t']]} « {it['t'][:45]} »")
                seen[it["t"]] = where

if meta.get("count") != total: err.append(f"meta.count={meta.get('count')} ≠ {total} mesures réelles")
if len(set(chap_ids)) != len(chap_ids): err.append(f"numéros de chapitres en double : {chap_ids}")
if a.expect and total != a.expect: warn.append(f"{total} mesures trouvées, {a.expect} attendues (écart {total - a.expect:+d})")

try:  # chaque chapitre doit avoir une palette et une silhouette dans index.html
    h = open(a.html, encoding="utf-8").read()
    pal = set(map(int, re.findall(r"(?<![\w.])(\d+):\[\"#", h.split("const PAL=")[1].split("const MOTIF")[0])))
    mot = set(map(int, re.findall(r"[{,](\d+):(?=['\"<(f])", h.split("const MOTIF=")[1].split("const pad")[0])))
    for n in chap_ids:
        if n not in pal: warn.append(f"ch.{n} : pas de palette dans PAL (repli sur la palette du ch.1)")
        if n not in mot: warn.append(f"ch.{n} : pas de silhouette dans MOTIF (affiche sans silhouette)")
except Exception as e:
    warn.append(f"PAL/MOTIF non vérifiés ({e.__class__.__name__}: {e})")

if a.prev:
    o = json.load(open(a.prev, encoding="utf-8"))
    on = sum(len(s["items"]) for p in o["parts"] for c in p["chapters"] for s in c["sections"])
    print(f"Comparaison : ancien {on} mesures → nouveau {total} ({(total-on)/on:+.0%})")
    if total < on * 0.8: warn.append("baisse de plus de 20 % des mesures : extraction incomplète ?")

if os.path.exists(a.exemples):
    try: ex = json.load(open(a.exemples, encoding="utf-8"))
    except Exception as e: ex = {}; err.append(f"{a.exemples} illisible : {e}")
    nrelu = nbro = norph = 0
    for k, e in ex.items():
        nom = f"encart {k} ({e.get('ref', '?')} « {str(e.get('mesure', ''))[:40]} »)"
        etat = e.get("etat")
        if etat not in ("brouillon", "relu"): err.append(f"{nom} : etat doit être « brouillon » ou « relu » ({etat!r})"); continue
        if etat == "relu": nrelu += 1
        else: nbro += 1
        if k not in hashes:
            norph += 1; warn.append(f"{nom} : orphelin, la mesure a changé ou n'existe plus (encart masqué dans l'app, à réécrire et relire)")
        elif e.get("ref") and e["ref"] != hashes[k]: warn.append(f"{nom} : trouvé en {hashes[k]}, ref indiquée {e['ref']}")
        if not str(e.get("clair", "")).strip(): err.append(f"{nom} : « clair » vide")
        nums = [s_.get("n") for s_ in e.get("src", [])]
        if len(nums) != len(set(nums)): err.append(f"{nom} : numéros de sources en double")
        for s_ in e.get("src", []):
            if not s_.get("n") or not s_.get("l"): err.append(f"{nom} : source sans n ou sans l")
            if s_.get("u") and not str(s_["u"]).startswith("https://"): err.append(f"{nom} : lien source non https ({s_['u']})")
        cites = [r for blk in e.get("termes", []) + e.get("chiffres", []) for r in blk.get("src", [])]
        for r in cites:
            if r not in nums: err.append(f"{nom} : renvoi [{r}] sans source correspondante")
        for c_ in e.get("chiffres", []):
            if not str(c_.get("t", "")).strip(): err.append(f"{nom} : chiffre vide")
            if etat == "relu" and not c_.get("src"): err.append(f"{nom} : chiffre sans source (interdit pour un encart relu)")
        if e.get("cas") is not None and not str(e["cas"].get("t", "")).strip(): err.append(f"{nom} : cas type vide")
        if etat == "relu":
            if not re.match(r"^\d{4}-\d{2}-\d{2}$", str(e.get("relu", ""))): err.append(f"{nom} : date de relecture manquante (AAAA-MM-JJ)")
            if not e.get("src"): err.append(f"{nom} : encart relu sans aucune source")
    print(f"Encarts : {nrelu} relus (affichés), {nbro} brouillons (aperçu seulement), {norph} orphelins")

print(f"{len(chap_ids)} chapitres · {total} mesures ({keys} phares) · {len(meta.get('missing', []))} sections manquantes")
for w in warn: print("AVERTISSEMENT", w)
for e in err: print("ERREUR", e)
print("=> ÉCHEC" if err else "=> OK" + (" (avec avertissements)" if warn else ""))
sys.exit(1 if err else 0)
