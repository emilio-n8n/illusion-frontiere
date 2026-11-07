# Décisions de style et de production

## Direction artistique

Référence absolue : image fournie par l'utilisateur — bureau/archive sombre, écran pâle, silhouette de dos, grain, profondeur de champ. Le film doit ressembler à des frames de film, jamais à un collage.

Palette :

- noir `#080A0D`, ombres bleu profond `#17232D`, bleu acier `#344B5B`
- bordeaux `#653E4A`, argent `#A1A1A0`, écran `#C9C4B8`
- rouge encre `#A81F16` avec parcimonie.

Typographie :

- Archivo Black pour les titres/nombres.
- JetBrains Mono pour les labels/HUD.
- Jamais de texte généré dans les images ; le texte est toujours dessiné par le moteur.

## Le Bureau

Métaphore assumée, pas un faux documentaire. « Ce bureau n'existe pas. » Le meuble, les tiroirs, le projecteur, la règle. Le récit fictif porte la thèse ; les faits restent réels.

## Voix

Voix clonée de l'utilisateur (Fish Audio Drama 3) plutôt qu'une voix synthétique générique. Le débit lent est assumé : l'utilisateur a validé jusqu'à 35 min. Ne pas accélérer, ne pas couper pour rentrer dans 22 min.

## Format

Master 1080p, 24 fps, H.264, AAC 192k, 48 kHz stéréo. Pas de 4K : les sources sont 1024/1536, un upscale 4K n'apporterait rien. Décision révisable si YouTube l'exige.

## Rendu

- Block par block, cache, concat. Pas de timeline unique de 26 min.
- GitHub Actions pour les rendus lourds ; local uniquement pour les tests et les petits rendus.
- Un seul Chromium en local (7,6 Go de RAM).
- Les clips 2.5D sont bruts ; le grade/grain est appliqué une seule fois par le moteur.

## Doublons d'images

Premier montage : 160 emplacements pour 22 images, jusqu'à 15 répétitions. Décision : **une image dédiée par bloc** (Nxxx-A/B), 130 images, zéro réutilisation. Les motifs peuvent se ressembler (mains, tiroirs), mais aucune image n'est répétée.

## Transitions de voix

Les blocs sont collés sans silence, la couture s'entend. Pour le prochain film : 0,25 s de silence entre blocs + 0,15 s de poignée en début/fin de prise. Pour ce film, on assume (ou on ajoute un fondu de 20 ms pour éviter les clics).

## Motion design Vox

Le style Vox doit être **projeté dans le monde du film**, pas posé comme une infographie claire :

- typographie pâle `#C9C4B8`, traits fins, rouge `#A81F16` pour l'accent ;
- nombres animés, grilles de points, barres de comparaison, timeline, brackets de cadrage, carte/frontière, barres de censure, citation ;
- pas de jaune/bleu vif, pas de fond blanc, pas de cards opaques ;
- les graphiques sont dessinés après le grade, avant le grain, pour être texturés par la pellicule ;
- 5–8 insertions maximum dans le film, aux moments de chiffres/dates.

## Ce qu'il ne faut pas faire

- Collage de photos, cut-out, split screen.
- Texte généré par l'image.
- Voix robotique générique.
- Rythme de diaporama : varier les cadrages, les échelles, les mouvements.
- Musique qui remplit le silence : le silence est un effet.
- Publier sans vérifier les licences et sans déclarer le contenu synthétique.
