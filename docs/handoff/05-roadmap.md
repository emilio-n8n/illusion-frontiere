# Roadmap — ce qui reste avant publication

## 1. Terminer le film v2 (images uniques)

- [ ] Finir les 130 images `Nxxx-A/B` (génération en cours, ~87/130 au dernier point).
- [ ] Contrôler les images : texte parasite sur écrans, anatomies, doublons de motif.
- [ ] `SUBTITLES=0 node studio/build_narration_blocks.mjs` (utilise `narration-map.json`).
- [ ] `node studio/check_assets.mjs narration`.
- [ ] Committer les 130 images + les blocs narration.
- [ ] Lancer le workflow `render` (`dir=narration`, `blocks=all`, `scale=1`).
- [ ] Récupérer `film-silent`, préfixer `out/intro.mp4`, muxer `out/audio/mix-lead.wav`.
- [ ] Release `film-final-v2`.

## 2. Motion design Vox

- [ ] Implémenter les types dans `studio/render.html` : `number`, `dots`, `bars`, `brackets`, `timeline`, `frontier`, `redact`, `quote`, `diagram`.
- [ ] Créer `films/01-illusion-frontiere/storyboard/motion.json` (mapping bloc → graphiques).
- [ ] Injecter `motions` dans les blocs narration.
- [ ] Vérifier 4–6 insertions : 86 milliards, 800 000/160 000, H.M. 1953, Turing 1950, frontière, « conscient : présumé ».
- [ ] Re-rendre les blocs concernés, pas tout le film.

## 3. SFX et mix final

- [ ] Placer 15–25 sons : projecteur, papier, tiroirs, pas, tampon, néon, pluie, IRM, cœur.
- [ ] Baisser la musique sous la voix (déjà duckée), ajouter des respirations de silence.
- [ ] Master -14 LUFS, -1 dBTP ; vérifier au casque et sur téléphone.
- [ ] Crédits Freesound dans le générique.

## 4. Finition éditoriale

- [ ] Relire le fact-check : DishBrain (800k, « sentience »), FinalSpark (16 organoïdes, 160k), Anthropic (model welfare, date).
- [ ] Sous-titres `.srt` français (et éventuellement anglais).
- [ ] Générique : sources, images IA, musique, polices, Freesound.
- [ ] Miniature : Bureau, écran pâle, une touche rouge ; tester la lisibilité en petit.
- [ ] Titre YouTube, description, chapitres, sources, mentions IA.
- [ ] Déclaration « contenu synthétique » si applicable.
- [ ] Contrôle qualité : noirceur, banding, compression YouTube, audio.

## 5. Publication

- [ ] Décider la date et l'heure.
- [ ] Créer la chaîne/logo/bannière si pas fait.
- [ ] Upload, miniature, chapitres, carte de fin, commentaire épinglé avec sources.
- [ ] Surveiller les premières 48 h (rétention, commentaires).

## Dette technique

- `tools/fetch_chunks.mjs` : les artefacts Actions sont lents à télécharger ; préférer un zip par plan à l'avenir.
- `studio/mix_audio.mjs` : le `--lead` n'a pas été fiable ; l'ouverture est construite manuellement. À corriger pour le prochain film.
- Les clips 2.5D ne sont pas utilisés dans le v2 ; prévoir une version « hero » ou des inserts.
- Le rendu local est limité à 1 Chromium ; utiliser Actions pour tout rendu > 2 min.
