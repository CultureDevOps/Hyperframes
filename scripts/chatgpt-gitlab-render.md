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
## Voix neuronale française (nouveau lot, non publiée)
La voix **Piper Siwis medium (fr_FR, 22050 Hz)** remplace eSpeak par défaut.
Écoute humaine obligatoire : aucune qualité ne peut être garantie par un test de fichiers.
Le modèle n'est jamais committé ni téléchargé implicitement pendant le rendu.

Moteur : `piper-tts==1.8.0` (GPL-3.0-or-later).
Modèle : `rhasspy/piper-voices` révision
`d5de91c972ba5a13cea0e77a63fda1623faac2c1`,
`fr/fr_FR/siwis/medium/fr_FR-siwis-medium.onnx`,
SHA-256 `641d1ab097da2b81128c076810edb052b385decc8be3381814802a64a73baf99`.
Le modèle et sa configuration .onnx.json doivent rester côte à côte.
Licence des enregistrements d'entraînement : CC BY 4.0.
**Attribution** : SIWIS French Speech Synthesis Database (2017),
Junichi Yamagishi, Pierre-Edouard Honnet, Philip Garner et Alexandros Lazaridis,
University of Edinburgh ; contributeurs Piper. Les droits de chaque modèle et du moteur
sont à vérifier séparément avant diffusion extérieure.

Après installation locale explicite de Piper et téléchargement depuis la révision épinglée :
```sh
python -m pip install 'piper-tts==1.8.0'
python scripts/render_chatgpt_gitlab.py \
  --voice piper --piper-model /dossier/prive/fr_FR-siwis-medium.onnx \
  --output /dossier/prive/film-neural.mp4
```
Une seule instance du modèle est chargée pour toutes les phrases.
Le montage, les scènes et les sous-titres sont recalés sur les durées WAV mesurées.
Si la voix sort des 5–7 minutes visées, elle n'est pas accélérée artificiellement :
une revue éditoriale est nécessaire. La fenêtre technique de sécurité autorise
4–10 minutes pour préserver les durées déterminées par la narration.
L'ancien moteur est conservé uniquement pour comparaison avec `--voice espeak`.
La CI exécute un smoke de voix française sur **une phrase fictive**, supprime le WAV,
et n'exporte aucun média ni aucun modèle.
