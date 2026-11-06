#!/usr/bin/env python3
"""Measure the recorded voice-over blocks and update the block timings.

Place files in films/01-illusion-frontiere/audio/blocks/N001.wav (or .mp3/.flac),
then run: python3 tools/measure_audio.py
"""

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BLOCKS = ROOT / "films/01-illusion-frontiere/script/blocks.json"
AUDIO_DIR = ROOT / "films/01-illusion-frontiere/audio/blocks"
OUT = ROOT / "films/01-illusion-frontiere/audio/durations.json"


def ffprobe_duration(path):
    r = subprocess.run([
        "ffprobe", "-v", "error", "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1", str(path),
    ], capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(r.stderr.strip() or f"ffprobe failed: {path}")
    return float(r.stdout.strip())


def main():
    data = json.loads(BLOCKS.read_text())
    found = {}
    for block in data["blocks"]:
        for ext in (".wav", ".flac", ".mp3", ".m4a"):
            candidate = AUDIO_DIR / f"{block['id']}{ext}"
            if candidate.exists():
                found[block["id"]] = candidate
                break

    if not found:
        print(f"no audio found in {AUDIO_DIR.relative_to(ROOT)}")
        return 1

    total = 0.0
    measured = 0
    for block in data["blocks"]:
        path = found.get(block["id"])
        if not path:
            total += block["seconds"]
            continue
        duration = ffprobe_duration(path)
        block["seconds"] = round(duration, 3)
        block["audio"] = str(path.relative_to(ROOT))
        block["measured"] = True
        total += duration
        measured += 1

    data["totalSeconds"] = round(total, 3)
    data["measuredBlocks"] = measured
    BLOCKS.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n")
    OUT.write_text(json.dumps({
        "totalSeconds": round(total, 3),
        "measured": measured,
        "total": len(data["blocks"]),
        "blocks": {b["id"]: b["seconds"] for b in data["blocks"]},
    }, ensure_ascii=False, indent=2) + "\n")

    print(f"{measured}/{len(data['blocks'])} blocks measured — total {total/60:.2f} min")
    missing = [b["id"] for b in data["blocks"] if not b.get("measured")]
    if missing:
        print(f"still estimated: {', '.join(missing)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
