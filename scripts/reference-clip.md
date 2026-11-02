# OPS-010 — Vidéo de référence « Friday Deploy » (10 secondes)

État : **candidate pour revue**, pas approuvée visuellement. Sources originales dans
`compositions/culturedevops/intro/index.html` et `scripts/generate_soundtrack.py`.
Aucun asset musical externe, aucune voix tierce ni fichier média stocké dans Git.

| Temps | Plan | Intention sonore | Critère humain |
| --- | --- | --- | --- |
| 0.3–2.4 s | Vendredi 17:59, bouton déploiement, cadre sûr | Pulsation retenue | Lecture immédiate sur écran mobile |
| 2.6–5.4 s | Terminal CI vert puis erreur HTTP 500 | Glitchs croissants | Compréhension en un regard |
| 5.5–7.15 s | Alerte PROD, secousses | Sirène accélérée, mini-silence 7.0–7.18 | Tension puis respiration |
| 7.2–8.9 s | Flash et « Ça marche sur ma machine ! » | Impact + fanfare absurde à 7.18 | Climax net, texte non tronqué |
| 8.9–10 s | ROLLBACK / Culture DevOps | Trombone descendant, fade terminal | Sortie lisible, pas de clic sonore |

## Rendu et validation

Depuis Windows, sur un poste de confiance, après vérification locale des outils :
`pwsh -NoProfile -File scripts/render_and_review.ps1 -Composition intro`.
Le script existant valide le MP4 et construit une planche de contact **hors dépôt public**
avec contrôle d'accès local. Lire le MP4 intégral en plus de la planche, notamment
les coupes à 2.6, 5.5, 7.2 et 8.9 s, l'absence de recadrage et les crêtes audio.

En PR, `ops010-tooling.yml` exécute des tests de tempo/Python et un rendu
éphémère sur `ubuntu-24.04` : HyperFrames `0.8.221` via lockfile, 1920×1080,
30 fps, WAV original 10 s, mux AAC, contrat ffprobe, suppression locale. **Aucun
upload, release, déploiement ni publication** ; logs et assertions seulement.
La CI valide la chaîne technique mais **ne valide pas le rythme perçu ni la qualité visuelle**.

## Dette FFmpeg

Le runner installe FFmpeg depuis les dépôts Ubuntu sans pin : **procédure et
paramètres reproductibles, mais ni octets MP4 identiques ni version binaire
reproductible garantis**. Les références, CVE non résolues et échéance
du 15 novembre 2026 restent dans `scripts/ffmpeg-audit.md`. Cette PR
ne prétend pas corriger FFmpeg. Entrée strictement générée localement ;
aucun MP4 tiers potentiellement piégé. Après un correctif officiel vérifié,
ouvrir un lot distinct pour verrouiller et tester le runtime.
