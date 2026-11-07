#!/usr/bin/env python3
"""Generate the French voice-over with Fish Audio Drama 3 (Gradio endpoint).

Single line:
  python3 tools/drama_voice.py --text "[calm] Bonjour." -o assets/voice-test/test.wav

Narration blocks:
  python3 tools/drama_voice.py --blocks --only N001,N002,N003
  python3 tools/drama_voice.py --blocks
  python3 tools/drama_voice.py --blocks --force --only N001

Optional voice cloning:
  python3 tools/drama_voice.py --blocks --ref path/to/ref.wav --ref-transcript "exact words"
"""

import argparse
import json
import mimetypes
import os
import sys
import time
import urllib.request
import uuid
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from imagine import download, post_json, stream_event  # noqa: E402

DEFAULT_URL = os.environ.get("DRAMA_URL", "https://915cd4357dc265ed4e.gradio.live")
BLOCKS = ROOT / "films/01-illusion-frontiere/script/blocks.json"
OUT_DIR = ROOT / "films/01-illusion-frontiere/audio/blocks"
STATUS = ROOT / "films/01-illusion-frontiere/audio/voice-status.json"

DIRECTIONS = {
    "PROLOGUE": "[calm, low voice, intimate documentary narrator, slow, close to the microphone]",
    "APPRENDRE": "[calm, curious, measured, telling a story]",
    "MÉMOIRE": "[soft, reflective, slightly distant, slow]",
    "CORPS": "[low, serious, tense, controlled]",
    "ÉMOTION": "[intimate, gentle, close, a little fragile]",
    "CONSCIENCE": "[quiet, philosophical, slower, searching]",
    "FRONTIÈRE": "[soft, almost a whisper, then warm and direct]",
}


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


_UPLOAD_CACHE = {}


def upload_file(base, local):
    """Upload a local file to the Gradio server, return a FileData dict.

    The /run endpoint validates file inputs with pydantic: a plain local path
    string is rejected, it wants {'path': <server path>, 'meta': {...}}.
    """
    key = f"{base}|{local}"
    if key in _UPLOAD_CACHE:
        return _UPLOAD_CACHE[key]
    local = Path(local)
    mime = mimetypes.guess_type(local.name)[0] or "application/octet-stream"
    boundary = "----Boundary" + uuid.uuid4().hex
    body = bytearray()
    body += f"--{boundary}\r\n".encode()
    body += f'Content-Disposition: form-data; name="files"; filename="{local.name}"\r\n'.encode()
    body += f"Content-Type: {mime}\r\n\r\n".encode()
    body += local.read_bytes()
    body += f"\r\n--{boundary}--\r\n".encode()
    req = urllib.request.Request(
        base + "/gradio_api/upload",
        data=bytes(body),
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=120) as r:
        server_paths = json.loads(r.read().decode())
    filedata = {"path": server_paths[0], "meta": {"_type": "gradio.FileData"}}
    _UPLOAD_CACHE[key] = filedata
    return filedata


def perform(base, text, ref, ref_transcript, temperature, top_p, max_frames, seed, one_pass):
    if isinstance(ref, (str, Path)) and ref and Path(ref).exists():
        ref = upload_file(base, ref)
    payload = {"data": [text, ref, ref_transcript, temperature, top_p, max_frames, seed, one_pass]}
    res = post_json(f"{base}/gradio_api/call/run", payload)
    event_id = res.get("event_id")
    if not event_id:
        raise RuntimeError(f"no event_id: {res}")
    out = stream_event(f"{base}/gradio_api/call/run/{event_id}", timeout=900)
    audio = out[0] if out else None
    status_text = out[1] if len(out) > 1 else ""
    src = pick_audio(audio)
    if not src:
        raise RuntimeError(f"no audio in response: {out!r}")
    return src, status_text


