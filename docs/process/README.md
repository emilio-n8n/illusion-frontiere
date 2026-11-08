# Process de production — chaîne IA / L'Illusion de la frontière

Ce dossier décrit **comment on a réellement produit** le film, pas la version idéalisée. Il contient le pipeline, la génération d'assets, le motion design, le rendu, et surtout le **post-mortem des erreurs et du temps perdu**.

## Ordre de lecture

1. `01-pipeline.md` — la chaîne complète, du script à la release.
2. `02-assets.md` — images, depth, 2.5D, voix, musique, SFX, QC.
3. `03-motion.md` — le kit motion design Vox, son intégration et ses pièges.
4. `04-render-actions.md` — le moteur de blocs, GitHub Actions, assemblage.
5. `05-postmortem.md` — **les erreurs, leur coût, leur correction, la règle pour la suite.**
6. `06-checklist.md` — la checklist réutilisable pour la prochaine vidéo.
7. `07-time-ledger.md` — le temps réel passé, poste par poste.

## Les trois règles qui résument tout

1. **Une image unique par bloc, dès le début.** Ne jamais monter 70 blocs avec un pool de 26 images.
2. **La voix est le chemin critique.** Un endpoint temporaire qui tombe coûte des heures ; il faut un modèle local ou une API stable, et générer par lots reprenables.
3. **Ne pas construire une technologie avant d'en avoir besoin.** Le 2.5D et Blender étaient beaux, mais le montage v2 n'utilise pas les 26 clips : c'était du temps en grande partie perdu.

## Chiffres du projet

- Script : 3 472 mots, 70 blocs, 25 min 56 de voix.
- Images : 26 hero + 130 uniques v2 = 156 images.
- Voix : 70 prises clonées.
- Musique : 6 nappes.
- SFX : 18 textures + 10 foley.
- Film : 26 min 02, 1080p, 24 fps, ~580 Mo.
- Motion design : 8 insertions.
- Dépôt : https://github.com/emilio-n8n/illusion-frontiere
