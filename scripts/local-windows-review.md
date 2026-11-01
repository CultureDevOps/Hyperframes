# OPS-010 — Rendu et revue privée sur Windows (hors CI)

Le script `render_and_review.ps1` automatise un rendu local, l'ajout de la bande-son originale, le contrôle `ffprobe` (1920×1080, 30 fps, AAC, durée) et la génération privée d'une planche de neuf images. **Aucune publication ni téléversement** n'est implémenté.

## Utilisation

Dans PowerShell 5.1 ou 7, depuis la racine du dépôt :

```powershell
.\scripts\render_and_review.ps1 -Composition mvc -PlanOnly
.\scripts\render_and_review.ps1 -Composition intro -PlanOnly
# Quand FFmpeg/FFprobe, Python 3 et Node 22 + npm sont installés localement :
.\scripts\render_and_review.ps1 -Composition intro -OutputDirectory "$HOME\hyperframes-prive"
# Pour inspecter uniquement une vidéo déjà présente sur le poste :
.\scripts\render_and_review.ps1 -Composition mvc -ExistingMp4 "D:\Videos\mvc-explainer.mp4" -OutputDirectory "$HOME\hyperframes-prive"
```

Les trois compositions sont `intro` (10 s), `nounours` (10 s) et `mvc` (35 s). Le mode `-PlanOnly` affiche le plan sans créer de dossier, installer de dépendance, lire de MP4 ou lancer FFmpeg. Un rendu réel exécute `npm ci` et peut télécharger Chrome depuis la chaîne HyperFrames ; utiliser `-SkipInstall` uniquement après un `npm ci` local. Les fichiers finaux sont stockés hors du dépôt public. La bande-son, la vidéo et les planches ne doivent pas être commitées, diffusées ni publiées sans autorisation distincte.

Sur Windows, la destination doit être un **volume NTFS local fixe**, sans jonction ni lien symbolique dans le chemin. Un dossier existant aux ACL permissives est refusé sans modification ; un nouveau dossier feuille reçoit uniquement les droits de l'utilisateur courant et de SYSTEM. Une copie est vérifiée par SHA-256 puis renommée, sans écraser les originaux. Les fichiers `.partial` anciens liés à une interruption ne sont jamais supprimés automatiquement. Les ACL des images produites par l'outil Python sont héritées de leur répertoire ; contrôler les permissions locales en cas d'adaptation.

La CI PR exécute des tests Python, les modes `-PlanOnly` sous Linux/Windows et des tests NTFS sur **octets synthétiques**, sous PowerShell 5.1 et 7 ; elle **n'exécute pas de rendu vidéo**. Ce lot n'atteste ni un rendu complet sur le PC utilisateur, ni la qualité audio/visuelle, ni la sécurité de la baseline FFmpeg (dette CVE indépendante).

**Garde-fou :** la branche `main` conserve des workflows de rendu **manuels uniquement** et sans téléversement d'artefacts. La revue humaine doit porter sur la vidéo locale complète, pas seulement sur les neuf captures.
