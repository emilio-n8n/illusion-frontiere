# Pipeline de production

## Vue d'ensemble

```
script (70 blocs)
  → voix clonée (Fish Audio Drama 3) + mesure des durées
  → images (Krea 2 Turbo) + depth maps (Depth Anything V2)
  → clips 2.5D (Blender photo_depth) ou images fixes
  → blocs JSON (shots, durées, overlays, motion)
  → rendu bloc par bloc (Chromium + ffmpeg)
  → mux voix + musique + SFX
  → concat + étalonnage final
```

## Le bloc

Un bloc = un JSON (`studio/blocks/*.json` ou `studio/narration/*.json`) + des images/clips. Chaque bloc a une durée propre, une liste de shots, un `fadeIn`/`fadeOut`, un `subtitle` optionnel, des `motions` optionnelles.

Un shot :
```json
{
  "id": "N011-A",
  "src": "/assets/generated/N011-A.png",
  "duration": 8.2,
  "camera": "push-in",
  "overlay": "",
  "transition": "cut",
  "seed": 100100
}
```

`src` peut être un PNG (`/assets/generated/...`) ou un clip (`/assets/clips/...`). Le moteur détecte l'extension, seek la vidéo frame par frame, et n'ajoute pas de mouvement synthétique aux clips.

## Le moteur

- `studio/render.html` : Canvas 1920×1080, grade teal/bordeaux, vignette, grain, scanlines, poussière, HUD, overlays, sous-titres, motion design.
- `studio/render_block.mjs` : Chromium headless + ffmpeg, capture ~12 fps en 1080p, ~25 fps en 540p.
- `studio/render_all.mjs` : rend les blocs prêts, parallélisme à régler selon la RAM (1 en local, 20 sur Actions).
- `studio/concat.mjs` : concaténation `-c copy`.
- `studio/mux_voice.mjs` : ajoute la prise voix à un bloc.
- `studio/mix_audio.mjs` : voix + musique par acte, ducking, -14 LUFS.
- `studio/assemble_clips.mjs` : frames Blender → mp4 (brut, sans grade).
- `studio/check_assets.mjs` : vérifie que tous les assets existent.

## Commandes

```bash
# images
python3 tools/batch_generate.py --manifest films/01-illusion-frontiere/storyboard/shots-v2.json

# blocs narration
SUBTITLES=0 node studio/build_narration_blocks.mjs
node studio/check_assets.mjs narration

# rendu local (1 seul Chromium)
node studio/render_all.mjs --dir narration --scale 1 --parallel 1 --force

# mix
node studio/mix_audio.mjs --video ""          # → out/audio/mix.wav
# (l'ouverture de 6 s est construite séparément, voir 03-assets.md)

# assemblage final
node studio/mux_voice.mjs
node studio/concat.mjs --dir voiced --out out/film-final-voiced.mp4
```

## GitHub Actions

- `.github/workflows/render.yml` : rendu des blocs par matrice, artefacts, join.
- `.github/workflows/blender.yml` : scènes Blender et 2.5D par plages de frames.
- Le workflow `render` accepte `dir=blocks` (preuve) ou `dir=narration` (film), `scale`, `preset`, `crf`, `partial`.
- Les mp4 ne sont **jamais** poussés dans git ; les images et clips sources le sont.
- Les runners n'ont pas ffmpeg préinstallé : le workflow l'installe avec `--no-install-recommends`.

## Pièges connus

- **Playwright Chromium** : pas de H.264 ? En pratique il lit les mp4 H.264 locaux et sur Actions ; vérifier si un clip échoue.
- **Mémoire locale** : 7,6 Go, un seul Chromium à la fois. Trois en parallèle = OOM.
- **`cp -n`** : ne écrase pas les anciens mp4 ; toujours supprimer avant de recopier les artefacts.
- **`colorbalance` ffmpeg** : les options sont `rs/gs/bs`, `rm/gm/bm`, `rh/gh/bh` ; `ms`/`hs` n'existent pas.
- **Blender 5.2** : EEVEE headless a besoin de GL/EGL ; `xvfb-run` force le CPU. Cycles GPU : `cycles.device='GPU'`, OPTIX dans les préférences.
- **Gradio** : les tunnels `*.gradio.live` expirent ; toujours passer l'URL en argument ou `DRAMA_URL`/`ACE_URL`.
- **Fichiers Gradio** : les inputs audio doivent être uploadés via `/gradio_api/upload` et passés comme `{path, meta}`.

## Où sont les rendus

- `out/film-final-intro.mp4` : v1 complète (26:02, voix + musique, images répétées).
- `out/film-proof-clips.mp4` : preuve 2:45 avec les 26 clips 2.5D.
- `out/animatic-silent.mp4` : animatique silencieuse 70 blocs (sous-titres).
- `out/audio/mix.wav` : mix voix + musique.
- `out/audio/mix-lead.wav` : mix avec 6 s d'ouverture musicale.
- `out/intro.mp4` : carton titre 6 s.
- `out/film-final-v2` : à produire avec les 130 images uniques.
