# Studio — chaîne IA

Dépôt de production de la chaîne. Premier film : **L'Illusion de la frontière**.

## État

- Script v1 : `films/01-illusion-frontiere/script/script-v1.md`
- Découpage narration : `films/01-illusion-frontiere/script/blocks.md` — 70 blocs, 21,6 min estimées
- Notes de vérification : `films/01-illusion-frontiere/research/fact-check-v1.md`
- Storyboard : `films/01-illusion-frontiere/storyboard/shots.json` — 26 plans
- Prompts et style : `films/01-illusion-frontiere/prompts/style.json`
- Images générées : `assets/generated/`
- Rendu : `studio/`
- Preuve visuelle : `out/film-proof.mp4` — 2 min 45, 1080p, 24 fps, sans audio
- Animatique complète : `out/animatic-silent.mp4` — 21 min 37, 70 blocs, 960×540, sous-titres, sans audio
- Actions : `.github/workflows/render.yml` (run B00 validé, run 7 blocs en cours)

## Structure

```
films/01-illusion-frontiere/
  script/        narration, blocs, versions
  research/      sources, vérifications
  prompts/       sujets de plans + style.json
  storyboard/    shots.json (plan → image → caméra → overlay)
  audio/         guide d'enregistrement, sound design
studio/
  render.html          moteur de rendu (canvas, grain, étalonnage)
  render_block.mjs     un bloc → mp4 (Chromium + ffmpeg)
  render_all.mjs       tous les blocs prêts
  build_blocks.mjs     storyboard → 7 blocs de preuve
  build_narration_blocks.mjs  narration → 70 blocs animatiques
  concat.mjs           assemblage
  blocks/              7 blocs de preuve (B00…B06)
  narration/           70 blocs de narration (N001…N070)
tools/
  imagine.py           client Gradio
  batch_generate.py    génération par lot, reprise automatique
  split_script.py      script → blocs de narration
  measure_audio.py     durées réelles de la voix
```

## Génération d'images

Le endpoint Gradio est un tunnel temporaire. On le passe par `--url` ou `GRADIO_URL`.

```bash
python3 tools/batch_generate.py
python3 tools/batch_generate.py --only B02-S03 --force
```

Chaque image reçoit un sidecar `.json` avec le prompt exact, la graine et les réglages. Une image doit toujours pouvoir être reproduite.

## Rendu

```bash
node studio/build_blocks.mjs
node studio/check_assets.mjs

# une preuve rapide, 960x540
node studio/render_all.mjs --scale 0.5 --parallel 3 --concat

# le master 1080p
node studio/render_all.mjs --scale 1 --parallel 4 --concat
```

Un bloc = une page HTML + un JSON de timeline + un mp4. Le rendu d'un bloc de 25 s prend environ 45 s en 1080p sur cette machine.

### Blocs de preuve (B00–B06)

Sept blocs, 165 s, qui couvrent les moments visuels clés du film : le Bureau, l'enfant, H.M., le corps, l'émotion, la conscience, la frontière. C'est la preuve de look.

```bash
node studio/concat.mjs --dir blocks --out out/film-proof.mp4
```

Le rendu local 1080p est dans `out/film-proof.mp4`. Le même assemblage est produit par GitHub Actions en artefact `film-silent`.

### Blocs de narration (N001–N070)

Un bloc par paragraphe du script. Le texte est affiché en sous-titre pour l'animatique. Quand la voix est enregistrée :

```bash
python3 tools/measure_audio.py
node studio/build_narration_blocks.mjs
```

Les durées réelles remplacent les estimations et pilotent le montage.

## GitHub Actions

Workflow manuel `render` :

- `dir` : `blocks` (preuve) ou `narration` (animatique)
- `blocks` : `all` ou une liste (`B00,B01`)
- `scale` : `1` ou `0.5`
- `preset` / `crf` : réglages x264

Chaque bloc est rendu dans un job séparé, uploadé en artefact, puis le job `join` concatène le master. Les mp4 ne sont pas versionnés.

Remote : https://github.com/emilio-n8n/illusion-frontiere (public, minutes Actions illimitées).
