# Assets — voix, musique, SFX, images, licences

## Voix

- 70 prises : `films/01-illusion-frontiere/audio/blocks/N001.wav` … `N070.wav`
- Mesures : `films/01-illusion-frontiere/audio/durations.json`
- Statut : `films/01-illusion-frontiere/audio/voice-status.json`
- Référence de clonage : `assets/voice-test/reference.wav` (10 s, voix de l'utilisateur)
- Transcript de la référence : « aujourd'hui on va parler d'un sujet qui passionne et qui intrigue la plupart d'entre nous : les ordinateurs organiques »
- Modèle : Fish Audio Drama 3 (Gradio, 83 langues, clonage zéro-shot)
- Direction : `[calm, low voice, intimate documentary narrator, slow, close to the microphone]` au prologue, variantes par acte dans `tools/drama_voice.py`
- Client : `tools/drama_voice.py`
- Durée mesurée : 25 min 56.
- Piège : le modèle est lent (~4-8× temps réel) et le tunnel expire. Reprendre sans `--force` pour ne pas régénérer les blocs existants.

## Musique

- 6 nappes : `films/01-illusion-frontiere/audio/music/M00.wav` … `M05.wav` (90–120 s, 48 kHz stéréo).
- Mapping : M00 prologue, M01 acte I, M02 acte II, M03 acte III, M04 acte IV, M05 acte V/finale.
- Générées avec ACE-Step 1.5 (Gradio), prompts dans `films/01-illusion-frontiere/audio/music.json`.
- Client : `tools/ace_music.py` (initialise le moteur avant de générer).
- Mix : `studio/mix_audio.mjs` (ducking, -14 LUFS). L'ouverture de 6 s est un segment de M00 à partir de 30 s, volume 0.16, fondu, concaténé devant `mix.wav` → `mix-lead.wav`.

## SFX

- 18 textures : `films/01-illusion-frontiere/audio/sfx/S01.wav` … `S18.wav` (room tones, hums, météo, riser, sub drop, heartbeat, projecteur, bande, IRM).
- Catalogue : `films/01-illusion-frontiere/audio/sfx.json`.
- 10 sons de foley : `films/01-illusion-frontiere/audio/foley/*.mp3` (projecteur, tiroir, pas, porte, pluie, néon, tampon, bande).
- Crédits : `films/01-illusion-frontiere/audio/foley-credits.md` (CC0/CC-BY).
- Clé Freesound : `~/.config/illusion-frontiere/freesound.key` (hors dépôt, ne jamais committer).
- Client : `tools/freesound.py`.
- **Aucun SFX n'est encore placé dans le montage.** La bibliothèque est prête.

## Images

- 26 images hero : `assets/generated/B00-S01.png` … `B06-S03.png` (1536×864 ou 1024×576).
- Cartes de profondeur : `assets/depth/B00-S01.png` … (Depth Anything V2, 16-bit).
- **130 images uniques v2** : `assets/generated/N001-A.png` … `N070-B.png` (générées pour supprimer les doublons).
- Prompts et seeds : `films/01-illusion-frontiere/storyboard/shots-v2.json`.
- Mapping bloc → images : `films/01-illusion-frontiere/storyboard/narration-map.json`.
- Style : `films/01-illusion-frontiere/prompts/style.json`.
- Client : `tools/imagine.py` (Krea 2 Turbo, 8 steps), `tools/batch_generate.py`.

## Clips 2.5D

- 26 clips bruts : `assets/clips/B00-S01.mp4` … `B06-S03.mp4` (1080p, 24 fps, sans grade).
- Générés par `blender/photo_depth.py` (image + depth → grille déplacée + caméra).
- Le moteur applique le grade ; ne pas baker le grade dans les clips.
- Les clips ne sont pas encore utilisés dans le montage v2 (les 130 images uniques prennent le dessus). Ils restent disponibles pour une version « hero » ou des inserts.

## Licences

- Images Krea : vérifier les conditions commerciales du service avant monétisation.
- Voix Fish Audio : vérifier les conditions du modèle et du service ; la voix clonée est celle de l'utilisateur.
- Musique ACE-Step : modèles ouverts, vérifier la case « commercial use » de la version utilisée.
- Freesound : CC0 ou CC-BY uniquement ; crédits générés. Éviter CC-BY-NC.
- Polices : JetBrains Mono (OFL), Archivo Black (OFL).
- YouTube : déclarer le contenu synthétique réaliste.
