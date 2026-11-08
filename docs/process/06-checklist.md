# 06 — Checklist réutilisable pour la prochaine vidéo

## Pré-production

- [ ] Sujet, angle, thèse en une phrase.
- [ ] Recherche : 5–10 sources primaires, chiffres vérifiés, limites.
- [ ] Script écrit pour la voix (phrases courtes, respirations).
- [ ] Découpage en blocs (un paragraphe = un bloc), 25–40 s max.
- [ ] Hook des 20 premières secondes écrit et testé à voix haute.
- [ ] Miniature et titre provisoires dès le script (le hook doit tenir en 3–4 mots).
- [ ] Fact-check verrouillé **avant** l'enregistrement de la voix.

## Voix

- [ ] Référence de clonage : 10–30 s, une seule voix, pas de musique.
- [ ] Transcript exact de la référence.
- [ ] Endpoint stable (local ou API), pas un tunnel temporaire pour un batch long.
- [ ] Une prise par bloc, seed fixe, sidecar.
- [ ] 0,15 s de poignée en début/fin, 0,25 s de silence entre blocs.
- [ ] `python3 tools/measure_audio.py` → durées réelles.
- [ ] Écoute de contrôle : 3 blocs au hasard, pas seulement le début.

## Images

- [ ] **Une image dédiée par bloc**, IDs `Nxxx-A/B`.
- [ ] Banque de 20–25 motifs par acte, caméra/lumière variées.
- [ ] Style prompt + negative validés sur 3 images avant le batch.
- [ ] Batch reprenable, sidecars, seeds.
- [ ] QC : texte parasite sur écrans, anatomie, doublons de motif, palette.
- [ ] Pas plus de 2 images par bloc (sauf besoin).
- [ ] 1024 pour les inserts, 1536 pour les hero.

## Motion design

- [ ] Graphiques choisis **après** les images, pour éviter les mismatches.
- [ ] 5–8 insertions max.
- [ ] Chaque graphique est calé sur la phrase (`at = index/len * durée`).
- [ ] Un seul accent rouge par graphique.
- [ ] Test de lisibilité à 25 % de la taille.
- [ ] Preview 3 s par graphique (le still ne montre pas le mouvement).
- [ ] Pas de label littéral sur une image qui ne correspond pas.

## 2.5D / 3D (optionnel)

- [ ] Picture lock d'abord.
- [ ] 4–6 plans hero maximum.
- [ ] Depth maps vérifiées (silhouette, premier plan, fond).
- [ ] Clips bruts, grade dans le moteur.
- [ ] Rendu sur GPU réel, pas EEVEE CPU.

## Rendu

- [ ] Test d'un bloc en 540p, still + mp4.
- [ ] Test d'un bloc sur Actions avant la matrice.
- [ ] ffmpeg installé avec `--no-install-recommends`.
- [ ] Timeout job 20 min, retry.
- [ ] `join` dépend de `plan`.
- [ ] Assets référencés présents dans git (pas de 404).
- [ ] Télécharger les gros artefacts dans `out/`, pas `/tmp`.
- [ ] Jamais `cp -n`.

## Audio et assemblage

- [ ] Voix + musique : ducking, -14 LUFS, -1 dBTP.
- [ ] Ouverture musicale construite comme segment séparé, concaténée.
- [ ] SFX placés pendant le montage (projecteur, papier, tiroirs, pas, néon, pluie…).
- [ ] Crédits Freesound CC-BY.
- [ ] Vérifier `ffprobe` : 48 kHz stéréo, durée, flux.

## Finition

- [ ] Sous-titres `.srt` français.
- [ ] Générique : sources, images IA, musique, polices, foley.
- [ ] Miniature 1280×720, < 2 Mo, lisible en petit.
- [ ] Titre YouTube, description, chapitres, sources.
- [ ] Déclaration « contenu synthétique ».
- [ ] Contrôle qualité téléphone + casque.
- [ ] Publication programmée.

## Après publication

- [ ] Surveiller rétention 48 h.
- [ ] Répondre aux commentaires sources.
- [ ] Noter ce qui a marché / ce qui a cassé.
- [ ] Mettre à jour `docs/process/05-postmortem.md`.
