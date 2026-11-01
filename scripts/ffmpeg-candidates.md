# OPS-010 — Options FFmpeg et runners GitHub (01/11/2026)

**Critère :** comparer des sources gratuites officielles, sans prétendre que
toutes les vulnérabilités sont corrigées. La dette Ubuntu est enregistrée dans
ffmpeg-security-policy.json ; elle reste non résolue.

| Solution | Disponibilité | Observations et limites |
| --- | --- | --- |
| Ubuntu 24.04 archive universe | Paquet 7:6.1.1-3ubuntu5, runner ubuntu-24.04 vérifié | Baseline reproductible mais antérieure aux corrections de USN-8915-1. Ne pas déclarer la base sûre. |
| Ubuntu 24.04 ESM Apps | 7:6.1.1-3ubuntu5+esm15 (USN-8915-1) | Corrigé pour cet avis, mais via Ubuntu Pro. Entitlement, identité et éventuel coût hors mandat ; ne pas activer. |
| Ubuntu 26.04 universe | Archive 7:8.0.1-3ubuntu2, runner standard ubuntu-26.04 disponible depuis le 17/09/2026 | L'avis USN-8915-1 indique lui aussi +esm5. Numéro majeur plus récent != sécurité acquise. |
| Debian 13 Trixie | Archive officielle stable/security 7:7.1.5-0+deb13u1 | Correctifs DSA-6073/6268/6361, mais d'autres CVE ouvertes dans le tracker Debian. Nécessite une image Debian officielle épinglée par digest sur runner GitHub, contrôle de provenance et de compatibilité Chrome/FFmpeg. **Non exécuté dans ce lot.** |
| Source amont et distributions statiques | FFmpeg source officielle ou binaires tiers | Construire et vérifier signatures/hachages et dépendances ; pas de provenance et maintenance automatiques ; non adopté. |

Sources officielles (consultées le 01/11/2026) :
- https://ubuntu.com/security/notices/USN-8915-1
- https://packages.ubuntu.com/noble/ffmpeg
- https://packages.ubuntu.com/resolute/ffmpeg
- https://github.blog/changelog/2026-09-17-ubuntu-26-generally-available-and-latest-migration/
- https://docs.github.com/en/actions/how-tos/write-workflows/choose-where-workflows-run/choose-the-runner-for-a-job
- https://packages.debian.org/trixie/ffmpeg
- https://security-tracker.debian.org/tracker/source-package/ffmpeg
- https://security-tracker.debian.org/tracker/DSA-6073-1
- https://security-tracker.debian.org/tracker/DSA-6268-1
- https://security-tracker.debian.org/tracker/DSA-6361-1
- https://canonical.com/legal/ubuntu-pro/personal

Le job PR probe-ubuntu-ffmpeg utilise deux runners GitHub gratuits,
ubuntu-24.04 et ubuntu-26.04. Il actualise les index APT **uniquement sur
le runner jetable** puis lit apt-cache policy sans installation de paquet.
Sa sortie security_status=NOT_ASSESSED est obligatoire ; le candidat disponible
ne prouve ni correctif CVE, ni compatibilité d'un futur rendu. Aucun artefact,
Docker privilégié ou vidéo n'est créé par cette sonde.

**Décision provisoire :** garder les rendus actuels inchangés (PR Draft) ;
étudier Debian 13 en pilote isolé après revue de l'image officielle et de
son digest, des CVE restantes et des bibliothèques ; tester ensuite les
3 rendus éphémères avec leurs métadonnées, musiques et contrôles Chrome.
Ne jamais mélanger des dépôts Debian et Ubuntu, activer Ubuntu Pro ni
publier une vidéo sans autorisation séparée.

## 01/11/2026 — réévaluation CVE ciblée et décision de sécurité

Sources éditeur recoupées :
- [Ubuntu USN-8915-1](https://ubuntu.com/security/notices/USN-8915-1) :
  `7:6.1.1-3ubuntu5+esm15` (noble) et `7:8.0.1-3ubuntu2+esm5`
  (resolute) annoncés dans **Ubuntu Pro / ESM Apps** pour les CVE
  **de cet avis seulement**. Aucun droit Ubuntu Pro n'a été créé ou activé.
- [Ubuntu CVE-2026-107678](https://ubuntu.com/security/CVE-2026-107678) :
  statut FFmpeg **« Needs evaluation »** pour noble 24.04 et resolute 26.04 ;
  ceci ne signifie ni « corrigé » ni « confirmé vulnérable » par Ubuntu.
- [Debian CVE-2026-107678](https://security-tracker.debian.org/tracker/CVE-2026-107678) :
  Trixie **`7:7.1.5-0+deb13u1` vulnérable**, correction reportée ;
  exhaustion de pile via les boîtes PSSH du démultiplexeur MP4/MOV.
- [Debian DSA-6361-1](https://security-tracker.debian.org/tracker/DSA-6361-1) :
  ce **même** paquet corrige les CVE listées pour cet avis, sans effacer
  les vulnérabilités ouvertes indépendantes.
- [Debian FFmpeg](https://packages.debian.org/trixie/ffmpeg) :
  version du paquet 13 stable confirmée.

**Conclusion vérifiable :** ni Ubuntu 26.04 ni Debian 13 n'apportent
aujourd'hui une preuve de remédiation globale, et le correctif ESM
d'USN-8915-1 ne doit pas être interprété comme traitant CVE-2026-107678.
Aucun basculement de l'exécuteur de rendu existant n'est autorisé.
L'utilisation de MP4 externes non fiables reste hors périmètre ; les
rendus CI manipulent des MP4 générés localement sur runners jetables,
ce qui réduit mais n'annule pas le risque de dépendances compromises.

Le manifeste `scripts/ffmpeg-security-policy.json` mémorise explicitement
la distinction entre « vulnerable » (Debian) et « needs_evaluation »
(Ubuntu). Le test obligatoire `audit_ffmpeg_security.py` échoue si
ces observations sont silencieusement requalifiées en « fixed » ou
si le document prétend que la vulnérabilité MP4 est résolue.
C'est un **contrôle de cohérence d'un relevé daté, pas une interrogation
continue du tracker** ni un scanner de CVE. Le prochain réexamen reste
prévu avant le 15/11/2026. Les sondes APT Ubuntu et Debian **sans installation**
et les trois rendus techniques éphémères restent inchangés.
