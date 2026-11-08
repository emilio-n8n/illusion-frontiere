# 01 — Le pipeline complet

## Vue d'ensemble

```
recherche + script
  ↓
découpage en blocs de narration (un paragraphe = un bloc)
  ↓
voix off par bloc (clonage) + mesure des durées réelles
  ↓
images dédiées par bloc + depth maps (optionnel)
  ↓
blocs JSON (shots, durées, motion, overlays)
  ↓
rendu bloc par bloc (Chromium + ffmpeg)
  ↓
mux voix par bloc
  ↓
mix voix + musique + SFX
  ↓
concat + carton d'ouverture + release
```

## Étape 0 — Recherche et script

- Le brief fournit la thèse, les actes, les interdits scientifiques.
- Le script est écrit pour être **lu**, pas pour être beau à l'écran : phrases courtes, respirations, refrains.
- Le script est découpé en **70 blocs** (`tools/split_script.py`), un paragraphe par bloc.
- Chaque bloc reçoit un ID (`N001`…`N070`), un acte, un nombre de mots, une durée estimée à 165 mots/min.
- Le découpage est la **liste d'enregistrement** de la voix : `films/01-illusion-frontiere/script/blocks.md`.

## Étape 1 — Voix

- Modèle : Fish Audio Drama 3, clonage à partir de 10 s de référence.
- Une prise par bloc, WAV 44,1 kHz mono.
- `tools/drama_voice.py` gère : upload de la référence, direction de jeu par acte, reprise sans `--force`, sidecars.
- `tools/measure_audio.py` remplace les durées estimées par les durées réelles.
- Résultat : 25 min 56 de voix.

## Étape 2 — Images

- Krea 2 Turbo, 8 steps, 1024 ou 1536.
- **Une image dédiée par bloc** (`Nxxx-A`, `Nxxx-B`), pas un pool réutilisé.
- Prompts : banque de motifs par acte + caméra + lumière, dans `tools/make_shot_v2.py`.
- Style : `films/01-illusion-frontiere/prompts/style.json` (look + negative).
- Sidecar JSON par image : prompt exact, seed, réglages.
- QC : texte parasite, anatomie, doublons de motif, cohérence de palette.

## Étape 3 — Depth et 2.5D (optionnel)

- Depth Anything V2 produit une carte de profondeur par image.
- `blender/photo_depth.py` plaque l'image sur une grille, la déplace avec la profondeur, et anime une caméra.
- Rendu brut, sans grade ; le moteur applique le look une seule fois.
- Utile pour quelques plans hero, pas pour les 70 blocs : le coût de rendu est élevé.

## Étape 4 — Blocs JSON

Un bloc = un fichier `studio/narration/Nxxx.json` :

```json
{
  "id": "N011",
  "title": "ACTE I — APPRENDRE",
  "fps": 24,
  "width": 1920,
  "height": 1080,
  "fadeIn": 0.18,
  "fadeOut": 0.18,
  "duration": 18.112,
  "subtitle": null,
  "motions": [ ... ],
  "shots": [
    { "id": "N011-A", "src": "/assets/generated/N011-A.png", "duration": 9.96, "camera": "push-in" },
    { "id": "N011-B", "src": "/assets/generated/N011-B.png", "duration": 8.15, "camera": "pan-right" }
  ]
}
```

- La durée du bloc vient de la voix mesurée, jamais d'une fenêtre fixe.
- Les shots se partagent la durée (55/45 pour deux).
- `motions` est optionnel ; le renderer dessine les graphiques.

## Étape 5 — Rendu

- `studio/render.html` dessine une frame pour un temps `t`.
- `studio/render_block.mjs` pilote Chromium, capture les frames, encode avec ffmpeg.
- Un bloc = un mp4. Cache, re-rendu ciblé.
- En local : 1 Chromium à la fois (7,6 Go de RAM).
- Sur Actions : matrice de 70 jobs, 20 en parallèle.

## Étape 6 — Audio et assemblage

- `studio/mux_voice.mjs` ajoute la prise voix à chaque bloc.
- `studio/mix_audio.mjs` construit le lit musical par acte, ducke sous la voix, normalise à -14 LUFS.
- `out/audio/mix-lead.wav` ajoute 6 s d'ouverture musicale.
- `out/intro.mp4` est le carton titre 6 s.
- `studio/concat.mjs` concatène intro + film, puis mux du mix final.

## Étape 7 — Release

- `gh release create film-final-v2 out/film-final-v2.mp4`.
- Miniature : `studio/thumbnail.mjs` → deux variantes 1280×720.
- Le dépôt garde les sources, pas les mp4.

## Ce qui est industrialisable

- Le découpage, la génération d'images, le rendu par blocs, le mux, le mix.
- Ce qui ne l'est pas : l'écriture, le choix des images (QC), le montage des SFX, la miniature.
- Le goulot n'est pas le rendu : c'est la **direction artistique** et le **contrôle des assets**.
