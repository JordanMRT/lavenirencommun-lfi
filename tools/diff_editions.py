#!/usr/bin/env python3
"""Compare deux éditions (data/programme.json) et dit ce qui change, mesure par mesure.
Sert à préparer une nouvelle édition (2027…) sans casse : rien n'est modifié, on lit seulement.

Usage : python3 tools/diff_editions.py ancien.json nouveau.json [--exemples data/exemples.json]
                                       [--seuil 0.60] [--detail] [--rapport rapport.md]

Ce que ça donne :
  1. Un bilan : mesures identiques (dont déplacées), modifiées, supprimées, nouvelles.
  2. La correspondance des chapitres ancien → nouveau : sert à vérifier que chaque thème garde SA palette
     et SA silhouette dans index.html (PAL et MOTIF sont rangés par numéro de chapitre).
  3. Un verdict pour chaque encart de data/exemples.json : intact, à réviser (mesure modifiée, avec les
     mots changés) ou sans suite (mesure supprimée). Un encart dont la mesure change est masqué dans l'app.
--detail : affiche aussi la liste complète. --rapport : écrit le rapport complet (détail inclus) en Markdown.

Une mesure « identique » = même empreinte que tools/mesure_hash.py (espaces et accents normalisés).
Une mesure « modifiée » = texte différent mais très proche (similarité mots à mots ≥ --seuil), rapprochée
de l'ancienne une seule fois. Rien n'est inventé : c'est un rapprochement à vérifier à l'œil."""
import sys, os, re, json, math, argparse, unicodedata, difflib
from collections import Counter, defaultdict
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mesure_hash import mesure_hash

ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
ap.add_argument("ancien"); ap.add_argument("nouveau")
ap.add_argument("--exemples", default="data/exemples.json", help="encarts à évaluer (ignoré s'il n'existe pas)")
ap.add_argument("--seuil", type=float, default=0.60, help="similarité minimale pour dire « modifiée » (0 à 1, défaut 0.60)")
ap.add_argument("--detail", action="store_true", help="affiche aussi les listes complètes")
ap.add_argument("--rapport", help="écrit le rapport complet en Markdown dans ce fichier")
a = ap.parse_args()


def norm_titre(t):
    return re.sub(r"\s+", " ", unicodedata.normalize("NFC", t).lower()).strip()


def charger(path):
    try: d = json.load(open(path, encoding="utf-8"))
    except Exception as e: sys.exit(f"Impossible de lire {path} : {e}")
    L = []
    for p in d["parts"]:
        for c in p["chapters"]:
            for s in c["sections"]:
                for i, it in enumerate(s["items"]):
                    sub = it.get("sub", [])
                    L.append({"c": c["n"], "ct": c["title"], "s": s["n"], "st": s["title"], "i": i, "k": it.get("k", 0),
                              "t": it["t"], "sub": sub, "txt": " ".join([it["t"], *sub]),
                              "h": mesure_hash(it["t"], sub), "ref": f"{c['n']}.{s['n']}",
                              "lieu": (norm_titre(c["title"]), norm_titre(s["title"]))})
    return d.get("meta", {}), L


def mots(t):
    return re.findall(r"\w+", unicodedata.normalize("NFC", t).lower())


def diff_mots(old, new):
    """Texte avec [-mots retirés-] et {+mots ajoutés+} ; les longs passages communs sont abrégés."""
    A, B, out = old.split(), new.split(), []
    for op, i1, i2, j1, j2 in difflib.SequenceMatcher(None, A, B, autojunk=False).get_opcodes():
        if op == "equal":
            seg = A[i1:i2]
            out.append(" ".join(seg) if len(seg) <= 12 else " ".join(seg[:4]) + " […] " + " ".join(seg[-4:]))
        else:
            if i2 > i1: out.append("[-" + " ".join(A[i1:i2]) + "-]")
            if j2 > j1: out.append("{+" + " ".join(B[j1:j2]) + "+}")
    return " ".join(out)


metaA, A = charger(a.ancien)
metaB, B = charger(a.nouveau)

# 1. Identiques : même empreinte (on préfère la mesure qui est restée dans la même section)
parN = defaultdict(list)
for j, m in enumerate(B): parN[m["h"]].append(j)
paire, utilisees = {}, set()            # index ancien -> (index nouveau, similarité)
for i, m in enumerate(A):
    cands = [j for j in parN.get(m["h"], []) if j not in utilisees]
    if not cands: continue
    j = next((j for j in cands if B[j]["lieu"] == m["lieu"]), cands[0])
    paire[i] = (j, 1.0); utilisees.add(j)

