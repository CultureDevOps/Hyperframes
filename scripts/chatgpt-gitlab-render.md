# OPS-010 — Film 720p : état et limites

**Éditorial :** adaptation publiable du storyboard OPS-010 et de la présentation
OPS-028 V2.2. Tous les exemples sont fictifs. Aucune URL privée, historique,
valeur de secret ou état opérationnel réel ne figure dans les scènes.

**Source vidéo :** `compositions/culturedevops/chatgpt-gitlab/index.html`,
`narration.json` et `scripts/render_chatgpt_gitlab.py`. Racine de la composition
HyperFrames déclarée en 1280×720, 30 FPS. Le rendu de revue de cette livraison
emploie Chromium pour capturer trois états animables par chapitre de **cette**
composition ; un montage FFmpeg à 30 FPS maintient les plans selon les durées
mesurées de la narration. **Ce n'est pas un export natif `hyperframes render`.**

**Voix :** synthèse locale `espeak -v fr -s 156`. Voix non humaine, à réenregistrer
ou remplacer sous licence claire avant toute sortie officielle.
**Musique :** oscillateurs synthétiques originaux, mixés à faible niveau sous la voix.
**Sous-titres :** SRT synchronisé phrase par phrase, intégré à l'image, et
fichier SRT séparé. Contenu original, sans média externe.

Commande depuis un environnement Linux isolé avec `python3`,
`playwright`, Chromium local, espeak et FFmpeg :

```
python3 scripts/render_chatgpt_gitlab.py --output /chemin/prive/film.mp4
```

Le script refuse une sortie dans le checkout Git public. Le fichier est privé,
non téléversé à GitHub ; les 24 images de travail restent dans un dossier temporaire.
Le contrôle `ffprobe` valide H.264/AAC, 1280×720, 30 FPS et une durée de 5–7 min.

**Reproductibilité :** scripts et narration versionnés, mesures et dépendances
locales observées ; ni capture Chrome/FFmpeg, ni voix espeak, ni octets binaires
ne sont verrouillés par checksum de distribution. Aucun gain chiffré inventé.
CVE/risque FFmpeg non remédié, entrée média fabriquée localement uniquement.

**CI PR :** `ops010-explainer.yml`, tests structurels sans publication ni
vidéo ; le rendu complet et sa revue audio/visuelle ont lieu séparément.
Aucune sortie média dans les GitHub Actions publics.