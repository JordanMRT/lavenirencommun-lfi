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
Un bouton facultatif, **fermé par défaut**, sous les mesures qui ont un encart. Principe : n'affirmer un détail que s'il est écrit dans la mesure elle-même ; pas de mise en œuvre ni d'effets prédits.

- **Clé = empreinte du texte exact de la mesure** : `python3 tools/mesure_hash.py 8.4` liste les mesures d'une section avec leur empreinte. Si la mesure change (nouvelle édition), l'encart disparaît de l'app ; `validate_data.py` le signale comme « orphelin ».
- **`etat`** : `"relu"` = affiché à tout le monde ; tout le reste (`"brouillon"`…) = masqué, visible seulement avec `?brouillons=1` à la fin de l'adresse (bandeau rouge « Brouillon »). Passer à `"relu"` suffit : aucune date ni autre champ n'est exigé.
- **Tous les champs sont facultatifs** : `clair`, `termes` (`mot`, `def`, `src`), `chiffres` (`t`, `src`), `cas` (un texte, ou `{"t": …, "src": [1]}`, ou une liste de ceux-ci), `src` (`n`, `l`, `u` en https), et `ref`, `mesure`, `note` (mémos internes, jamais affichés). Un encart s'affiche dès qu'il a au moins un bloc (`clair`, `termes`, `chiffres` ou `cas`). Pour retirer un bloc, supprime-le.
- **Un encart mal formé ne casse jamais l'app** : il est ignoré (message dans la console du navigateur). `python3 tools/validate_data.py` ne signale que des avertissements, sauf si le JSON est illisible (il indique alors la ligne et la colonne).
- Le pied d'encart est fixe : « Éclairage non officiel, il n'engage pas le programme ni le parti. »
