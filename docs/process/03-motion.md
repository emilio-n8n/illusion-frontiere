# 03 — Motion design Vox, version archive

## Principe

Le motion design ne doit **pas** ressembler à une infographie Vox posée sur une vidéo sombre. Il doit être **projeté dans le monde du film** : mêmes noirs, même écran pâle, même rouge encre, même grain. On garde la grammaire Vox (chiffres, barres, timeline, brackets, annotations) mais avec la palette et la texture de l'archive.

Règles :

- Typographie : Archivo Black pour les nombres/titres, JetBrains Mono pour les labels.
- Couleurs : `#C9C4B8` (pâle), `#A81F16` (rouge), `#A1A1A0` (gris), fond transparent.
- Pas de blanc pur, pas de jaune/bleu vif, pas de carte opaque.
- Traits fins, beaucoup de vide, un seul accent rouge par graphique.
- Les graphiques sont dessinés **après le grade et la vignette, avant le grain et les scanlines** : ils sont ainsi texturés par la pellicule.
- Jamais plus de 8 insertions dans un film de 26 min.

## Types implémentés

| Type | Usage | Exemple |
|---|---|---|
| `number` | chiffre qui compte, label, sous-label | 800 000 neurones |
| `dots` | grille de points + chiffre | 86 milliards, 1 point = 540 M |
| `bars` | comparaison de deux valeurs | DishBrain 800k vs FinalSpark 160k |
| `brackets` | cadrage Vox autour d'un sujet, date | 1953, mémoire |
| `timeline` | frise horizontale, années | 1950 → 1953 → 2022 → 2024 |
| `redact` | barres de censure + tampon | « CONSCIENT : PRÉSUMÉ » |
| `frontier` | ligne qui se trace puis s'efface | « la frontière n'est pas une ligne » |
| `diagram` | boucle de 3 nœuds | expérience → erreur → ajustement |

## Schéma JSON

`films/01-illusion-frontiere/storyboard/motion.json` :

```json
{
  "motions": {
    "N011": [{
      "type": "dots",
      "value": 86,
      "unit": "MILLIARDS",
      "label": "NEURONES DANS UN CERVEAU D'ENFANT",
      "legend": "1 POINT = 540 MILLIONS",
      "at": 4.26,
      "dur": 5.2,
      "x": 1010, "y": 150, "w": 760, "h": 470,
      "highlight": 0.35
    }]
  }
}
```

- `at` est relatif au début du bloc, en secondes.
- `x/y/w/h` sont en coordonnées 1920×1080.
- Le builder injecte `motions` dans le bloc ; le renderer les dessine.

## Calage sur la voix

Sans timings de mots, on estime la position de la phrase dans le bloc :

```python
at = index_de_la_phrase / len(texte) * duree_du_bloc
```

Puis `dur = min(dur_prevu, duree_bloc - at)`. C'est approximatif mais suffisant : les graphiques tombent dans la bonne zone.

Exemples calés :

| Bloc | Graphique | `at` |
|---|---|---|
| N011 | 86 milliards | 4,26 s |
| N020 | 1953 / mémoire | 0,4 s |
| N032 | 800 000 | 12,69 s |
| N034 | barres 800k/160k | 12,47 s |
| N055 | timeline | 0,4 s |
| N061 | censure + tampon | 44,39 s |
| N070 | frontière | 0,4 s |

## Intégration dans le renderer

Ordre de dessin d'une frame :

```
shot (image ou clip)
→ grade
→ vignette
→ drawMotions(block.motions)
→ grain
→ scanlines
→ poussière
→ overlay bas-gauche
→ sous-titre
→ HUD
→ fade du bloc
```

Fonctions dans `studio/render.html` :

- `motionAlpha(local, m)` : fade in/out.
- `drawMotion(m, local)` : un type.
- `drawMotions(t)` : boucle sur `block.motions`.

## Erreurs constatées

### 1. `out` n'existait pas

Les fonctions utilisaient `out(t)` (ease-out cubique), défini dans l'ancien prototype mais **pas** dans `render.html`. Erreur `ReferenceError: out is not defined` au premier still avec brackets/timeline. Correction : ajouter `const out = t => 1 - Math.pow(1 - clamp(t), 3);`.

### 2. Le graphique ne correspond pas à l'image

N020 : brackets « H.M. — 1953 » autour d'une **montre**. Les images sont générées par banque de motifs, pas par sens strict. Correction : label générique « 1953 / MÉMOIRE ». Règle : **vérifier l'image derrière chaque graphique** avant de garder un label littéral.

### 3. Barres de censure sur un écran blanc

N061 : les barres noires tombent sur un écran de projection, pas sur un dossier. Visuellement, ça lit comme une projection censurée ; c'est acceptable, mais ce n'était pas l'intention. Règle : choisir un plan de dossier pour `redact`, ou assumer l'effet « on censure l'écran ».

### 4. Ligne de frontière confondue avec le décor

N070 : la ligne verticale tombait sur le bord de la porte, donc invisible. Correction : déplacer à `x = W*0.34`, ajouter un glow rouge et des labels NOUS/EUX. Règle : **la ligne doit traverser une zone sombre**, pas un bord déjà présent.

### 5. Chronologie trop chargée

Trop de graphiques au même endroit = fatigue. On a limité à 8 insertions, avec des blocs respirables entre. Règle : un graphique par idée, pas un graphique par phrase.

### 6. Texte trop petit / trop faint

Les labels mono à 11–13 px et alpha 0.4 sont illisibles sur téléphone. Correction : 14–16 px, alpha 0.7–0.9, et un léger shadow. Règle : tester la miniature du graphique à 25 % de sa taille.

### 7. Le still ne montre pas le mouvement

Normal : un still fige le graphique. Le motion est dans le temps (compte, barres qui poussent, ligne qui se trace, tampon qui s'abat). Ne pas juger le motion sur un still ; rendre 2–3 s de preview.

## Ce qui a bien marché

- Le contraste pâle/rouge sur les images sombres.
- Les barres DishBrain/FinalSpark, lisibles et informatives.
- La timeline, très Vox, mais intégrée par la typo mono et le rouge.
- Le tampon « CONSCIENT : PRÉSUMÉ », qui reprend le twist du script.
- La frontière qui s'efface, qui est une idée visuelle, pas une décoration.

## Pour le prochain film

- Construire les graphiques **après** le choix des images, pour éviter les mismatches.
- Garder un fichier `motion.json` par film, avec un type par idée.
- Rendre un preview de 3 s par graphique avant le rendu complet.
- Ne jamais dépasser 30 % du film en motion design.
