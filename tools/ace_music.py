#!/usr/bin/env python3
"""Generate the film's music beds with ACE-Step 1.5 (Gradio endpoint).

Single take:
  python3 tools/ace_music.py --style "dark ambient drone, ..." -o music-test/drone.wav

Batch (films/01-illusion-frontiere/audio/music.json):
  python3 tools/ace_music.py --batch
  python3 tools/ace_music.py --batch --only M00,M01
"""

import argparse
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from imagine import download, post_json, stream_event  # noqa: E402

DEFAULT_URL = os.environ.get("ACE_URL", "https://e6322dd83157129528.gradio.live")
TRACKS = ROOT / "films/01-illusion-frontiere/audio/music.json"
OUT_DIR = ROOT / "films/01-illusion-frontiere/audio/music"
STATUS = ROOT / "films/01-illusion-frontiere/audio/music-status.json"
API = "generate_music_ui"


def now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def pick_audio(value):
    if isinstance(value, str):
        return value
    if isinstance(value, dict):
        for key in ("url", "path", "name"):
            if value.get(key):
                return value[key]
        for key in ("value", "audio", "data"):
            if key in value:
                got = pick_audio(value[key])
                if got:
                    return got
    if isinstance(value, (list, tuple)):
        for item in value:
            got = pick_audio(item)
            if got:
                return got
    return None


def load_status():
    if STATUS.exists():
        try:
            return json.loads(STATUS.read_text())
        except Exception:
            return {}
    return {}


def save_status(status):
    STATUS.parent.mkdir(parents=True, exist_ok=True)
    tmp = STATUS.with_suffix(".tmp")
    tmp.write_text(json.dumps(status, indent=2, ensure_ascii=False) + "\n")
    tmp.replace(STATUS)


def ensure_engine(base):
    """The server needs its engine initialized once (like the UI button)."""
    try:
        res = post_json(
            f"{base}/gradio_api/call/init_engine",
            {"data": ["acestep-5Hz-lm-0.6B (Fastest & Lightweight - Recommended for T4)"]},
        )
        event_id = res.get("event_id")
        if not event_id:
            return
        out = stream_event(f"{base}/gradio_api/call/init_engine/{event_id}", timeout=300)
        print(f"  engine: {out[0] if out else '?'}", flush=True)
    except Exception as exc:
        print(f"  engine init skipped ({type(exc).__name__}: {exc})", flush=True)


def generate(base, style, duration, seed, bpm=0, key="", timesig="",
             steps=8, guidance=1.0, thinking=False):
    """Returns (track1_url, diagnostics). Lyrics empty + instrumental True."""
    payload = {"data": [style, "", duration, "🇬🇧 English", 1, thinking,
                        seed, bpm, key, timesig, steps, guidance, True]}
    res = post_json(f"{base}/gradio_api/call/{API}", payload)
    event_id = res.get("event_id")
    if not event_id:
        raise RuntimeError(f"no event_id: {res}")
    out = stream_event(f"{base}/gradio_api/call/{API}/{event_id}", timeout=1200)
    audio = out[0] if out else None
    diagnostics = out[2] if len(out) > 2 else ""
    src = pick_audio(audio)
    if not src:
        raise RuntimeError(f"no audio in response: {out!r}")
    return src, diagnostics


def valid_audio(path):
    return path.exists() and path.stat().st_size > 50_000


def generate_track(base, track, out_dir, force=False):
    out = out_dir / f"{track['id']}.wav"
    if valid_audio(out) and not force:
        return {"status": "skipped", "file": str(out.relative_to(ROOT)), "seconds": 0}
    t0 = time.time()
    src, diagnostics = generate(
        base, track["style"], track["duration"], track["seed"],
        bpm=track.get("bpm", 0), key=track.get("key", ""),
        timesig=track.get("timesig", ""),
        steps=track.get("steps", 8), guidance=track.get("guidance", 1.0),
        thinking=track.get("thinking", False),
    )
    out.parent.mkdir(parents=True, exist_ok=True)
    download(base, src, out)
    if not valid_audio(out):
        raise RuntimeError(f"audio too small: {out}")
    meta = {**track, "diagnostics": diagnostics,
            "seconds": round(time.time() - t0, 1), "generated_at": now()}
    (out_dir / f"{track['id']}.json").write_text(
        json.dumps(meta, indent=2, ensure_ascii=False) + "\n")
    return {"status": "ok", "file": str(out.relative_to(ROOT)),
            "seconds": meta["seconds"]}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--style")
    ap.add_argument("--style-file")
    ap.add_argument("-o", "--out", default="assets/music-test/take.wav")
    ap.add_argument("--duration", type=int, default=30)
    ap.add_argument("--seed", type=int, default=9001)
    ap.add_argument("--bpm", type=int, default=0)
    ap.add_argument("--key", default="")
    ap.add_argument("--batch", action="store_true")
    ap.add_argument("--tracks", default=str(TRACKS),
                    help="track list JSON (music.json or sfx.json)")
    ap.add_argument("--outdir", default=None,
                    help="output folder (default: alongside the track list)")
    ap.add_argument("--only", default="")
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--url", default=DEFAULT_URL)
    args = ap.parse_args()
    base = args.url.rstrip("/")
    ensure_engine(base)

    if args.batch:
        tracks_path = Path(args.tracks)
        if not tracks_path.is_absolute():
            tracks_path = ROOT / tracks_path
        tracks = json.loads(tracks_path.read_text())["tracks"]
        if args.only:
            wanted = {x.strip() for x in args.only.split(",") if x.strip()}
            tracks = [t for t in tracks if t["id"] in wanted]
        out_dir = Path(args.outdir) if args.outdir else tracks_path.parent / tracks_path.stem
        if not out_dir.is_absolute():
            out_dir = ROOT / out_dir
        out_dir.mkdir(parents=True, exist_ok=True)
        status = load_status()
        print(f"music: {len(tracks)} track(s), endpoint {base}", flush=True)
        t_start = time.time()
        for i, track in enumerate(tracks, 1):
            print(f"[{i}/{len(tracks)}] {track['id']} — {track['title']} — {track['duration']}s", flush=True)
            try:
                result = generate_track(base, track, out_dir, force=args.force)
            except Exception as exc:
                print(f"  ! {type(exc).__name__}: {exc}", flush=True)
                status[track["id"]] = {"status": "error", "error": str(exc), "at": now()}
                save_status(status)
                time.sleep(3)
                continue
            status[track["id"]] = {**result, "at": now()}
            save_status(status)
            print(f"  {result['status']} in {result['seconds']}s", flush=True)
        elapsed = time.time() - t_start
        ok = sum(1 for s in status.values() if s.get("status") == "ok")
        errors = sum(1 for s in status.values() if s.get("status") == "error")
        print(f"done: {ok} ok, {errors} error(s), {elapsed/60:.1f} min", flush=True)
        return 0

    style = args.style
    if args.style_file:
        style = Path(args.style_file).read_text().strip()
    if not style:
        ap.error("--style, --style-file or --batch is required")
    t0 = time.time()
    src, diagnostics = generate(base, style, args.duration, args.seed,
                                bpm=args.bpm, key=args.key)
    out = Path(args.out)
    download(base, src, out)
    print(f"✓ {out} ({out.stat().st_size/1024:.0f} KB, {time.time()-t0:.1f}s)")
    print(f"  server: {diagnostics}")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:
        print(f"error: {type(exc).__name__}: {exc}", file=sys.stderr)
        sys.exit(1)
