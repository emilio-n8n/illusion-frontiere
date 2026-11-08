# 04 — Rendu et GitHub Actions

## Le moteur de blocs

- `studio/render.html` : Canvas 1920×1080, dessine une frame pour un temps `t`.
- `studio/render_block.mjs` : Chromium headless + `page.evaluate(async t => setT(t))` + `toDataURL` + pipe ffmpeg.
- `studio/render_all.mjs` : rend les blocs dont les assets existent, parallélisme réglable.
- `studio/concat.mjs` : concat `-c copy` des mp4 de blocs.

### Débit mesuré

| Résolution | Débit de capture | Temps pour 25 s de bloc |
|---|---|---|
| 960×540 | ~25 fps | ~25–30 s |
| 1920×1080 | ~12 fps | ~45–60 s (images) / ~2 min (clips vidéo) |

- Les clips mp4 ralentissent la capture (seek frame par frame).
- En local, **1 seul Chromium** : 3 en parallèle = OOM (7,6 Go de RAM).
- Sur Actions, chaque bloc est un runner séparé : 20 en parallèle.

## Actions — workflow `render`

Entrées :

- `dir` : `blocks` (preuve) ou `narration` (film).
- `blocks` : `all` ou liste.
- `scale` : 1 ou 0.5.
- `preset`, `crf`, `partial`.

Structure :

1. `plan` : calcule la matrice des blocs.
2. `render` : un job par bloc ; checkout, npm, Chromium, ffmpeg, rendu, artefact.
3. `join` : télécharge les artefacts, concatène, upload `film-silent`.

### Pièges corrigés

- **ffmpeg absent** : `spawn ffmpeg ENOENT`. Installer explicitement.
- **apt lent** : `ffmpeg` tire `pocketsphinx` et des pilotes VA-API ; 7 jobs ont timeout à 40 min. Utiliser `--no-install-recommends` et un timeout de 20 min.
- **`join` sans `plan`** : en mode batch, `needs.plan.outputs.mode` était vide → mauvais chemin d'encodage. `needs: [plan, render]`.
- **Clips absents** : les blocs pointaient vers `/out/blender/shots/*.mp4`, non poussés → 404 sur 14 jobs. Les clips doivent être dans `assets/clips/` (versionnés) ou le mode clips doit être opt-in.
- **`cp -n`** : les anciens mp4 540p n'étaient pas écrasés → film muxé avec de vieux blocs, mauvaise durée/résolution. Toujours supprimer avant de recopier.
- **Artefacts 156 chunks** : `gh run download` lent, et extraction dans la racine → « file exists ». Télécharger chaque artefact dans son sous-dossier.
- **`/tmp` 3,9 Go** : le download d'un film de 543 Mo a échoué à 68 Mo (quota). Télécharger dans `out/` sur le disque projet.
- **Playwright** : `npm ci` télécharge les navigateurs ; ajouter `PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD=1` et `npx playwright install --with-deps chromium`.

## Actions — workflow `blender`

- Matrice par plages de frames (`chunks`), pas un job de 144 frames.
- Chaque job télécharge Blender 5.2.1 (cache tarball), installe GL/EGL, rend sa plage, upload les PNG.
- `join` assemble les frames et encode.
- **EEVEE headless** : `xvfb-run` force le CPU (4 min/frame) ; sans X, EGL_BAD_MATCH. Sur Actions CPU, utiliser Cycles CPU ou abandonner. Sur T4, Cycles GPU (`cycles.device='GPU'`, OPTIX dans les préférences).
- **Blender 5.2** : plus de bloom EEVEE, plus de nœud Composite ; OutputFile a changé. Contournement : rendu brut + glow/grade ffmpeg.

## Assemblage final

```bash
# 1. récupérer le film silencieux
gh run download <run-id> -n film-silent -D out/v2

# 2. intro + film
printf "file '%s'\nfile '%s'\n" "$PWD/out/intro.mp4" "$PWD/out/v2/film-silent.mp4" > /tmp/list.txt
ffmpeg -f concat -safe 0 -i /tmp/list.txt -c copy out/film-v2-with-intro.mp4

# 3. mux voix + musique
ffmpeg -i out/film-v2-with-intro.mp4 -i out/audio/mix-lead.wav \
  -map 0:v:0 -map 1:a:0 -c:v copy -c:a aac -b:a 192k -shortest \
  -movflags +faststart out/film-final-v2.mp4
```

## Release

```bash
gh release create film-final-v2 out/film-final-v2.mp4 \
  --title "..." --notes "..."
```

- Les mp4 ne sont pas dans git.
- Les images, clips, sidecars, scripts et docs le sont.
- Toujours vérifier la durée, la résolution et les flux avec `ffprobe` avant release.
