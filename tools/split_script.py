#!/usr/bin/env python3
"""Split the narration script into recordable blocks (one paragraph = one block).

The block list is the bridge between writing and production: each block gets an
id, a word count and an estimated duration. When the real voice is recorded, its
measured duration replaces the estimate.

Outputs:
  films/01-illusion-frontiere/script/blocks.json
  films/01-illusion-frontiere/script/blocks.md
"""

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "films/01-illusion-frontiere/script/script-v1.md"
OUT_JSON = ROOT / "films/01-illusion-frontiere/script/blocks.json"
OUT_MD = ROOT / "films/01-illusion-frontiere/script/blocks.md"

WPM = 165.0
TAIL = 0.5

SHOTS = {
    "PROLOGUE": ["B00-S01", "B00-S02", "B00-S03"],
    "APPRENDRE": ["B01-S01", "B01-S02", "B01-S03", "B01-S04"],
    "MÉMOIRE": ["B02-S01", "B02-S02", "B02-S03", "B02-S04"],
    "CORPS": ["B03-S01", "B03-S02", "B03-S03", "B03-S04"],
    "ÉMOTION": ["B04-S01", "B04-S02", "B04-S03", "B04-S04"],
    "CONSCIENCE": ["B05-S01", "B05-S02", "B05-S03", "B05-S04"],
    "FRONTIÈRE": ["B06-S01", "B06-S02", "B06-S03"],
}


def shots_for(act):
    upper = act.upper()
    for key, shots in SHOTS.items():
        if key in upper:
            return shots
    return ["B00-S01"]


RULES = [
    (r"enfant|marche|tombe|chute|genoux|corps qui a faim", ["B01-S01", "B01-S02"]),
    (r"apprend|erreur|gradient|entraîn|modèle|fine-tuning|préféré|retour humain", ["B01-S03", "B01-S04"]),
    (r"1953|H\.M\.|souvenir|mémoire|oublie|consolidation|disque dur|contexte", ["B02-S01", "B02-S02", "B02-S03"]),
    (r"hallucine|paramètres|restituer|passé à protéger", ["B02-S04", "B02-S03"]),
    (r"robot|corps|main|douleur|souffre|capteur|prothèse|interface", ["B03-S01", "B03-S02"]),
    (r"neurones|organoïdes|Cortical|FinalSpark|biocomputing|petri|biologique|silicium", ["B03-S03", "B03-S04"]),
    (r"émotion|téléphone|chatbot|programme|aimée|solitude|relation|trois heures", ["B04-S01", "B04-S02", "B04-S03"]),
    (r"conscience|Turing|expérience|qualia|miroir|autre esprit|problème difficile", ["B05-S01", "B05-S02", "B05-S03"]),
    (r"dossier|archiviste|frontière|tiroir|meuble|Bureau", ["B00-S01", "B00-S02", "B06-S02"]),
]

def pick_shots(text, act, i):
    upper = act.upper()
    if "PROLOGUE" in upper:
        return ["B00-S01", "B00-S02", "B00-S03"]
    if "FRONTIÈRE" in upper or "FINALE" in upper:
        return ["B06-S01", "B06-S02", "B06-S03"]
    low = text.lower()
    for pattern, shots in RULES:
        if re.search(pattern, low, re.I):
            a = shots[i % len(shots)]
            b = shots[(i + 1) % len(shots)]
            return [a] if a == b else [a, b]
    return shots_for(act)


def words(text):
    return re.findall(r"[A-Za-zÀ-ÖØ-öø-ÿ0-9'’\-]+", text)


def main():
    lines = SCRIPT.read_text().splitlines()
    blocks = []
    act = ""
    started = False
    buf = []

    def flush():
        nonlocal buf
        text = " ".join(x.strip() for x in buf).strip()
        buf = []
        if not text:
            return
        if text.startswith("Note d'intention") or text.startswith("Logline"):
            return
        w = words(text)
        if len(w) < 6:
            return
        n = len(blocks) + 1
        blocks.append({
            "id": f"N{n:03d}",
            "act": act,
            "text": text,
            "words": len(w),
            "seconds": round(len(w) / WPM * 60 + TAIL, 1),
            "suggestedShots": pick_shots(text, act, len(blocks)),
        })

    for raw in lines:
        line = raw.rstrip()
        if line.startswith("## "):
            flush()
            started = True
            act = line[3:].strip()
            continue
        if not started:
            continue
        if not line.strip():
            flush()
            continue
        if line.startswith("#") or line.startswith("*[") or line.startswith("*Durée") or line.startswith("**") or line.startswith(">") or line.startswith("---"):
            flush()
            continue
        buf.append(line)

    flush()
    total = sum(b["seconds"] for b in blocks)

    OUT_JSON.write_text(json.dumps({
        "source": str(SCRIPT.relative_to(ROOT)),
        "wpm": WPM,
        "totalSeconds": round(total, 1),
        "blocks": blocks,
    }, ensure_ascii=False, indent=2) + "\n")

    md = ["# Blocs de narration — script v1", ""]
    md.append(f"{len(blocks)} blocs · {total/60:.1f} min estimées à {WPM:.0f} mots/min · une prise par bloc.")
    md.append("")
    md.append("> Enregistrer chaque bloc dans un fichier séparé (`N001.wav`, `N002.wav`...). ")
    md.append("> La durée réelle de chaque prise remplacera l'estimation et pilotera le montage.")
    md.append("")
    for b in blocks:
        md.append(f"## {b['id']} — {b['act']} — {b['seconds']:.1f}s · {b['words']} mots")
        md.append("")
        md.append(b["text"])
        md.append("")
        md.append(f"*Shots suggérés : {', '.join(b['suggestedShots'])}*")
        md.append("")
    OUT_MD.write_text("\n".join(md) + "\n")

    print(f"{len(blocks)} blocks, {total/60:.1f} min")
    for b in blocks[:5]:
        print(f"  {b['id']} {b['seconds']:.1f}s {b['act'][:24]:24} {b['text'][:60]}")
    print(f"  ... last: {blocks[-1]['id']} {blocks[-1]['seconds']:.1f}s")


if __name__ == "__main__":
    main()
