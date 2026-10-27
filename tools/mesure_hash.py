#!/usr/bin/env python3
"""Empreinte d'une mesure : relie un encart de data/exemples.json au texte EXACT de la mesure.
Si le texte change (nouvelle édition, correction), l'empreinte change et l'encart disparaît de l'app
jusqu'à sa réécriture : un encart périmé ne peut pas rester affiché.

Même calcul que la fonction hash() de index.html (FNV-1a 32 bits sur le texte en UTF-8) : ne pas modifier l'un sans l'autre.

Usage : python3 tools/mesure_hash.py 8.4        liste les mesures de la section 8.4 avec leur empreinte (et indice)
        python3 tools/mesure_hash.py --tout     toutes les mesures"""
import sys, re, json, signal, unicodedata

ESPACES = re.compile(r"[ \t\n\r\f\v\u00a0\u2000-\u200a\u202f\u205f\u3000]+")

def mesure_hash(t, sub=()):
    txt = "\n".join(ESPACES.sub(" ", unicodedata.normalize("NFC", x)).strip() for x in [t, *sub])
    h = 2166136261
    for b in txt.encode("utf-8"):
        h = ((h ^ b) * 16777619) & 0xFFFFFFFF
    return f"{h:08x}"

def mesures(data):
    for p in data["parts"]:
        for c in p["chapters"]:
            for s in c["sections"]:
                for i, it in enumerate(s["items"]):
                    yield c["n"], s["n"], i, it

if __name__ == "__main__":
    if hasattr(signal, "SIGPIPE"): signal.signal(signal.SIGPIPE, signal.SIG_DFL)  # pas d'erreur avec | head
    data = json.load(open("data/programme.json", encoding="utf-8"))
    arg = sys.argv[1] if len(sys.argv) > 1 else "--tout"
    for c, s, i, it in mesures(data):
        if arg == "--tout" or arg == f"{c}.{s}":
            print(f"{c}.{s}#{i}  {mesure_hash(it['t'], it.get('sub', []))}  {'★ ' if it.get('k') else ''}{it['t'][:90]}")