# 2. Modifiées : rapprochement flou des restes (index inversé pondéré, puis similarité mot à mot)
resteA = [i for i in range(len(A)) if i not in paire]
resteB = [j for j in range(len(B)) if j not in utilisees]
motsB = {j: mots(B[j]["txt"]) for j in resteB}
df = Counter(w for j in resteB for w in set(motsB[j]))
idf = {w: math.log(1 + len(resteB) / n) for w, n in df.items()}
inv = defaultdict(list)
for j in resteB:
    for w in set(motsB[j]): inv[w].append(j)
proche, couples = {}, []                # proche : meilleur candidat même sous le seuil (pour les encarts)
for i in resteA:
    wa = mots(A[i]["txt"]); score = Counter()
    for w in set(wa):
        for j in inv.get(w, ()): score[j] += idf[w]
    best = None
    for j, _ in score.most_common(6):
        r = difflib.SequenceMatcher(None, wa, motsB[j], autojunk=False).ratio()
        if best is None or r > best[1]: best = (j, r)
        if r >= a.seuil: couples.append((r, i, j))
    if best: proche[i] = best
pris = set()
for r, i, j in sorted(couples, reverse=True):
    if i in paire or j in pris: continue
    paire[i] = (j, r); pris.add(j)

utilisees |= pris
identiques = {i: j for i, (j, r) in paire.items() if r == 1.0}
modifiees = {i: (j, r) for i, (j, r) in paire.items() if r < 1.0}
deplacees = [(i, j) for i, j in identiques.items() if A[i]["lieu"] != B[j]["lieu"]]
supprimees = [i for i in range(len(A)) if i not in paire]
nouvelles = [j for j in range(len(B)) if j not in utilisees]

out = []
P = out.append
fmt = lambda m: f"{m['ref']}#{m['i']} {'★ ' if m['k'] else ''}{m['t'][:110]}{'…' if len(m['t']) > 110 else ''}"
pct = lambda x, n: f"{x / n:.0%}" if n else "—"

P("# Comparaison d'éditions\n")
P(f"- Ancienne : `{a.ancien}` — {metaA.get('label', '?')} — {len(A)} mesures ({sum(m['k'] for m in A)} phares)")
P(f"- Nouvelle : `{a.nouveau}` — {metaB.get('label', '?')} — {len(B)} mesures ({sum(m['k'] for m in B)} phares)\n")
P("## Bilan\n")
P("| | Mesures | Part de l'ancienne édition |\n|---|---:|---:|")
P(f"| Identiques | {len(identiques)} | {pct(len(identiques), len(A))} |")
P(f"| dont déplacées (autre section ou autre chapitre) | {len(deplacees)} | |")
P(f"| Modifiées (texte proche, seuil {a.seuil:.0%}) | {len(modifiees)} | {pct(len(modifiees), len(A))} |")
P(f"| Supprimées | {len(supprimees)} | {pct(len(supprimees), len(A))} |")
P(f"| Nouvelles | {len(nouvelles)} | (part de la nouvelle : {pct(len(nouvelles), len(B))}) |\n")

# Correspondance des chapitres
P("## Correspondance des chapitres\n")
P("À contrôler dans `index.html` : PAL (palette) et MOTIF (silhouette) sont rangés par numéro de chapitre.\n")
chapA = {}; chapB = {}
for m in A: chapA.setdefault(m["c"], [m["ct"], 0])[1] += 1
for m in B: chapB.setdefault(m["c"], [m["ct"], 0])[1] += 1
vers = defaultdict(Counter)
for i, (j, r) in paire.items(): vers[A[i]["c"]][B[j]["c"]] += 1
recus = Counter()
P("| Ancien chapitre | Mesures | → Nouveau chapitre | Retrouvées | Verdict |\n|---|---:|---|---:|---|")
for c, (titre, n) in sorted(chapA.items()):
    if not vers[c]: P(f"| {c}. {titre} | {n} | (aucun) | 0 | **DISPARU ou entièrement réécrit** |"); continue
    nc, k = vers[c].most_common(1)[0]; recus[nc] += k
    meme_titre = unicodedata.normalize("NFC", chapB[nc][0]).lower() == unicodedata.normalize("NFC", titre).lower()
    if nc == c and meme_titre: verdict = "inchangé"
    elif nc != c and meme_titre: verdict = "**RENUMÉROTÉ**"
    elif nc == c: verdict = "titre changé"
    else: verdict = "**RENUMÉROTÉ** et titre changé"
    eclate = f" (éclaté sur {len(vers[c])} chapitres)" if len(vers[c]) > 1 else ""
    P(f"| {c}. {titre} | {n} | {nc}. {chapB[nc][0]} | {k} ({pct(k, n)}) | {verdict}{eclate} |")
