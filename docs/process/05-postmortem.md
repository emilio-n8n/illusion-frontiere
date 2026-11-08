# 05 — Post-mortem : erreurs, pertes de temps, règles

> Ce document est volontairement dur. Il ne sert à rien de raconter que tout s'est bien passé : le film est bon, mais une grande partie du temps est partie dans des impasses, des doublons et des outils instables. Les durées sont des estimations d'après les logs et l'horloge des runs.

## Résumé exécutif

- Le film v2 est livré (26 min, 1080p, 130 images uniques, motion, voix, musique).
- Mais **~40 à 50 % du temps de production** a été consommé par des erreurs évitables.
- Les trois plus gros postes : **les doublons d'images**, **l'instabilité de la voix**, et **le pipeline 2.5D/Blender non utilisé**.
- La bonne nouvelle : chaque erreur a une correction simple et réutilisable, listée à la fin.

## Top 10 des pertes de temps

| # | Poste | Coût estimé | Cause |
|---|---|---|---|
| 1 | Doublons d'images → 130 images à refaire | ~2 h | 160 emplacements pour 22 images uniques |
| 2 | Voix : tunnels 404, relances, lenteur | ~2 h 30 | Endpoint Gradio temporaire, RTF 3,6–8 |
| 3 | 2.5D : 26 clips, 156 jobs, 7 Go d'artefacts | ~3 h | Pipeline construit avant le montage, non utilisé en v2 |
| 4 | Blender neural-net sur T4 | ~2 h | EEVEE CPU 4 min/frame, Cycles 44 s/frame, abandonné |
| 5 | Actions : ffmpeg/apt, 7 jobs timeout | ~1 h 30 | ffmpeg absent, apt lent, timeout 40 min |
| 6 | Téléchargement des 156 chunks | ~1 h 30 | `gh run download` lent, erreurs « file exists », 7 Go |
| 7 | Blender 5.2 : bloom, Composite, EGL | ~1 h 30 | API changée, EEVEE headless sans GPU |
| 8 | QC images / texte parasite | ~30 min | Labels sur scanner et moniteur |
| 9 | `cp -n` : vieux mp4 540p conservés | ~30 min | Mux avec les mauvais blocs |
| 10 | Mix : mapping musique, 192 kHz mono, lead | ~30 min | Sous-chaînes, format de sortie, adelay |

## A. Stratégie et choix d'outils

### A1. Le skill Higgsfield payant

- **Symptôme** : téléchargement et lecture d'un skill `vox-motion-graphics` qui s'appuie sur un MCP Higgsfield payant (30–45 crédits par clip de 10 s).
- **Cause** : le skill est séduisant sur le papier, mais le MCP n'est pas installé et le coût est incompatible avec une chaîne industrielle.
- **Coût** : ~30–45 min de lecture/analyse.
- **Correction** : on a gardé la grammaire (prompts, structure) et construit un moteur local.
- **Règle** : vérifier la disponibilité et le coût d'un outil **avant** de lire 200 lignes de spec.

### A2. `rembg` pour découper une silhouette

- **Symptôme** : `rembg` a timeout à 300 s et laissé un `ship.png` de 0 octet.
- **Cause** : segmentation lourde pour un besoin simple (silhouette).
- **Coût** : ~10 min + un asset cassé.
- **Correction** : masque de luminance sur une photo réelle, puis silhouette alpha.
- **Règle** : pour une silhouette, un masque de luminance suffit ; ne pas sortir l'artillerie.

### A3. Le 2.5D avant le montage

- **Symptôme** : 26 clips de travelling générés, 156 jobs Actions, ~7 Go de PNG téléchargés, puis **non utilisés** dans le film v2.
- **Cause** : on a construit la technologie avant de savoir quels plans seraient répétés et quel montage serait retenu.
- **Coût** : ~3 h.
- **Correction** : les 130 images uniques ont remplacé les 26 clips dans le montage.
- **Règle** : **picture lock d'abord**, 2.5D ensuite, et seulement pour 4–6 plans hero.

### A4. Blender neural-net sur T4

- **Symptôme** : scène procédurale construite, EEVEE headless à 4 min/frame, Cycles GPU à 44 s/frame, puis abandon.
- **Cause** : un plan de 6 s ne justifiait pas une usine 3D.
- **Coût** : ~2 h.
- **Correction** : le plan B01-S03 est couvert par une image + mouvement de caméra.
- **Règle** : ne pas construire un pipeline 3D pour un seul plan ; le 2.5D ou une image animée suffit.

