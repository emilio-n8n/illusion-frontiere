# 02 — Génération d'assets

## Images : Krea 2 Turbo

### Débit réel

- 1024 px, 16:9, 8 steps : **~31–40 s/image** (le « 21 s » annoncé n'est pas tenu).
- 1536 px : **~77–85 s/image**.
- 130 images à 1024 : **79 min** de génération, plus les reprises.
- Prévoir 1 image = 1 requête, pas de batch parallèle : le serveur fait la queue.

### Prompt

Structure qui a tenu :

```
[SUJET + ACTION] + [CAMÉRA/OBJECTIF] + [LUMIÈRE/PALETTE] + [COMPOSITION]
+ look maison (style.json) + negative (texte, collage, UI, anatomie...)
```

Look maison (extrait) :

> Underexposed 35mm film still from a dark cinematic documentary. Photorealistic, coherent single scene with real spatial depth and a believable camera position. Deep blue-black shadows, steel-blue ambient light, muted burgundy practical accents, pale silver highlights, never a warm orange grade. Thin volumetric haze, natural shallow depth of field, subtle anamorphic character, fine film grain, physically plausible materials, muted desaturated palette. Clean unmarked surfaces.

Negative clé :

> collage, photo montage, cut-out, split screen, infographic, illustration, vector art, cartoon, anime, 3d render, CGI, plastic skin, oversaturated colors, neon purple, glowing hologram, futuristic UI, HUD, text, letters, words, typography, watermark, logo, border, frame, poster layout, low resolution, deformed anatomy.

### Erreurs d'images constatées

- **Texte parasite** : les écrans (scanner, moniteur de labo, téléphone) génèrent des labels/UI. Il faut soit régénérer avec « no labels, no UI, blank screen », soit éviter les écrans dans le motif.
- **Anatomie** : mains parfois plastiques, visages d'enfants parfois trop âgés. À contrôler à l'œil ; le grain et le mouvement pardonnent beaucoup.
- **Doublons de motif** : la banque de 15 motifs par acte se répète tous les 15 blocs. Ce n'est pas un doublon d'image (fichiers différents) mais un motif qui revient ; varier la caméra/lumière aide.
- **Cohérence** : les images 1024 sont plus douces que les 1536 ; le moteur upscale et ajoute du grain, acceptable.

### Bonnes pratiques

- Une image par bloc, dès le début.
- Seeds fixes et sidecars.
- Un batch reprenable : ne pas régénérer ce qui existe.
- QC par échantillon + OCR éventuel (tesseract a raté les petits labels, ne pas s'y fier seul).
- Nommer les fichiers par bloc (`N011-A`), pas par sujet.

## Depth maps : Depth Anything V2

### Ce qui a marché

```python
# dans Colab, après git clone du repo officiel + timm + checkpoint vits
import sys; sys.path.insert(0, "/content/da2")
from depth_anything_v2.dpt import DepthAnythingV2
m = DepthAnythingV2(encoder="vits", features=64, out_channels=[48, 96, 192, 384])
m.load_state_dict(torch.load("/content/ckpts/vits.pth", map_location="cpu"))
m = m.to("cuda").eval()
d = m.infer_image(cv2.imread(path))  # float, normaliser, sauver en 16-bit
```

- 26 cartes en ~5 min sur T4.
- Profondeur correcte : silhouette détachée, premier plan lumineux, fond noir.
- Stocker en PNG 16-bit dans `assets/depth/`.

### Ce qui a échoué

- `pip install git+https://github.com/DepthAnything/Depth-Anything-V2.git` : pas de `setup.py`/`pyproject.toml`.
- `transformers` + `Depth-Anything-V2-Small` : pas de `preprocessor_config.json`.
- Solution : cloner le repo et importer `depth_anything_v2.dpt` directement.

## 2.5D : Blender photo_depth

- `blender/photo_depth.py` : grille 320×180, image en émission, depth en displacement, caméra.
- Moves : `push-in`, `push-out`, `pan-left`, `pan-right`, `drift`.
- Rendu brut, sans grade : le moteur applique le grade.
- Coût : ~8 s/frame à 540p, ~25 s/frame à 1080p sur CPU ; 6 s de clip = 2–3 min.
- **26 clips produits, non utilisés dans le montage v2** (les 130 images uniques ont pris le dessus). C'est le principal sunk cost du projet.

## Voix : Fish Audio Drama 3

### Configuration

- Référence : 10 s de la voix de l'utilisateur, WAV mono 44,1 kHz.
- Transcript exact de la référence (obligatoire pour le clonage).
- Direction par acte : `[calm, low voice, intimate documentary narrator, slow, close to the microphone]`, etc.
- Une prise par bloc, seed fixe, `one_pass=true`.

### Débit

- RTF ~3,6–8 : une prise de 15 s prend 55–120 s.
- 70 blocs : **~2 h** au total, hors relances.
- Le tunnel Gradio tombe régulièrement : un batch peut échouer à 27/70, 53/70, 70/70.

### Pièges

- **Upload de fichier** : Gradio 6 exige un `FileData` (`{path, meta}`), pas un chemin local. Utiliser `/gradio_api/upload`.
- **404** : le tunnel a expiré ; reprendre sans `--force` pour ne pas refaire les blocs existants.
- **Coutures** : les blocs sont collés sans silence ; on entend la transition. Ajouter 0,25 s de silence et 0,15 s de poignée pour le prochain film.
- **Débit** : le clone est lent (~123 mots/min). L'utilisateur a validé 35 min max, donc on n'accélère pas.

## Musique : ACE-Step 1.5

- 6 nappes M00–M05, 90–120 s, 48 kHz stéréo.
- Prompts par acte dans `audio/music.json`.
- **Le serveur exige `init_engine` avant `generate_music_ui`**, sinon l'appel échoue (`data: null`).
- Débit : 6 nappes en 3 min 20.
- Mapping par acte : attention aux sous-chaînes (`ACTE I` matchait `ACTE II`) ; utiliser `startsWith('ACTE I ')`.

## SFX

- 18 textures générées (room tones, hums, riser, drop, heartbeat, projecteur, bande, IRM).
- 10 foley Freesound (projecteur, tiroir, pas, porte, pluie, néon, tampon, bande).
- Filtre de licence : CC0 ou CC-BY uniquement ; crédits générés dans `audio/foley-credits.md`.
- **Aucun SFX n'est encore placé** dans le montage v2.

## Licences

- Krea : vérifier les conditions commerciales du service.
- Fish Audio : vérifier les conditions du modèle et du service.
- ACE-Step : vérifier la case commercial use.
- Freesound : CC0/CC-BY, jamais CC-BY-NC.
- Polices : JetBrains Mono OFL, Archivo Black OFL.
- YouTube : déclarer le contenu synthétique réaliste.
