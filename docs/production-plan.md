# Plan de production — L'Illusion de la frontière

## État au 6 novembre 2026

| Élément | État |
|---|---|
| Script v1 | écrit, 3 472 mots, 20–22 min |
| Vérifications scientifiques | première passe, sources listées |
| Découpage narration | 70 blocs, 21,6 min estimées |
| Storyboard | 26 plans hero, prompts + seeds |
| Images | 26 plans en génération / contrôle |
| Moteur de rendu | opérationnel, 1080p, ~12 fps de capture |
| Preuve visuelle | 7 blocs, 2 min 45, en cours de rendu |
| GitHub Actions | workflow écrit, à tester |
| Voix off | bloquée : enregistrement créateur |
| Musique / SFX | palette écrite, pas encore produits |

## Ce qui peut avancer sans la voix

1. **Contrôle des images** : contact sheet, rejets, régénérations.
2. **Preuve visuelle** : rendu des 7 blocs B00–B06, montage, étalonnage.
3. **Animatique complète** : 70 blocs N001–N070, sous-titres, 960×540, pour valider le rythme.
4. **Actions** : test du workflow sur les 7 blocs, cache Playwright, artefacts.
5. **Décors supplémentaires** : 20–30 plans de coupe (archives, labo, écrans, mains, textures).
6. **Sound design** : repérage des sons, pas de mix sans image verrouillée.
7. **Titre / miniature / description** : à partir du script.

## Ce qui est bloqué par la voix

- Durée réelle de chaque bloc.
- Découpage final des shots dans chaque bloc.
- Rythme du montage (les respirations, les silences).
- Mixage final (la voix est la référence).
- Choix des moments où la musique se retire.

## Décisions à prendre

1. **Voix** : enregistrement réel (recommandé par le brief) ou clone ElevenLabs. Le script est écrit pour une voix humaine ; un clone demande une passe de direction supplémentaire.
2. **Visibilité du dépôt** : privé (2 000 min Actions/mois) ou public (minutes illimitées, mais script et assets exposés). Le dépôt actuel est privé.
3. **4K** : le pipeline est natif 1080p. Les images sont générées en 1536×864 ou 1024×576. Un master 4K serait un upscale ; mieux vaut un 1080p propre, puis un upscale 4K en fin de chaîne si YouTube l'exige.
4. **Musique** : bibliothèque libre de droits, composition originale, ou génération. Le sound design est écrit pour une musique minimaliste, pas pour des cues de bibliothèque.
5. **Format des blocs** : 70 blocs de narration (actuel) ou regroupement en 40 blocs de 30 s. 70 est plus précis pour la voix, 40 est plus rapide à rendre. Le moteur gère les deux.

## Prochaines étapes concrètes

### Sans voix

- [ ] Contrôler les 26 images, régénérer les plans avec du texte parasite.
- [ ] Rendre les 7 blocs en 1080p et assembler `out/proof-look.mp4`.
- [ ] Pousser les assets, lancer le workflow `render` sur `blocks=all`, `scale=0.5`.
- [ ] Rendre l'animatique 70 blocs en 960×540, vérifier le rythme.
- [ ] Générer 20 plans de coupe supplémentaires.
- [ ] Écrire la miniature et les 3 premières secondes.

### Avec la voix

- [ ] Enregistrer les 70 blocs (guide : `films/01-illusion-frontiere/audio/README.md`).
- [ ] `python3 tools/measure_audio.py`
- [ ] `node studio/build_narration_blocks.mjs`
- [ ] Ajuster le mapping shots / blocs.
- [ ] Rendre les 70 blocs en 1080p.
- [ ] Mixage musique + SFX.
- [ ] Étalonnage final, générique, export.

## Estimation

- Preuve visuelle : 1 journée.
- Animatique complète : 1 journée.
- Images supplémentaires : 2–3 jours (génération + contrôle).
- Voix + montage : 3–5 jours.
- Mix + finition : 2 jours.

Soit 7 à 10 jours de travail solo pour un premier 20 minutes, une fois la voix disponible. Le goulot n'est pas le rendu : c'est le contrôle des images et l'écriture.