### A5. Cible 15 min vs film 26 min

- **Symptôme** : le brief parlait de 15 min, la voix mesurée fait 25 min 56.
- **Cause** : estimation à 165 mots/min, alors que la voix clonée tourne à ~123 mots/min.
- **Coût** : ajustements de plan, mais l'utilisateur a validé 35 min.
- **Règle** : mesurer la voix **avant** de promettre une durée ; la durée appartient à la voix.

## B. Images

### B1. Débit réel du endpoint

- **Symptôme** : 1536 px à ~77–85 s/image, alors que l'annonce parlait de 21 s.
- **Cause** : GPU partagé, résolution, queue.
- **Coût** : 26 images en 25 min ; 130 images en 79 min.
- **Règle** : mesurer 3 images, puis planifier ; ne pas promettre un débit théorique.

### B2. Tunnels Gradio qui expirent

- **Symptôme** : 404 en plein batch ; 26/70, 53/70, 70/70 selon les runs.
- **Cause** : `*.gradio.live` temporaire, notebook redémarré.
- **Coût** : relances, attentes, blocs perdus.
- **Correction** : reprise sans `--force`, URL en argument.
- **Règle** : pour la production, un modèle local ou une API stable ; le tunnel ne doit servir qu'aux tests.

### B3. Texte généré dans les images

- **Symptôme** : labels sur le scanner cérébral, UI sur le moniteur de labo, texte sur l'écran de téléphone.
- **Cause** : les modèles ajoutent du texte sur les écrans même avec « no text ».
- **Coût** : 2 régénérations + re-render.
- **Correction** : prompts « blank screen, no labels, no UI » + negative renforcé ; ou éviter les écrans.
- **Règle** : tout écran est un risque de texte ; le vérifier avant de valider l'image.

### B4. Les doublons d'images — le pire poste

- **Symptôme** : 160 emplacements de plans pour 22 images uniques, jusqu'à 15 répétitions (B06-S02, B00-S01, B00-S02…).
- **Cause** : le premier mapping réutilisait 26 images hero pour 70 blocs.
- **Coût** : 130 images à générer (79 min) + rebuild + re-render (~2 h).
- **Correction** : une image dédiée par bloc (`Nxxx-A/B`), 130 images, zéro réutilisation.
- **Règle** : **une image par bloc dès le premier montage**. Un pool de 26 images ne tient pas 26 minutes.

### B5. OCR peu fiable

- **Symptôme** : tesseract n'a détecté aucun texte, alors qu'un moniteur affichait des chiffres.
- **Cause** : texte petit, faible contraste, image sombre.
- **Correction** : QC visuel + échantillons, pas uniquement OCR.
- **Règle** : l'OCR est un filtre, pas une validation.

### B6. Motifs qui se répètent

- **Symptôme** : la banque de 15 motifs par acte revient tous les 15 blocs.
- **Cause** : 70 blocs × 2 images = 140 images, la banque est trop petite.
- **Correction** : caméra/lumière variées, mais le sujet revient.
- **Règle** : 20–25 motifs par acte pour un film de 25 min, ou générer des variantes de sujet.

## C. Voix

### C1. Tunnels qui tombent

- **Symptôme** : 404 sur les 70 blocs, plusieurs fois.
- **Cause** : notebook redémarré / tunnel expiré.
- **Coût** : ~2 h cumulées.
- **Correction** : relance avec la nouvelle URL, reprise sans `--force`.
- **Règle** : générer la voix en une session stable, sauvegarder chaque prise, ne jamais dépendre d'un tunnel pour un batch long.

### C2. Upload de la référence

- **Symptôme** : `validation error for FileData`, chemin local refusé.
- **Cause** : Gradio 6 exige `{path, meta}`.
- **Correction** : POST multipart sur `/gradio_api/upload`, puis passer le `FileData`.
- **Règle** : lire le format d'input de l'API avant d'envoyer un chemin.

### C3. Lenteur

- **Symptôme** : RTF 3,6–8 ; 15 s d'audio en 55–120 s.
- **Cause** : modèle int4 sur T4 partagé.
- **Coût** : ~2 h pour 70 blocs.
- **Règle** : planifier la voix en dernier recours, ou utiliser un modèle local plus rapide pour les itérations.

### C4. Coutures entre blocs

- **Symptôme** : on entend la transition entre deux prises.
- **Cause** : blocs collés sans silence.
- **Coût** : qualité perçue.
- **Correction** : pour le prochain film, 0,25 s de silence + 0,15 s de poignée.
- **Règle** : le montage doit respirer entre les idées ; ce n'est pas un défaut de voix, c'est un défaut de montage.