P("")
for c, (titre, n) in sorted(chapB.items()):
    if c not in recus: P(f"- Chapitre **nouveau** : {c}. {titre} ({n} mesures) — il faudra lui donner une palette et une silhouette.")
P("")

# Encarts
if os.path.exists(a.exemples):
    try: ex = json.load(open(a.exemples, encoding="utf-8"))
    except Exception as e: ex = {}; P(f"*Encarts illisibles ({e})*\n")
    parH = {m["h"]: i for i, m in enumerate(A)}
    cat = defaultdict(list)
    for k, e in ex.items():
        etat = e.get("etat", "?") if isinstance(e, dict) else "?"
        nom = f"`{k}` ({etat}) {e.get('ref', '?') if isinstance(e, dict) else '?'} « {str(e.get('mesure', ''))[:50] if isinstance(e, dict) else ''} »"
        if k not in parH: cat["DÉJÀ ORPHELIN dans l'ancienne édition"].append(f"- {nom}"); continue
        i = parH[k]
        if i in identiques:
            j = identiques[i]; dep = f" — déplacée de {A[i]['ref']} à {B[j]['ref']}" if A[i]["lieu"] != B[j]["lieu"] else ""
            cat["INTACTS (la mesure est identique, l'encart reste affiché)"].append(f"- {nom} → {B[j]['ref']}{dep}"); continue
        if i in modifiees:
            j, r = modifiees[i]
            cat["À RÉVISER (mesure modifiée : l'encart est masqué tant qu'il n'est pas réécrit)"].append(
                f"- {nom} → {B[j]['ref']}, similarité {r:.0%}\n  - changement : {diff_mots(A[i]['txt'], B[j]['txt'])}")
        else:
            near = proche.get(i); hint = f"\n  - plus proche (similarité {near[1]:.0%}, pas retenue) : {fmt(B[near[0]])}" if near and near[1] >= 0.4 else ""
            cat["SANS SUITE (mesure supprimée ou profondément réécrite)"].append(f"- {nom}{hint}")
    P(f"## Encarts ({len(ex)})\n")
    for titre in ["INTACTS (la mesure est identique, l'encart reste affiché)",
                  "À RÉVISER (mesure modifiée : l'encart est masqué tant qu'il n'est pas réécrit)",
                  "SANS SUITE (mesure supprimée ou profondément réécrite)", "DÉJÀ ORPHELIN dans l'ancienne édition"]:
        if cat.get(titre): P(f"### {titre} — {len(cat[titre])}\n"); P("\n".join(cat[titre])); P("")
    if not ex: P("Aucun encart.\n")

# Détail
detail = ["## Détail\n"]
if deplacees:
    detail.append(f"### Déplacées ({len(deplacees)})\n")
    detail += [f"- {A[i]['ref']} → {B[j]['ref']} : {fmt(A[i])}" for i, j in deplacees]; detail.append("")
if modifiees:
    detail.append(f"### Modifiées ({len(modifiees)})\n")
    for i, (j, r) in sorted(modifiees.items(), key=lambda x: x[1][1]):
        detail.append(f"- {A[i]['ref']}#{A[i]['i']} → {B[j]['ref']}#{B[j]['i']} ({r:.0%}) : {diff_mots(A[i]['txt'], B[j]['txt'])}")
    detail.append("")
if supprimees: detail.append(f"### Supprimées ({len(supprimees)})\n"); detail += [f"- {fmt(A[i])}" for i in supprimees]; detail.append("")
if nouvelles: detail.append(f"### Nouvelles ({len(nouvelles)})\n"); detail += [f"- {fmt(B[j])}" for j in nouvelles]; detail.append("")

if a.rapport:
    open(a.rapport, "w", encoding="utf-8").write("\n".join(out + detail) + "\n")
print("\n".join(out + (detail if a.detail else [])))
if a.rapport: print(f"Rapport complet écrit dans {a.rapport}")
elif not a.detail: print("(ajouter --detail pour les listes complètes, ou --rapport rapport.md)")
