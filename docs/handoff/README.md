# Passation — L'Illusion de la frontière

**À lire en premier si la conversation a été compactée.** Ce dossier contient l'état du projet, les décisions, les chemins, les commandes et la roadmap. Le dépôt est la source de vérité ; ce dossier est la mémoire du raisonnement.

## En une phrase

Documentaire français de ~26 minutes sur la frontière homme/machine : une archiviste fictive classe les différences entre l'humain et l'IA, jusqu'à découvrir que la frontière passe par elle. Images générées, voix clonée, musique, 2.5D, rendu block par block.

## État au 7 novembre 2026

- Script v1 : 3 472 mots, 70 blocs, 25 min 56 de voix mesurée.
- Voix : 70/70 blocs, clonée avec Fish Audio Drama 3 (référence : `assets/voice-test/reference.wav`).
- Musique : 6 nappes (M00–M05), une par acte.
- SFX : 18 textures générées + 10 sons de foley Freesound.
- Images : 26 images hero + **130 images dédiées v2 en cours** (une par bloc, zéro doublon).
- 2.5D : 26 clips de travelling (depth + Blender), dans `assets/clips/`.
- Film v1 : `out/film-final-intro.mp4` (26:02, 1080p, voix + musique, ouverture 6 s) — images encore répétées.
- Film v2 : en préparation, images uniques + motion design Vox.
- Dépôt public : https://github.com/emilio-n8n/illusion-frontiere
- Releases : `film-final-v1`, `proof-clips-v1`.

## Ordre de lecture

1. `01-project.md` — le film, la thèse, les actes.
2. `02-pipeline.md` — comment on produit, les commandes.
3. `03-assets.md` — voix, musique, SFX, images, licences.
4. `04-decisions.md` — les choix de style et les pièges.
5. `05-roadmap.md` — ce qui reste avant publication.
6. `06-links.md` — liens, endpoints, secrets.
7. `STATE.json` — état machine.

## Process détaillé

Le process complet, le motion design, la génération d'assets et surtout le **post-mortem des erreurs et du temps perdu** sont dans `docs/process/` :

- `README.md`, `01-pipeline.md`, `02-assets.md`, `03-motion.md`
- `04-render-actions.md`, `05-postmortem.md`, `06-checklist.md`, `07-time-ledger.md`

## Règle d'or

Ne jamais casser le thème : archive sombre, écran pâle, teal/bordeaux, grain, typographie mono + Archivo Black. Le motion design Vox doit être **projeté dans ce monde**, pas posé par-dessus comme une infographie claire.
