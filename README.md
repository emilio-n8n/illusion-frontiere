# Studio — chaîne IA

Dépôt de production de la chaîne. Premier film : **L'Illusion de la frontière**.

## État

- Script v1 : `films/01-illusion-frontiere/script/script-v1.md`
- Notes de vérification : `films/01-illusion-frontiere/research/fact-check-v1.md`
- Style visuel et prompt maison : `films/01-illusion-frontiere/prompts/style.json`
- Trois images de test : `assets/tests/`
- Générateur d'images : `tools/imagine.py`
- Pipeline de rendu : à construire (`studio/`, `.github/workflows/`)

## Structure

```
films/01-illusion-frontiere/
  script/        narration, versions
  research/      sources, vérifications
  prompts/       sujets de plans + style.json
  blocks/        un bloc = une page HTML + un rendu
  audio/         voix off, musique, sound design
studio/          moteur de rendu et assemblage
tools/           génération d'images, utilitaires
assets/          images générées, références
lab/             prototypes de style (non versionnés en frames)
```

## Boucle de production

1. Le script est découpé en **blocs de narration** de 20 à 40 secondes.
2. La voix off est enregistrée ou générée, puis mesurée : c'est elle qui fixe la durée du bloc.
3. Les images du bloc sont générées avec le prompt maison, puis contrôlées.
4. Chaque bloc est une page HTML autonome, rendue en mp4.
5. Les blocs sont concaténés, la musique et le sound design sont mixés, l'étalonnage final est appliqué.

## Génération d'images

Le endpoint Gradio est un tunnel temporaire. On le passe par `--url` ou `GRADIO_URL`.

```bash
python3 tools/imagine.py \
  --prompt-file films/01-illusion-frontiere/prompts/tests/A-control-room.txt \
  --style-json films/01-illusion-frontiere/prompts/style.json \
  --seed 424242 \
  -o assets/tests/A-control-room.png
```

Chaque image reçoit un sidecar `.json` avec le prompt exact, la graine et les réglages. Une image doit toujours pouvoir être reproduite.

## Rendu

Les rendus lourds sont destinés à GitHub Actions. Le dépôt ne versionne ni les frames ni les mp4 : seuls les assets sources, les scripts et les manifestes sont commités. Les rendus sortent en artefacts de workflow.

> Le pipeline Actions n'est pas encore écrit. Il le sera après validation du script et du découpage en blocs.
