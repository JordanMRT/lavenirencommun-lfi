# Mise à jour vers l'édition 2027 : checklist

Approche : **l'édition 2027 remplace la 2025** dans l'app, sans sélecteur d'édition. La 2025 reste récupérable grâce à l'étiquette Git `edition-2025`.
Principe : on prépare tout hors ligne, on valide, et on ne touche à `main` (donc au site en ligne) qu'à la fin.

## Points de vigilance (ce qui peut casser)

| Risque | Pourquoi | Parade |
|---|---|---|
| Encarts masqués | Un encart est lié à l'empreinte du texte exact de sa mesure : si la mesure change, il disparaît | `diff_editions.py` donne un verdict par encart (étape 5) |
| Mauvaises couleurs ou silhouettes | `PAL` et `MOTIF` (dans `index.html`) sont rangés par numéro de chapitre | Tableau de correspondance des chapitres (étape 5), puis étape 7 |
| Mise à jour du cache qui échoue | `sw.js` installe tous les fichiers de `PRE` d'un coup : si un seul manque, rien ne s'installe | Ne pas renommer `data/programme.json`, `data/exemples.json`, etc. |
| Sources qui disparaissent | Les pages web 2025 ne sont déjà plus en ligne (redirigées vers l'accueil) | Étape 1 : archiver avant tout |
| Texte périmé dans le pied de page | « Prochaine mise à jour : le 6 novembre 2026 » est écrit en dur dans `foot()` (`index.html`) | Étape 8 |
| Liens profonds | `#/c/N/sM` repose sur la numérotation | Acceptable ; à connaître |
| Balises de suivi perdues | Google Tag (GA4) et vérification Search Console sont dans le `<head>` de `index.html` ; l'étiquette `edition-2025` date d'avant leur ajout | Ne jamais restaurer `index.html` depuis l'étiquette ; contrôle à l'étape 10 |

## Avant le jour J (une seule fois)

```bash
cd ~/Documents/GitHub/lavenirencommun-lfi
git pull
git tag -a edition-2025 -m "Dernier état de l'édition 2025 avant l'import 2027"
git push origin edition-2025
```

L'étiquette ne change rien au site en ligne. Pour retrouver l'ancien fichier : `git show edition-2025:data/programme.json`.
Garde aussi, **hors du dépôt**, une copie sauvegardée (iCloud, par exemple) du PDF `aec2025.pdf` et du dossier `pages_manquantes`.
Vérifie que l'environnement fonctionne : `source .venv/bin/activate && python3 tools/validate_data.py` doit répondre `=> OK`.

## Le jour J

### 1. Archiver les sources avant tout
Dans un dossier hors dépôt, par exemple `~/Documents/sources-programme-2027/` : le PDF de l'édition s'il existe (`curl -L -o …` ou téléchargement dans Safari) et les pages HTML des parties, chapitres et sections si l'édition est publiée en pages web.
Ne rien supposer : note l'adresse exacte de chaque fichier récupéré.

### 2. Travailler sur une branche
```bash
git switch -c edition-2027
git show edition-2025:data/programme.json > /tmp/programme-2025.json
```

### 3. Construire les nouvelles données (sans écraser l'ancien fichier)
- **Pages web** : adapter `EDITION` et `PARTS` en tête de `tools/build_data.py` (libellé, date de capture, adresse de base, parties), puis
  `python3 tools/build_data.py <pages_parties_chapitres> <pages_sections> /tmp/programme-2027.json`.
  Si le HTML a changé, il faudra ajuster les sélecteurs dans `parse_section`.
- **PDF** : on écrit un extracteur sur le texte du PDF et on contrôle chaque mesure contre ce texte (méthode utilisée pour 7.6 et 7.8).
- Sections récupérées après coup : `tools/merge_missing.py` (voir README).

### 4. Valider
```bash
python3 tools/validate_data.py /tmp/programme-2027.json --expect 1069 --prev /tmp/programme-2025.json
```
Les ERREURS doivent être à zéro. Les AVERTISSEMENTS se lisent un par un (mesures collées, texte très court, chapitre sans palette…).
Le chiffre annoncé est 1 069 mesures : un écart est un signal à expliquer, pas forcément une erreur.

### 5. Comparer les deux éditions
```bash
python3 tools/diff_editions.py /tmp/programme-2025.json /tmp/programme-2027.json --rapport ~/Documents/sources-programme-2027/rapport.md
```
À lire dans l'ordre :
1. **Bilan** : parts d'identiques, modifiées, supprimées et nouvelles.
2. **Correspondance des chapitres** : tout chapitre `RENUMÉROTÉ`, `titre changé` ou `nouveau` demande une décision à l'étape 7.
3. **Encarts** : `INTACTS` (rien à faire), `À RÉVISER` (voir étape 6), `SANS SUITE`.

### 6. Traiter les encarts
- **Intacts** : rien.
- **À réviser** : le rapport montre les mots changés. Relis le nouveau texte de la mesure : si l'encart reste exact, on lui donne la nouvelle empreinte (copie d'abord `cp /tmp/programme-2027.json data/programme.json` sur la branche, puis `python3 tools/mesure_hash.py N.M`) ; sinon on le réécrit, en restant strictement dans le texte de la mesure (règles du README).
- **Sans suite** : on les laisse (ils sont masqués, c'est sans danger) ou on les supprime.

### 7. Palettes et silhouettes
Si un chapitre est renuméroté, ajouté ou supprimé : adapter `PAL` et `MOTIF` pour que **chaque thème garde sa palette et sa silhouette**, en faisant correspondre par titre et non par numéro. Les affiches elles-mêmes ne se modifient pas. Un chapitre nouveau a besoin d'une entrée dans `PAL` et dans `MOTIF` (le validateur le signale).

### 8. Textes à changer
- `index.html`, fonction `foot()` : retirer ou remplacer « Prochaine mise à jour : le 6 novembre 2026 (édition 2027) ».
- `meta.label` vient du build (`EDITION`) : vérifier qu'il affiche bien « édition 2027 ».
- `README.md` : mentions de 2025 si nécessaire.

### 9. Cache
Dans `sw.js`, incrémenter `V` (actuellement `programme-v16`, donc `programme-v17` ou plus). Ne jamais le baisser, même pour un retour arrière.

### 10. Tester en local
```bash
cp /tmp/programme-2027.json data/programme.json
python3 tools/validate_data.py
python3 -m http.server 8000
grep -n "G-RYTGZEYJ04\|google-site-verification" index.html   # les trois lignes doivent être présentes
```
Ouvrir `http://localhost:8000` : recherche, chaque chapitre, quelques sections, les encarts, `#/c/N/sM`, le pied de page. Le test hors ligne se fait sur l'ordinateur (Safari, onglet Réseau) ou après la mise en ligne.

### 11. Livrer
Un seul `.patch`, vérifié sur clone propre :
```bash
git diff main edition-2027 > edition-2027.patch
cd /tmp && rm -rf verif && git clone https://github.com/JordanMRT/lavenirencommun-lfi verif && cd verif
git apply --check ~/…/edition-2027.patch && git apply ~/…/edition-2027.patch && python3 tools/validate_data.py
```
Puis fusion dans `main` et envoi.

### 12. Après la mise en ligne
Sur l'iPhone : ouvrir l'app en ligne, la fermer complètement et la rouvrir. Contrôler le libellé de l'édition, le nombre de mesures, une recherche, un encart.

## Retour arrière
```bash
git revert <commit_de_l_import>      # ou : git checkout edition-2025 -- data
```
Attention : ne pas restaurer `index.html` depuis l'étiquette (il perdrait les balises GA4 et Search Console) ; si `index.html` doit revenir en arrière, utiliser `git revert`.
Dans les deux cas, **incrémenter `V`** dans `sw.js` avant l'envoi pour que les appareils reprennent l'état restauré.
