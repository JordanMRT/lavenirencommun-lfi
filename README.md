# Le Programme — consultation par mot-clé (PWA)

Site statique (HTML/CSS/JS, sans build) : recherche instantanée + navigation par thèmes, installable sur l'écran d'accueil iPhone.

## Déployer sur GitHub Pages
1. Crée un dépôt GitHub et envoie-y le contenu de ce dossier (à la racine).
2. Settings → Pages → Source : *Deploy from a branch* → `main` / `/ (root)`.
3. Ouvre l'URL fournie dans Safari → Partager → *Sur l'écran d'accueil*.

## Mettre à jour les données
`python3 tools/build_data.py <pages_parties_chapitres> <pages_sections> data/programme.json`
(édition 2027 : adapter `PARTS` et `EDITION` en tête du script ; si le HTML change, ajuster les sélecteurs). Penser à incrémenter `V` dans `sw.js` pour forcer le rafraîchissement du cache.

Après un build : `python3 tools/validate_data.py` (ajouter `--expect N --prev ancien.json` pour comparer les volumes). Les sections manquantes peuvent être fusionnées ensuite avec `tools/fetch_missing.sh` puis `tools/merge_missing.py` (nécessite `beautifulsoup4` et `lxml`, dans un environnement virtuel ignoré par Git).

## Encarts « Comprendre cette mesure » (`data/exemples.json`)
Un bouton facultatif, **fermé par défaut**, sous les mesures qui ont un encart : « En clair », mots à connaître, chiffres sourcés, cas type (illustration) et sources. Principe : on n'affirme un détail que s'il est écrit dans la mesure elle-même ; pas de mise en œuvre ni d'effets prédits.

- **Clé = empreinte du texte exact de la mesure** (`python3 tools/mesure_hash.py 8.4` liste les mesures d'une section avec leur empreinte). Si la mesure change (nouvelle édition, correction), l'empreinte change et l'encart disparaît de l'app jusqu'à sa réécriture. `validate_data.py` signale ces encarts « orphelins ».
- **`etat`** : `brouillon` (jamais affiché au public ; visible en ajoutant `?brouillons=1` à l'adresse, avec un bandeau rouge) ou `relu` (affiché). Passer à `relu` seulement après relecture humaine, avec `relu` (date AAAA-MM-JJ) et au moins une source ; tout chiffre d'un encart relu doit renvoyer à une source.
- **Champs** : `ref` (section), `mesure` (début du texte, pour s'y retrouver), `clair`, `termes` (`mot`, `def`, `src`), `chiffres` (`t`, `src`), `cas` (`t`), `src` (`n`, `l`, `u` en https), `note` (mémo interne, jamais affiché).
- Le pied d'encart est fixe : « Éclairage non officiel, il n'engage pas le programme ni le parti. »