def generate_block(base, block, direction, args, out_dir):
    out = out_dir / f"{block['id']}.wav"
    if out.exists() and out.stat().st_size > 2000 and not args.force:
        return {"status": "skipped", "file": str(out.relative_to(ROOT)), "seconds": 0}

    text = f"{direction} {block['text']}".strip()
    t0 = time.time()
    src, status_text = perform(
        base, text, args.ref, args.ref_transcript,
        args.temperature, args.top_p, args.max_frames, args.seed, not args.chunked,
    )
    out.parent.mkdir(parents=True, exist_ok=True)
    download(base, src, out)
    if out.stat().st_size < 2000:
        raise RuntimeError(f"audio too small: {out}")
    meta = {
        "id": block["id"],
        "act": block["act"],
        "text": block["text"],
        "direction": direction,
        "seed": args.seed,
        "temperature": args.temperature,
        "top_p": args.top_p,
        "one_pass": not args.chunked,
        "reference": args.ref,
        "reference_transcript": args.ref_transcript,
        "server_status": status_text,
        "seconds": round(time.time() - t0, 1),
        "generated_at": now(),
    }
    (out_dir / f"{block['id']}.json").write_text(json.dumps(meta, indent=2, ensure_ascii=False) + "\n")
    return {"status": "ok", "file": str(out.relative_to(ROOT)), "seconds": meta["seconds"]}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--text")
    ap.add_argument("--text-file")
    ap.add_argument("-o", "--out", default="assets/voice-test/take.wav")
    ap.add_argument("--blocks", action="store_true")
    ap.add_argument("--only", default="")
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--out-dir", default=str(OUT_DIR))
    ap.add_argument("--ref", default=None, help="5-30 s reference clip for voice cloning")
    ap.add_argument("--ref-transcript", default="", help="exact transcript of the reference clip")
    ap.add_argument("--seed", type=int, default=424242)
    ap.add_argument("--temperature", type=float, default=0.7)
    ap.add_argument("--top-p", type=float, default=0.7)
    ap.add_argument("--max-frames", type=int, default=0)
    ap.add_argument("--chunked", action="store_true", help="let the model split the text into chunks")
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--url", default=DEFAULT_URL)
    args = ap.parse_args()
    base = args.url.rstrip("/")

    if args.blocks:
        data = json.loads(BLOCKS.read_text())
        blocks = data["blocks"]
        if args.only:
            wanted = {x.strip() for x in args.only.split(",") if x.strip()}
            blocks = [b for b in blocks if b["id"] in wanted]
        if args.limit:
            blocks = blocks[: args.limit]
        out_dir = Path(args.out_dir)
        if not out_dir.is_absolute():
            out_dir = ROOT / out_dir
        out_dir.mkdir(parents=True, exist_ok=True)
        status = load_status()
        print(f"voice: {len(blocks)} block(s), endpoint {base}", flush=True)
        t_start = time.time()
        for i, block in enumerate(blocks, 1):
            direction = DIRECTIONS.get(block["act"].upper(), DIRECTIONS["PROLOGUE"])
            print(f"[{i}/{len(blocks)}] {block['id']} — {block['act']} — {block['seconds']}s text", flush=True)
            try:
                result = generate_block(base, block, direction, args, out_dir)
            except Exception as exc:
                print(f"  ! {type(exc).__name__}: {exc}", flush=True)
                status[block["id"]] = {"status": "error", "error": str(exc), "at": now()}
                save_status(status)
                time.sleep(3)
                continue
            status[block["id"]] = {**result, "at": now()}
            save_status(status)
            print(f"  {result['status']} in {result['seconds']}s", flush=True)
        elapsed = time.time() - t_start
        ok = sum(1 for s in status.values() if s.get("status") == "ok")
        errors = sum(1 for s in status.values() if s.get("status") == "error")
        print(f"done: {ok} ok, {errors} error(s), {elapsed/60:.1f} min", flush=True)
        return 0

    text = args.text
    if args.text_file:
        text = Path(args.text_file).read_text().strip()
    if not text:
        ap.error("--text, --text-file or --blocks is required")
    t0 = time.time()
    src, status_text = perform(
        base, text, args.ref, args.ref_transcript,
        args.temperature, args.top_p, args.max_frames, args.seed, not args.chunked,
    )
    out = Path(args.out)
    download(base, src, out)
    print(f"✓ {out} ({out.stat().st_size/1024:.0f} KB, {time.time()-t0:.1f}s)")
    print(f"  server: {status_text}")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:
        print(f"error: {type(exc).__name__}: {exc}", file=sys.stderr)
        sys.exit(1)
