# Studio — moteur de rendu

Chaque bloc est un dossier de données : un JSON de timeline + des images. Le moteur est une page Canvas (`render.html`) qui dessine une frame pour un temps `t`. Le script `render_block.mjs` pilote Chromium, capture les frames et les encode avec ffmpeg.

## Format d'un bloc

```json
{
  "id": "B01",
  "title": "Apprendre",
  "fps": 24,
  "width": 1920,
  "height": 1080,
  "fadeIn": 0.35,
  "fadeOut": 0.35,
  "duration": 22,
  "subtitle": null,
  "shots": [
    {
      "id": "B01-S01",
      "src": "/assets/generated/B01-S01.png",
      "duration": 7,
      "camera": "push-in",
      "overlay": "APPRENDRE",
      "overlayPos": "left",
      "stamp": false,
      "transition": "cut",
      "seed": 7101
    }
  ]
}
```

- `duration` du bloc = somme des `duration` des shots. Le moteur s'arrête à la dernière frame.
- `camera` : `push-in`, `push-out`, `pan-left`, `pan-right`, `static`.
- `overlay` : texte court affiché en bas à gauche (ou au centre avec `overlayPos: "center"`).
- `stamp` : encadre l'overlay d'un tampon rouge.
- `subtitle` : texte long affiché en bas, utilisé pour les animatiques sans voix.
- `transition` : `cut` ou `dissolve`. Une dissolve ne fonctionne qu'à l'intérieur d'un bloc.

## Commandes

```bash
# construire les 7 blocs de preuve depuis le storyboard
node studio/build_blocks.mjs

# construire les 70 blocs de narration
node studio/build_narration_blocks.mjs

# vérifier les images
node studio/check_assets.mjs

# un bloc, quelques stills
node studio/render_block.mjs --block B00 --stills 2,8,15 --scale 0.5

# un bloc, mp4
node studio/render_block.mjs --block B00 --dir blocks --out out/blocks/B00.mp4 --scale 1

# tous les blocs prêts, puis concat
node studio/render_all.mjs --dir blocks --scale 1 --parallel 4 --concat
```

## Rendu

- Chromium via Playwright. En local : `CHROME=~/.cache/ms-playwright/chromium-1248/chrome-linux64/chrome`.
- ffmpeg : H.264, `yuv420p`, `+faststart`, CRF 18–20.
- 1920×1080 : ~12 fps de capture, soit ~40 s pour 18 s de vidéo.
- 960×540 : ~25 fps de capture, soit ~17 s pour 18 s.
- Les frames sont envoyées à ffmpeg par `image2pipe` ; pas de dossier de frames sur disque.

## Pourquoi ça tient 20 minutes

- Le bloc est l'unité de cache : on ne re-rend que le bloc modifié.
- Les blocs sont indépendants : GitHub Actions les rend en parallèle.
- La durée vient de la voix : `tools/measure_audio.py` met à jour `script/blocks.json`, puis `build_narration_blocks.mjs` répartit la durée réelle sur les shots.
- Aucun effet coûteux par frame (`ctx.filter` est banni) : grain, vignette, scanlines et étalonnage sont pré-rendus une fois.

## Ajouter un plan

1. Ajouter l'entrée dans `films/01-illusion-frontiere/storyboard/shots.json` (prompt, seed, résolution, caméra, overlay).
2. Générer l'image : `python3 tools/batch_generate.py --only B07-S01`.
3. Ajouter le bloc dans `studio/build_blocks.mjs` ou le mapping de narration.
4. Rebuild + render.

## Actions

Le workflow `.github/workflows/render.yml` accepte `dir=blocks` (preuve) ou `dir=narration` (animatique). Chaque bloc est un job ; le job `join` concatène. Les mp4 sortent en artefacts, jamais dans git.
