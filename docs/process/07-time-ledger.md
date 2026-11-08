# 07 — Journal de temps

> Estimations d'après les logs, les runs Actions et l'horloge. Les temps « actif » sont ceux passés à écrire, générer, contrôler, corriger ; les temps « machine » tournent en fond.

## Vue d'ensemble

| Phase | Actif | Machine | Note |
|---|---|---|---|
| Recherche + script + découpage | ~4 h | — | non mesuré précisément |
| 26 images hero | ~20 min | 25 min | 8 steps, 1536/1024 |
| QC + régénérations images | ~30 min | 4 min | scanner + labo |
| Voix 70 blocs | ~2 h | ~2 h | plusieurs relances 404 |
| Musique 6 nappes | ~15 min | 3 min 20 | ACE-Step |
| SFX 18 textures | ~10 min | 8 min 24 | ACE-Step |
| Foley 10 sons | ~20 min | ~10 min | Freesound |
| Depth 26 cartes | ~10 min | ~5 min | Colab T4 |
| 2.5D 26 clips | ~1 h | ~2 h | 156 jobs Actions + 7 Go |
| Blender neural-net | ~1 h | ~1 h | abandonné |
| Motion design | ~2 h | — | 8 insertions |
| Rendu v1/v2 | ~1 h | ~1 h 30 | Actions + downloads |
| Mix / assemblage | ~1 h | ~10 min | voix + musique |
| Miniatures | ~30 min | — | 2 variantes |
| Documentation / passation | ~1 h 30 | — | ce dossier |

## Chronologie approximative

### Jour 1 — Fondations

- Script v1, blocs, storyboard, 26 images.
- Test du look sombre, premier montage 2:45.
- Découverte des débits réels (77 s/image en 1536).

### Jour 2 — Voix et images

- Voix clonée, plusieurs relances Gradio.
- 26 images, QC, régénérations.
- Premier film v1 (26 min) avec images répétées.

### Jour 3 — 2.5D et Blender

- Depth maps, 26 clips 2.5D, 156 jobs Actions, téléchargements.
- Blender neural-net sur T4 : EEVEE CPU, Cycles GPU, abandon.
- Décision : le 2.5D ne sera pas utilisé dans le v2.

### Jour 4 — v2

- 130 images uniques (79 min), motion design, calage.
- Rendu v2, assemblage, miniatures, releases.
- Post-mortem et passation.

## Les postes qui ont explosé

| Poste | Prévu | Réel | Écart |
|---|---|---|---|
| 26 images | ~10 min | 25 min | ×2,5 |
| Voix 70 blocs | ~20 min | ~2 h | ×6 |
| 2.5D | ~30 min | ~3 h | ×6 |
| Blender | ~30 min | ~2 h | ×4 |
| Rendu film | ~20 min | ~1 h 30 | ×4 |

## Ce qui a été rapide

- La musique : 6 nappes en 3 min 20.
- Les SFX : 18 textures en 8 min.
- Le motion design : une fois le kit écrit, 8 insertions en ~2 h.
- Les miniatures : 2 variantes en 30 min.
- Le rendu d'un bloc : 45–60 s en 1080p (images).

## Leçon de planification

Toujours multiplier les estimations « théoriques » par **2 à 4** pour les modèles externes, et par **2** pour les rendus. Le temps réel est dominé par les files d'attente, les reprises et le QC, pas par le calcul.
