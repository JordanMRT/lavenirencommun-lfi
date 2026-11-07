#!/usr/bin/env python3
"""Construit data/programme.json (édition 2027) depuis les pages HTML de melenchon2027.fr/programme/livre.
Usage: python3 tools/build_data_2027.py <dossier_pages> <sortie.json>
Le dossier contient les pages archivées : <partie>.html et <partie>_chapitreN.html.
Dépendances: beautifulsoup4, lxml. Ne modifie rien d'autre que le fichier de sortie."""
import sys, os, re, json, unicodedata
from bs4 import BeautifulSoup

EDITION = {"label": "L'Avenir en commun, édition 2027", "snapshot": "2026-11-07",
           "base": "https://melenchon2027.fr/programme/livre"}
PARTS = ["pour-une-bifurcation-ecologique-et-sociale", "une-economie-au-service-des-besoins",
         "mettre-en-securite-sociale", "le-gout-du-futur-aux-nouvelles-frontieres-de-l-humanite",
         "fonder-la-6e-republique", "un-monde-ordonne"]
INVISIBLES = dict.fromkeys(map(ord, "\u200b\u200c\u200d\ufeff\u00ad"))

def txt(el):
    # séparateur vide : « 6<sup>e</sup> République » doit rester « 6e République »
    return unicodedata.normalize("NFC", " ".join(el.get_text("", strip=False).split()).translate(INVISIBLES))

def soup(path): return BeautifulSoup(open(path, encoding="utf-8", errors="replace").read(), "lxml")

def parse_section(sec, notes, where):
    h3 = sec.find("h3", class_="section-title")
    S = {"title": txt(h3), "id": h3.get("id", ""), "intro": "", "items": []}
    seen_list = False
    for el in sec.find_all(True, recursive=False):
        k = el.get("class") or []
        if el.name == "p":
            S["intro"] = (S["intro"] + " " + txt(el)).strip()
            if seen_list: notes.append(f"{where} : paragraphe APRÈS la liste, ajouté à l'intro : {txt(el)[:70]!r}")
        elif el.name == "div" and "mesure-cle" in k:
            p = el.find("p"); S["items"].append({"t": txt(p or el), "k": 1})
        elif el.name == "ul":
            seen_list = True
            for li in el.find_all("li"):
                lk = li.get("class") or []
                if "mesure" in lk: S["items"].append({"t": txt(li), "k": 0})
                elif "sous_mesure" in lk and S["items"]: S["items"][-1].setdefault("sub", []).append(txt(li))
                elif not lk and li.find("ul") is None: notes.append(f"{where} : <li> sans classe ignoré : {txt(li)[:70]!r}")
    return S

def main(pages, out):
    data = {"meta": {**EDITION, "missing": []}, "parts": []}
    notes, n, total, subs = [], 0, 0, 0
    for slug in PARTS:
        m = soup(f"{pages}/{slug}.html").find("main")
        ptitle = re.sub(r"^Partie \d+\s*[–-]\s*", "", txt(m.find("h1") or m.find("h2")))
        P = {"title": ptitle, "slug": slug, "chapters": []}
        k = 1
        while os.path.exists(f"{pages}/{slug}_chapitre{k}.html"):
            m = soup(f"{pages}/{slug}_chapitre{k}.html").find("main")
            n += 1
            C = {"n": n, "k": k, "title": re.sub(r"^Chapitre \d+\s*:\s*", "", txt(m.find("h1"))), "sections": []}
            for i, sec in enumerate(m.find("div", class_="chapitre_sections").find_all("section", recursive=False), 1):
                S = parse_section(sec, notes, f"{n}.{i} ({slug[:12]} ch{k})"); S["n"] = i
                total += len(S["items"]); subs += sum(len(x.get("sub", [])) for x in S["items"])
                if not S["items"]: notes.append(f"{n}.{i} : section sans mesure (liste dans le texte ?)")
                C["sections"].append(S)
            P["chapters"].append(C); k += 1
        data["parts"].append(P)
    data["meta"]["count"] = total
    json.dump(data, open(out, "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
    print(f"{n} chapitres ; {sum(len(c['sections']) for p in data['parts'] for c in p['chapters'])} sections ; {total} mesures + {subs} sous-mesures = {total + subs} (le livre en annonce 1069)")
    print("\n".join(notes) if notes else "Aucune anomalie.")

if __name__ == "__main__": main(*sys.argv[1:3])
