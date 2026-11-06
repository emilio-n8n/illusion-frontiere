#!/usr/bin/env python3
"""Minimal Gradio client for the Krea-2-Turbo endpoint (stdlib only).

Usage:
  python3 tools/imagine.py "prompt" -o assets/generated/shot-001.png
  python3 tools/imagine.py --prompt-file shot.txt --seed 123 -o out.png

The endpoint is a temporary gradio.live tunnel: pass --url or set GRADIO_URL.
Every generation writes a sidecar .json with the exact prompt, seed and settings
so an asset can always be reproduced.
"""

import argparse
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

DEFAULT_URL = "https://5ddf94cc911b396470.gradio.live"
API = "generate_image"


def post_json(url, payload, timeout=60):
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode())


def stream_event(url, timeout=600):
    req = urllib.request.Request(url, headers={"Accept": "text/event-stream"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        event = None
        for raw in r:
            line = raw.decode("utf-8", "replace").rstrip("\r\n")
            if line.startswith("event:"):
                event = line[6:].strip()
            elif line.startswith("data:"):
                data = line[5:].strip()
                if event == "complete":
                    return json.loads(data)
                if event == "error":
                    raise RuntimeError(data)
                if event == "generating":
                    print("  generating…", flush=True)


def pick_image(value):
    """Gallery values vary between gradio versions: tuple, update dict or str."""
    if isinstance(value, str):
        return value
    if isinstance(value, dict):
        if "url" in value and value["url"]:
            return value["url"]
        for key in ("value", "image", "path", "name"):
            if key in value:
                got = pick_image(value[key])
                if got:
                    return got
        return None
    if isinstance(value, (list, tuple)):
        for item in value:
            got = pick_image(item)
            if got:
                return got
    return None


def download(base, path, out):
    if path.startswith("http"):
        url = path
    else:
        url = base.rstrip("/") + "/gradio_api/file=" + urllib.parse.quote(path)
    req = urllib.request.Request(url)
    out.parent.mkdir(parents=True, exist_ok=True)
    with urllib.request.urlopen(req, timeout=120) as r, open(out, "wb") as f:
        f.write(r.read())
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("prompt", nargs="?", help="positive prompt")
    ap.add_argument("--prompt-file")
    ap.add_argument("--negative", default="")
    ap.add_argument("--negative-file")
    ap.add_argument("-o", "--out", required=True)
    ap.add_argument("--seed", type=int, default=-1)
    ap.add_argument("--steps", type=int, default=8)
    ap.add_argument("--resolution", default="1024px (Standard)",
                    choices=["1024px (Standard)", "1536px (High)", "2048px (2K Ultra)"])
    ap.add_argument("--aspect", default="16:9 Landscape",
                    choices=["16:9 Landscape", "9:16 Portrait", "1:1 Square",
                             "4:3 Standard", "3:4 Portrait"])
    ap.add_argument("--style", default="None",
                    choices=["None", "Cinematic", "Photographic", "Anime",
                             "Cyberpunk", "Fantasy"])
    ap.add_argument("--nag", type=float, default=1.25)
    ap.add_argument("--n", type=int, default=1)
    ap.add_argument("--style-json", help="house look file: look, negative, settings")
    ap.add_argument("--url", default=os.environ.get("GRADIO_URL", DEFAULT_URL))
    args = ap.parse_args()

    prompt = args.prompt
    if args.prompt_file:
        prompt = Path(args.prompt_file).read_text().strip()
    if not prompt:
        ap.error("a prompt or --prompt-file is required")
    negative = args.negative
    if args.negative_file:
        negative = Path(args.negative_file).read_text().strip()

    if args.style_json:
        style = json.loads(Path(args.style_json).read_text())
        settings = style.get("settings", {})
        prompt = prompt.rstrip(". ") + ". " + style["look"]
        negative = negative or style.get("negative", "")
        args.steps = settings.get("steps", args.steps)
        args.resolution = settings.get("resolution", args.resolution)
        args.aspect = settings.get("aspect", args.aspect)
        args.style = settings.get("style", args.style)
        args.nag = settings.get("nag", args.nag)

    base = args.url.rstrip("/")
    t0 = time.time()
    print(f"→ {base}  seed={args.seed}  steps={args.steps}  {args.resolution} / {args.aspect}")
    res = post_json(
        f"{base}/gradio_api/call/{API}",
        {"data": [prompt, negative, args.style, args.steps, args.aspect,
                  args.resolution, args.seed, args.n, args.nag]},
    )
    event_id = res.get("event_id")
    if not event_id:
        raise RuntimeError(f"no event_id: {res}")
    out = stream_event(f"{base}/gradio_api/call/{API}/{event_id}")
    # outputs: [gallery, status, zip]
    gallery = out[0] if out else []
    status = out[1] if len(out) > 1 else ""
    print(f"  server: {status}")

    written = []
    if args.n == 1:
        src = pick_image(gallery)
        if not src:
            raise RuntimeError(f"no image in response: {gallery!r}")
        target = Path(args.out)
        download(base, src, target)
        written.append(target)
    else:
        stem = Path(args.out)
        for i, item in enumerate(gallery):
            src = pick_image(item)
            if not src:
                continue
            target = stem.with_name(f"{stem.stem}-{i+1:02d}{stem.suffix}")
            download(base, src, target)
            written.append(target)

    meta = {
        "prompt": prompt,
        "negative": negative,
        "style": args.style,
        "steps": args.steps,
        "resolution": args.resolution,
        "aspect": args.aspect,
        "seed": args.seed,
        "nag": args.nag,
        "endpoint": base,
        "seconds": round(time.time() - t0, 1),
        "files": [str(p) for p in written],
        "server_status": status,
    }
    Path(str(args.out) + ".json").write_text(json.dumps(meta, indent=2, ensure_ascii=False) + "\n")
    for p in written:
        print(f"✓ {p}  ({p.stat().st_size/1024:.0f} KB, {meta['seconds']}s)")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (urllib.error.URLError, RuntimeError, KeyError) as e:
        print(f"error: {e}", file=sys.stderr)
        sys.exit(1)