## D. Musique et SFX

### D1. Moteur ACE-Step non initialisé

- **Symptôme** : `data: null` au premier appel.
- **Cause** : le serveur exige `init_engine` avant `generate_music_ui`.
- **Coût** : un appel perdu, ~1 min.
- **Correction** : `ensure_engine()` dans le client.
- **Règle** : reproduire le parcours UI (init → generate) dans le client.

### D2. Mapping musical `ACTE I` / `ACTE II`

- **Symptôme** : les actes II, III, IV recevaient M01.
- **Cause** : `includes('ACTE I')` matche `ACTE II`.
- **Coût** : un mix à refaire (~3 min).
- **Correction** : `startsWith('ACTE I ')` avec espace.
- **Règle** : les libellés d'actes sont des clés, pas des sous-chaînes.

### D3. Mix 192 kHz mono

- **Symptôme** : `mix.wav` en 192 kHz mono, 890 Mo.
- **Cause** : `loudnorm` upsample et downmix.
- **Correction** : `aformat=stereo` + `-ar 48000 -ac 2`.
- **Règle** : toujours vérifier `ffprobe` après un filtre audio.

### D4. Ouverture musicale

- **Symptôme** : `--lead`/`adelay` n'a pas allongé le mix.
- **Cause** : comportement de `amix`/`loudnorm`.
- **Correction** : segment de M00 à partir de 30 s, fondu, concaténé devant `mix.wav` → `mix-lead.wav`.
- **Règle** : pour un lead, construire un segment séparé et concaténer, pas un delay dans le graphe.

### D5. Aucun SFX placé

- **Symptôme** : la bibliothèque est prête (18 textures + 10 foley), mais le film n'a que voix + musique.
- **Cause** : on a produit les assets avant de faire le montage son.
- **Coût** : le film perd en texture documentaire.
- **Règle** : placer les SFX **pendant** le montage, pas après le picture lock.

## E. Rendu

### E1. `ctx.filter` blur

- **Symptôme** : 240 frames en 466 s (1,9 s/frame) avec des blurs canvas.
- **Cause** : `ctx.filter` est recalculé à chaque frame.
- **Correction** : pré-rendre grain, vignette, scanlines, grade ; bannir `ctx.filter` par frame.
- **Règle** : aucun filtre coûteux dans la boucle de rendu.

### E2. Canvas tainté

- **Symptôme** : `SecurityError: Tainted canvases may not be exported` avec `file://`.
- **Cause** : images locales chargées en `file://`.
- **Correction** : servir le dossier en HTTP.
- **Règle** : tout rendu canvas passe par un petit serveur local.

### E3. `setT` async / `out` manquant

- **Symptôme** : `ReferenceError: out is not defined` ; frames figées.
- **Cause** : le passage aux clips a rendu `setT` async ; `out` n'existait pas dans le renderer.
- **Correction** : `await window.setT(t)` dans `page.evaluate` ; ajouter `out`.
- **Règle** : après tout changement de signature, rendre un still de contrôle.

### E4. Clips 404 dans Actions

- **Symptôme** : 14 jobs échouent sur `/out/blender/shots/*.mp4`.
- **Cause** : les clips étaient en local, pas dans le checkout.
- **Correction** : `assets/clips/` versionné, ou mode clips opt-in.
- **Règle** : un asset référencé par un bloc doit être dans git ou téléchargé par le workflow.

### E5. `cp -n` et vieux mp4

- **Symptôme** : film muxé en 540p / mauvaise durée.
- **Cause** : `cp -n` n'écrase pas les anciens blocs.
- **Correction** : supprimer puis copier.
- **Règle** : jamais `cp -n` pour des artefacts de rendu.

### E6. Mémoire locale

- **Symptôme** : 3 Chromium en parallèle → EPIPE/OOM.
- **Cause** : 7,6 Go de RAM.
- **Correction** : 1 seul Chromium.
- **Règle** : local = 1 ; Actions = 20.

## F. GitHub Actions

### F1. ffmpeg absent

- **Symptôme** : `spawn ffmpeg ENOENT`.
- **Cause** : l'image `ubuntu-latest` n'a pas ffmpeg.
- **Correction** : `apt-get install -y --no-install-recommends ffmpeg`.
- **Règle** : ne jamais supposer un binaire préinstallé.

### F2. apt lent / timeout 40 min

