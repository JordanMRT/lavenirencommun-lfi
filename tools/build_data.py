#!/usr/bin/env python3
"""Construit data/programme.json depuis les pages HTML du programme.
Usage: python3 build_data.py <dossier_pages_parties_et_chapitres> <dossier_sections> <sortie.json>
Dépendances: beautifulsoup4, lxml (+ zstandard si des pages sont compressées zstd)."""
import sys, os, re, io, gzip, json, glob
from bs4 import BeautifulSoup

EDITION = {"label": "L'Avenir en commun, édition 2025", "snapshot": "2026-05-03",
           "base": "https://melenchon2027.fr/programme2025/livre"}
# Édition 2027 : adapter PARTS / EDITION (et le sélecteur si la structure HTML change).
PARTS = [("faire-la-revolution-citoyenne", "Faire la révolution citoyenne"),
         ("l-harmonie-des-etres-humains-entre-eux", "L’harmonie des êtres humains entre eux"),
         ("l-harmonie-des-etres-humains-avec-la-nature", "L’harmonie des êtres humains avec la nature"),
         ("ordonner-le-monde", "Ordonner le monde")]

def read(path):
    b = open(path, "rb").read()
    if b[:2] == b"\x1f\x8b": b = gzip.decompress(b)
    elif b[:4] == b"\x28\xb5\x2f\xfd":
        import zstandard; b = zstandard.ZstdDecompressor().stream_reader(io.BytesIO(b)).read()
    return BeautifulSoup(b.decode("utf-8", "replace"), "lxml")

def txt(el): return " ".join(el.get_text(" ", strip=True).split())

def main(pages, secs, out):
    titles, parts = {}, []
    for slug, ptitle in PARTS:
        m = read(f"{pages}/{slug}.html").find("main"); chaps = []
        for a in m.find_all("a"):
            r = re.search(r"chapitre(\d+)(?:/s(\d+))?$", a["href"])
            if not r: continue
            c, s = int(r[1]), r[2] and int(r[2])
            titles[(c, s)] = re.sub(r"^Chapitre \d+\s*:\s*", "", txt(a))
            if not s and c not in chaps: chaps.append(c)
        parts.append((ptitle, chaps))
    for f in glob.glob(f"{pages}/chapitre*.html"):  # sommaires de chapitres : titres plus fiables
        m = read(f).find("main"); c = int(re.search(r"chapitre(\d+)", f)[1])
        titles[(c, None)] = re.sub(r"^Chapitre \d+\s*:\s*", "", txt(m.find("h1")))
        for i, a in enumerate(m.select("nav.tdm a"), 1): titles[(c, i)] = txt(a)
    nsec = {}
    for (c, s) in titles:
        if s: nsec[c] = max(nsec.get(c, 0), s)
    data = {"meta": {**EDITION, "missing": []}, "parts": []}; total = 0
    for ptitle, chaps in parts:
        P = {"title": ptitle, "chapters": []}
        for c in chaps:
            C = {"n": c, "title": titles.get((c, None), f"Chapitre {c}"), "sections": []}
            for s in range(1, nsec.get(c, 0) + 1):
                S = {"n": s, "title": titles.get((c, s), f"Section {s}"), "intro": "", "items": []}
                f = f"{secs}/chapitre{c}_s{s}.html"; m = os.path.exists(f) and read(f).find("main")
                box = m and m.find("section", class_="contenu")
                if not box: S["missing"] = True; data["meta"]["missing"].append(f"chapitre{c}/s{s}")
                else:
                    h1 = m.find("h1"); S["title"] = txt(h1) if h1 else S["title"]
                    for el in box.find_all(["p", "div"], recursive=False):
                        k = el.get("class") or []
                        if el.name == "p": S["intro"] = (S["intro"] + " " + txt(el)).strip()
                        elif "mesure-cle" in k: S["items"].append({"t": txt(el), "k": 1})
                        elif "mesure" in k: S["items"].append({"t": txt(el), "k": 0})
                        elif "sous-mesure" in k and S["items"]: S["items"][-1].setdefault("sub", []).append(txt(el))
                    total += len(S["items"])
                C["sections"].append(S)
            P["chapters"].append(C)
        data["parts"].append(P)
    data["meta"]["count"] = total
    json.dump(data, open(out, "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
    print(total, "mesures;", len(data["meta"]["missing"]), "sections manquantes:", data["meta"]["missing"])

if __name__ == "__main__": main(*sys.argv[1:4])
