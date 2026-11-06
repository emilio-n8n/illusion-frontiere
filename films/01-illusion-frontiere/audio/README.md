# Voix off — guide d'enregistrement

## Format

- **48 kHz / 24 bits / WAV**, mono.
- Niveau : pics autour de **-6 dBFS**, plancher de bruit sous **-60 dBFS**.
- Pas de compression, pas de réverbération, pas de traitement. On étalonne au montage.
- Une prise par bloc, fichier séparé : `N001.wav`, `N002.wav`, etc.
- Laisser **0,5 s de silence** au début et à la fin de chaque prise.
- Ne pas couper les respirations. Elles seront conservées ou atténuées au montage.

## Jeu

Le script est écrit pour une voix calme, curieuse, légèrement inquiète. Pas de ton professoral, pas de dramatisation. La tension vient des phrases, pas de la performance.

- Les phrases courtes se posent, elles ne se précipitent pas.
- Les énumérations peuvent accélérer légèrement.
- Les questions ne montent pas toutes de la même façon : certaines sont de vraies questions, d'autres sont rhétoriques.
- Le refrain « Un dossier de plus. Une frontière de moins. » se dit presque à voix basse.

## Livraison

Déposer les fichiers dans :

```
films/01-illusion-frontiere/audio/blocks/
```

Puis mesurer :

```bash
python3 tools/measure_audio.py
```

Le script remplace les durées estimées par les durées réelles et écrit `audio/durations.json`. C'est ce fichier qui pilotera le montage.

## Blocs

La liste complète, avec le texte exact et les shots suggérés, est dans :

```
films/01-illusion-frontiere/script/blocks.md
```

70 blocs, 21,6 min estimées à 165 mots/min. La durée réelle peut varier de 10 à 15 %. Ne pas forcer le débit pour rentrer dans l'estimation : c'est le montage qui s'adapte.
