# Le Programme — consultation par mot-clé (PWA)

Site statique (HTML/CSS/JS, sans build) : recherche instantanée + navigation par thèmes, installable sur l'écran d'accueil iPhone.

## Déployer sur GitHub Pages
1. Crée un dépôt GitHub et envoie-y le contenu de ce dossier (à la racine).
2. Settings → Pages → Source : *Deploy from a branch* → `main` / `/ (root)`.
3. Ouvre l'URL fournie dans Safari → Partager → *Sur l'écran d'accueil*.

## Mettre à jour les données
`python3 tools/build_data.py <pages_parties_chapitres> <pages_sections> data/programme.json`
(édition 2027 : adapter `PARTS` et `EDITION` en tête du script ; si le HTML change, ajuster les sélecteurs). Penser à incrémenter `V` dans `sw.js` pour forcer le rafraîchissement du cache.