- **Symptôme** : 7 jobs bloqués 40 min dans `apt-get`, run annulé à 63/70.
- **Cause** : miroir lent + `pocketsphinx`/pilotes recommandés.
- **Correction** : `--no-install-recommends`, timeout 20 min, retry.
- **Règle** : un job de bloc doit finir en < 5 min ; timeout 20 min max.

### F3. `join` sans `plan`

- **Symptôme** : le join encode en mode single au lieu de batch.
- **Cause** : `needs.plan.outputs.mode` vide.
- **Correction** : `needs: [plan, render]`.
- **Règle** : tout job qui lit un output de `plan` doit dépendre de `plan`.

### F4. Artefacts lents / « file exists »

- **Symptôme** : 156 chunks, 7 Go, download lent, extraction dans la racine.
- **Cause** : un artefact par chunk, `-D` mauvais.
- **Correction** : sous-dossier par artefact ; à l'avenir, un zip par plan.
- **Règle** : un artefact = un dossier, pas 156.

### F5. `/tmp` 3,9 Go

- **Symptôme** : download du film échoue à 68 Mo (disk quota).
- **Cause** : `/tmp` est un tmpfs de 3,9 Go.
- **Correction** : télécharger dans `out/` sur le disque projet.
- **Règle** : les gros fichiers ne vont jamais dans `/tmp`.

## G. Blender

### G1. EEVEE headless

- **Symptôme** : `libEGL.so.1` manquant, puis `xvfb-run` à 4 min/frame.
- **Cause** : EEVEE a besoin d'un contexte GL ; xvfb force le CPU.
- **Correction** : installer GL/EGL et utiliser un GPU réel, ou Cycles GPU.
- **Règle** : EEVEE sur CPU-only = impasse.

### G2. API Blender 5.2

- **Symptôme** : `use_bloom` absent, `CompositorNodeComposite` absent, OutputFile modifié.
- **Cause** : refonte du compositor en 5.x.
- **Correction** : rendu brut + glow/grade ffmpeg.
- **Règle** : ne pas dépendre du compositor pour un look ; le grade final se fait dans ffmpeg.

### G3. Cycles GPU

- **Symptôme** : `enum "OPTIX" not found`, fallback CPU.
- **Cause** : en 5.x, `cycles.device = 'GPU'`, OPTIX se choisit dans les préférences.
- **Correction** : `prefs.compute_device_type='OPTIX'`, `cycles.device='GPU'`.
- **Règle** : tester 3 frames avant de lancer 144.

## H. Éditorial et finition

- **Doublons** : voir B4, le pire poste.
- **Pas de SFX** : voir D5.
- **Miniature tardive** : elle aurait dû être faite dès le script pour clarifier le hook.
- **Fact-check non verrouillé** : les 3 chiffres (DishBrain, FinalSpark, Anthropic) restent à confirmer avant publication.
- **Pas de SRT** : à produire.
- **Pas de description/chapitres** : à produire.
- **26 min vs 18–22** : validé par l'utilisateur, mais à assumer dans le titre/description.

## Ce qui a bien marché

- Le **système de blocs** : re-rendu ciblé, cache, concat.
- Les **sidecars** d'images (prompt, seed, réglages) : reproductibilité.
- Le **style prompt** : cohérence de palette sur 156 images.
- Le **voice clone** : timbre convaincant, 70 blocs.
- Les **6 nappes** : adaptées aux actes.
- Le **motion kit** : propre, intégré, 8 insertions.
- Le **dépôt de passation** : tout est retrouvable.

## Les 10 règles pour le prochain film

1. **Une image par bloc**, dès le premier montage.
2. **La voix d'abord**, sur un endpoint stable, mesurée, avec des silences entre blocs.
3. **Pas de 2.5D avant le picture lock** ; 4–6 plans hero maximum.
4. **Tester 1 bloc sur Actions** avant une matrice de 70.
5. **Jamais `cp -n`** pour les artefacts.
6. **Télécharger dans `out/`**, jamais dans `/tmp`.
7. **Aucun `ctx.filter` par frame** ; pré-rendre les effets.
8. **Motion après les images**, et vérifier que le graphique correspond au plan.
9. **Placer les SFX pendant le montage**, pas après.
10. **Miniature et fact-check dès le début**, pas à la fin.

## Conclusion

Le film est là, et il est bon. Mais le prochain doit prendre **la moitié du temps** : moins de technologie exploratoire, plus de direction artistique, et des assets uniques décidés avant le montage.
