#!/usr/bin/env python3
"""Batch image generation for the film, resumable and safe to interrupt.

Reads the storyboard manifest, appends the house look, calls the Gradio
endpoint one image at a time, and writes a sidecar + a status file.

Usage:
  python3 tools/batch_generate.py
  python3 tools/batch_generate.py --limit 4
  python3 tools/batch_generate.py --only B00-S01,B00-S02
  python3 tools/batch_generate.py --force
"""

import argparse
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from imagine import API, DEFAULT_URL, download, pick_image, post_json, stream_event  # noqa: E402

MANIFEST = ROOT / "films/01-illusion-frontiere/storyboard/shots.json"
STYLE = ROOT / "films/01-illusion-frontiere/prompts/style.json"
OUT = ROOT / "assets/generated"
STATUS = OUT / "status.json"


def now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def load_status():
    if STATUS.exists():
        try:
            return json.loads(STATUS.read_text())
        except Exception:
            return {}
    return {}


def save_status(status):
    OUT.mkdir(parents=True, exist_ok=True)
    tmp = STATUS.with_suffix(".tmp")
    tmp.write_text(json.dumps(status, indent=2, ensure_ascii=False) + "\n")
    tmp.replace(STATUS)


def valid_image(path):
    if not path.exists() or path.stat().st_size < 20_000:
        return False
    head = path.read_bytes()[:8]
    return head.startswith(b"\x89PNG") or head.startswith(b"\xff\xd8")


def compose_prompt(shot, style):
    look = style["look"].strip()
    # The shot prompts already carry the opening sentence of the look.
    tail = look.split(". ", 1)[1] if ". " in look else look
    return shot["prompt"].strip() + " " + tail


def generate_one(shot, style, base, out_dir, force=False):
    out = out_dir / f"{shot['id']}.png"
    if valid_image(out) and not force:
        return {"status": "skipped", "file": str(out.relative_to(ROOT)), "seconds": 0}

    prompt = compose_prompt(shot, style)
    negative = style["negative"]
    if shot.get("negativeExtra"):
        negative = negative + ", " + shot["negativeExtra"]
    t0 = time.time()
    res = post_json(
        f"{base}/gradio_api/call/{API}",
        {"data": [prompt, negative, style["settings"].get("style", "None"),
                  style["settings"].get("steps", 8), style["settings"].get("aspect", "16:9 Landscape"),
                  shot.get("resolution", style["settings"].get("resolution", "1024px (Standard)")),
                  shot["seed"], 1, style["settings"].get("nag", 1.25)]},
    )
    event_id = res.get("event_id")
    if not event_id:
        raise RuntimeError(f"no event_id: {res}")
    payload = stream_event(f"{base}/gradio_api/call/{API}/{event_id}")
    gallery = payload[0] if payload else []
    status_text = payload[1] if len(payload) > 1 else ""
    src = pick_image(gallery)
    if not src:
        raise RuntimeError(f"no image in response: {gallery!r}")
    download(base, src, out)
    if not valid_image(out):
        raise RuntimeError(f"downloaded file is not a valid image: {out}")

    meta = {
        "id": shot["id"],
        "block": shot["block"],
        "act": shot["act"],
        "title": shot["title"],
        "prompt": prompt,
        "negative": negative,
        "seed": shot["seed"],
        "resolution": shot.get("resolution"),
        "aspect": style["settings"].get("aspect"),
        "steps": style["settings"].get("steps"),
        "nag": style["settings"].get("nag"),
        "endpoint": base,
        "server_status": status_text,
        "seconds": round(time.time() - t0, 1),
        "generated_at": now(),
    }
    (out_dir / f"{shot['id']}.json").write_text(json.dumps(meta, indent=2, ensure_ascii=False) + "\n")
    return {"status": "ok", "file": str(out.relative_to(ROOT)), "seconds": meta["seconds"]}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", default=str(MANIFEST))
    ap.add_argument("--style", default=str(STYLE))
    ap.add_argument("--out", default=str(OUT))
    ap.add_argument("--url", default=DEFAULT_URL)
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--only", default="")
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--sleep", type=float, default=1.0)
    args = ap.parse_args()

    manifest = json.loads(Path(args.manifest).read_text())
    style = json.loads(Path(args.style).read_text())
    shots = manifest["shots"]
    if args.only:
        wanted = {x.strip() for x in args.only.split(",") if x.strip()}
        shots = [s for s in shots if s["id"] in wanted]
    if args.limit:
        shots = shots[: args.limit]

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    status = load_status()
    base = args.url.rstrip("/")

    print(f"batch: {len(shots)} shot(s), endpoint {base}", flush=True)
    t_start = time.time()
    for i, shot in enumerate(shots, 1):
        print(f"[{i}/{len(shots)}] {shot['id']} — {shot['title']} — seed {shot['seed']}", flush=True)
        try:
            result = generate_one(shot, style, base, out_dir, force=args.force)
        except Exception as exc:  # keep the batch alive
            print(f"  ! {type(exc).__name__}: {exc}", flush=True)
            status[shot["id"]] = {"status": "error", "error": str(exc), "at": now()}
            save_status(status)
            time.sleep(3)
            continue
        status[shot["id"]] = {**result, "at": now()}
        save_status(status)
        print(f"  {result['status']} in {result['seconds']}s", flush=True)
        time.sleep(args.sleep)

    elapsed = time.time() - t_start
    ok = sum(1 for s in status.values() if s.get("status") == "ok")
    errors = sum(1 for s in status.values() if s.get("status") == "error")
    print(f"done: {ok} ok, {errors} error(s), {elapsed/60:.1f} min", flush=True)


if __name__ == "__main__":
    main()
