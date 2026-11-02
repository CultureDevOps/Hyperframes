# OPS-010 × OPS-028 — Film pédagogique ChatGPT × GitLab

**Statut :** storyboard de production, vidéo non rendue. Source éditoriale : OPS-028 (GitLab IID 27, MR !53 V2). Ne jamais exposer le dépôt privé, URLs ChatGPT directes ou secrets.

## Contrat audiovisuel
- MP4 H.264/AAC, **1280×720**, 30 images/s, 16:9, français.
- Durée pilotée par la narration, cible initiale 5–7 min ; ne pas accélérer artificiellement les plans pour respecter une durée prédéfinie.
- Sous-titres synchronisés et lisibles sur mobile ; narration originale enregistrée/générée avec droits explicites ; musique originale optionnelle, toujours plus faible que la voix.
- Titres en zone sûre (marges 8 %), schémas animés simples, contraste élevé, pas plus de deux idées nouvelles par plan.
- Fil narratif : **problème → échec concret → architecture → mécanisme → démonstration → limites → conclusion**.
- Ne pas inventer d'économie de tokens, de coût ou de temps. Employer « réduction potentielle d'appels spécialisés », avec données mesurées seulement si OPS-022 apporte un jeu comparable.
- Claude Code / GitLab / MCP peut adopter une architecture équivalente. Comparer des **modes d'organisation**, pas prétendre à une exclusivité d'OpenAI.
- Aucune publication, déploiement ou fusion automatique. Sorties CI de revue privée uniquement après validation des effets.

## Storyboard et narration FR (version 0.1)

| ID | Durée indicative | Image / animation | Narration — intention |
|---|---:|---|---|
| S01 | 0:00–0:45 | Trois fenêtres d'agents, compteurs de contexte qui défilent, un chat oublié | « Un projet IA ne se résume pas à une conversation. Quand les sujets se multiplient, où sont les décisions ? Qui sait quel code a été réellement livré ? » |
| S02 | 0:45–1:35 | Trois pistes : CI, sécurité, fonctionnalité ; coupure puis retour sans mémoire fiable | « Une reprise approximative oblige à réexpliquer les faits, relancer des vérifications déjà passées, parfois agir sur le mauvais état. » |
| S03 | 1:35–2:45 | Diagramme HUB → satellites OPS ↔ GitLab, issues, commits, MR, CI | « Le HUB arbitre. Les satellites exécutent des chantiers indépendants. GitLab conserve les décisions, les preuves et la prochaine action. » |
| S04 | 2:45–3:55 | Zoom GitLab : checkpoint SHA, statut MR, pipeline, risques, prochaine action ; boucle animée | « Reprendre ne veut pas dire tout relire : on consulte le dernier checkpoint, on vérifie le delta, on agit, puis on laisse une nouvelle preuve. » |
| S05 | 3:55–4:50 | Deux voies : ChatGPT classique + connecteurs + CI déterministe / Work-Codex pour capacités locales | « Le meilleur appel spécialisé est celui qu'on n'a pas besoin de faire. Les opérations Git et CI accessibles aux connecteurs évitent de mobiliser systématiquement un agent de bureau. Cela ne prouve pas un pourcentage d'économie sans mesures. » |
| S06 | 4:50–5:35 | Claude Code et ChatGPT convergent vers le même registre GitLab | « Claude Code peut aussi suivre ce protocole : ce qui change, c'est l'architecture de coordination, pas une propriété exclusive d'un modèle. » |
| S07 | 5:35–6:10 | Risques : permissions, secrets, nouveaux déclencheurs, attente de l'utilisateur | « Le système ne travaille pas tout seul entre deux conversations. Les droits, les déclenchements et la confidentialité restent à maîtriser. » |
| S08 | 6:10–6:35 | Récapitulatif : un chantier, son dernier SHA, une prochaine action claire | « Le contexte utile devient récupérable. L'IA reste interchangeable ; les faits, eux, restent dans Git. » |

Durées **provisoires** : à recalculer à partir de la voix réelle avec pauses explicatives et transitions. Le tableau n'est **pas** une preuve de rendu MP4.

## Acceptation technique
1. Composition HyperFrames dédiée, sans toucher au court-métrage Friday Deploy ni à sa PR #9.
2. Vérification automatique des scènes et transitions, absence de débordement, lisibilité 720p et trame à 30 fps.
3. Intégration d'une narration effective et d'une bande-son originale/fournie licitement ; mix et sous-titres.
4. Rendu complet + sondes ffprobe (résolution, fps, durée, audio), échantillons de frames et revue humaine avant fusion.
5. Version FFmpeg et provenance attestées ; limiter les médias aux créations propres tant que la dette CVE reste ouverte.
6. Produire un artefact de **revue non public** réellement accessible depuis Android, avec approbation spécifique de l'upload/stockage si requis.

## Source de vérité
OPS-010 GitLab IID 9 ; OPS-028 GitLab IID 27 ; GitHub `CultureDevOps/Hyperframes`. Les exemples affichés dans le film sont synthétiques et non des captures de secrets, de conversations privées ou de pipelines sensibles.
