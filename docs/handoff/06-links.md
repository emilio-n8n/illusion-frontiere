# Liens et accès

## Dépôt

- GitHub : https://github.com/emilio-n8n/illusion-frontiere (public)
- Branche : `main`
- Actions : https://github.com/emilio-n8n/illusion-frontiere/actions

## Releases

- `film-final-v1` : https://github.com/emilio-n8n/illusion-frontiere/releases/tag/film-final-v1
  - `film-final-intro.mp4` — 26:02, 1080p, voix + musique, ouverture 6 s.
- `proof-clips-v1` : https://github.com/emilio-n8n/illusion-frontiere/releases/tag/proof-clips-v1
  - `film-proof-clips.mp4` — 2:45, 1080p, 26 travelling 2.5D.

## Endpoints temporaires

Les tunnels `*.gradio.live` expirent. Ne pas les coder en dur dans un script de production ; toujours passer l'URL en argument ou par variable d'environnement.

- Krea 2 Turbo (images) : dernier lien fourni `https://e6eff52740741708d0.gradio.live` (à vérifier).
- Fish Audio Drama 3 (voix) : dernier lien `https://991aaf9f8a5a5f8c0d.gradio.live` (à vérifier).
- ACE-Step 1.5 (musique) : dernier lien `https://e6322dd83157129528.gradio.live` (à vérifier).

## Secrets

- Clé Freesound : `~/.config/illusion-frontiere/freesound.key` (chmod 600, hors dépôt).
- GitHub : `gh` authentifié sur `emilio-n8n`.

## Commandes utiles

```bash
gh run list --workflow=render --limit 5
gh run view <run-id> --json status,conclusion,jobs
gh run download <run-id> -n film-silent -D /tmp/opencode/actions-final
gh release create <tag> <file> --title "..." --notes "..."
```

## Rendu final v1 (local)

- `out/film-final-intro.mp4` — 26:02, 395 Mo.
- `out/film-final.mp4` — version sans carton d'ouverture.
- `out/audio/mix.wav` — voix + musique.
- `out/audio/mix-lead.wav` — avec 6 s d'ouverture musicale.
- `out/intro.mp4` — carton titre 6 s.
