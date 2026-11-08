# Résumé motion design — 60 secondes

**Fichier :** `out/summary/illusion-frontiere-60s.mp4`  
**Format :** 1920×1080, 24 fps, 60 s, sans voix, musique et SFX.  
**Release :** `summary-60s` (GitHub).

Ce n'est pas une bande-annonce classique : c'est le film résumé en motion design, dans la même grammaire visuelle que l'archive (noir bleu, typographie pâle, rouge encre, grain, HUD).

## Découpage

| Temps | Scène | Écran |
|---|---|---|
| 0–4 s | Ouverture | Titre, dossier 01, règle rouge |
| 4–11 s | La question | « Où commence la conscience ? », ligne HUMAIN / MACHINE |
| 11–19 s | Le cerveau | 86 milliards, grille de points, « il ne stocke pas, il reconstruit » |
| 19–26 s | Le DishBrain | 800 000 neurones, mini-Pong, « mieux que le hasard » |
| 26–33 s | La matière | 16 organoïdes, 160 000 neurones, barres DishBrain / FinalSpark |
| 33–41 s | La frontière recule | frise 1950 → aujourd'hui → ? |
| 41–48 s | Le doute | dossier censuré, tampon « CONSCIENT : PRÉSUMÉ » |
| 48–56 s | La ligne | la frontière se trace puis s'efface, « c'est une histoire » |
| 56–60 s | Fin | carton titre, 26 minutes |

## Fabrication

- `studio/summary.html` : moteur Canvas autonome (9 scènes), réutilise les images du film, les polices, le grade, la vignette, le grain et les scanlines.
- `studio/render_block.mjs --page summary.html --block SUMMARY` : rendu des 1 440 frames.
- `studio/mix_summary.mjs` : lit M03 (tension) et M05 (finale), ajoute les SFX, normalise à -14 LUFS / -2.6 dBTP.
- Le montage est calé sur une mesure à 60 BPM : les coupes tombent sur les secondes.

## Audio

- **Musique :** M03 de 0 à 45,5 s (fondu), M05 à partir de 55 s du fichier, placée à 43 s (crossfade), fin en fondu.
- **SFX :** projecteur en boucle, shimmer aux transitions, sub drops à 19 s et 26 s, tiroir à 41 s, tampon à 45,22 s (exactement sur l'impact visuel).
- **Niveau :** -14,0 LUFS intégré, true peak -2,6 dBTP, 48 kHz stéréo, AAC 192 kbps.

## Notes éditoriales

- 86 milliards : ordre de grandeur du cerveau d'un enfant à la naissance.
- 800 000 : neurones humains cultivés par Cortical Labs (DishBrain, 2022).
- 16 organoïdes / 160 000 neurones : FinalSpark.
- La frise s'arrête sur « AUJOURD'HUI — BIEN-ÊTRE DES MODÈLES » pour ne pas inventer une date ; le film complet développe les chartes de bien-être des modèles.
- Le caveat du film est conservé : « des cultures sans yeux, sans oreilles, sans histoire » — ce ne sont pas des cerveaux miniatures.

## Commande

```bash
CHROME=$HOME/.cache/ms-playwright/chromium-1248/chrome-linux64/chrome \
  node studio/render_block.mjs --page summary.html --block SUMMARY \
  --out out/summary/summary-60s-silent.mp4 --scale 1

node studio/mix_summary.mjs \
  --video out/summary/summary-60s-silent.mp4 \
  --out out/summary/illusion-frontiere-60s.mp4
```

Le rendu prend ~3 min en local (8 fps de capture). Le mix prend ~10 s.
