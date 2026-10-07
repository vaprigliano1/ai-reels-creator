#!/usr/bin/env python3
"""Generate audio using the current workspace owner's selected voice/model."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import ssl
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

import certifi
from common import load_env as read_local_env, workspace_profile, workspace_job


API_BASE = "https://api.elevenlabs.io"
TLS_CONTEXT = ssl.create_default_context(cafile=certifi.where())


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_env(path: Path) -> dict[str, str]:
    return read_local_env(path, ("ELEVENLABS_API_KEY", "ELEVENLABS_VOICE_ID", "ELEVENLABS_MODEL_ID"))


def extract_script(path: Path, smoke_test: bool) -> str:
    if path.suffix.lower() == ".txt":
        full = path.read_text(encoding="utf-8").strip()
        return "\n\n".join(full.split("\n\n")[:3]) if smoke_test else full
    match = re.search(r"## Roteiro tagueado\s*```(?:text)?\s*(.*?)```", path.read_text(), re.S)
    if not match:
        raise SystemExit(f"tagged script block not found in {path}")
    full = match.group(1).strip()
    if not smoke_test:
        return full
    paragraphs = full.split("\n\n")
    return "\n\n".join(paragraphs[:3])


def update_job(job_path: Path, step: str, status: str, **fields: object) -> None:
    job = json.loads(job_path.read_text())
    job.setdefault("steps", {})[step] = status
    job["updated_at"] = now()
    for section, values in fields.items():
        if isinstance(values, dict):
            job.setdefault(section, {}).update(values)
        else:
            job[section] = values
    job_path.write_text(json.dumps(job, ensure_ascii=False, indent=2) + "\n")


def generate(api_key: str, voice_id: str, payload: dict[str, object]) -> bytes:
    request = urllib.request.Request(
        f"{API_BASE}/v1/text-to-speech/{voice_id}?output_format=mp3_44100_128",
        data=json.dumps(payload, ensure_ascii=False).encode(),
        headers={"xi-api-key": api_key, "Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=180, context=TLS_CONTEXT) as response:
            audio = response.read()
            if not response.headers.get("Content-Type", "").startswith("audio/"):
                raise RuntimeError("ElevenLabs returned a non-audio response")
            return audio
    except urllib.error.HTTPError as exc:
        raise RuntimeError(f"ElevenLabs HTTP {exc.code}; request may have consumed credits") from None


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--env", type=Path, required=True)
    parser.add_argument("--job-dir", type=Path, required=True)
    parser.add_argument("--script-file", type=Path, required=True)
    parser.add_argument("--smoke-test", action="store_true", help="First three script beats only")
    parser.add_argument("--dry-run", action="store_true", help="Validate without an API call or file writes")
    parser.add_argument("--retry-paid", action="store_true", help="Explicitly retry an uncertain paid request")
    parser.add_argument("--allow-paid", action="store_true", help="Human-authorized generation only")
    parser.add_argument("--max-characters", type=int, default=5000,
                        help="Conservative limit; verify the selected model before changing it")
    args = parser.parse_args()

    env_path = args.env.expanduser().resolve(strict=True)
    env = load_env(env_path)
    job_dir = args.job_dir.expanduser().resolve()
    workspace_job(env_path, job_dir)
    profile = workspace_profile(env_path)
    job_path = job_dir / "job.json"
    if not job_path.is_file():
        raise SystemExit(f"job.json not found in {job_dir}")

    script_path = args.script_file.expanduser().resolve(strict=True)
    if not script_path.is_relative_to(env_path.parent / "videos"):
        raise SystemExit("Script must be inside this workspace's videos/ directory")
    script = extract_script(script_path, args.smoke_test)
    if not script or len(script) > args.max_characters:
        raise SystemExit("Script is empty or exceeds the configured character limit")
    mode = "smoke" if args.smoke_test else "full"
    settings = profile.get("voice_settings", {})
    payload: dict[str, object] = {
        "text": script,
        "model_id": env["ELEVENLABS_MODEL_ID"],
        "language_code": profile["language_code"],
        "voice_settings": settings,
    }
    config = {"voice_id": env["ELEVENLABS_VOICE_ID"], **payload}
    fingerprint = hashlib.sha256(json.dumps(config, sort_keys=True, ensure_ascii=False).encode()).hexdigest()[:12]
    audio_dir = job_dir / "audio"
    out_path = audio_dir / f"elevenlabs_{mode}_{fingerprint}.mp3"
    meta_path = out_path.with_suffix(".json")
    attempt_path = out_path.with_suffix(".attempt.json")
    if args.dry_run:
        print(json.dumps({"mode": mode, "model": payload["model_id"], "language": payload["language_code"], "characters": len(script), "output": str(out_path), "api_calls": 0}, ensure_ascii=False))
        return
    if out_path.is_file() and out_path.stat().st_size > 0 and meta_path.is_file():
        meta = json.loads(meta_path.read_text())
        if meta.get("audio_sha256") == hashlib.sha256(out_path.read_bytes()).hexdigest():
            print(out_path)
            return
        raise SystemExit(f"existing audio failed checksum: {out_path}")
    if out_path.exists():
        raise SystemExit(f"existing audio lacks valid metadata; inspect before regenerating: {out_path}")
    if attempt_path.exists() and not args.retry_paid:
        raise SystemExit(f"previous generation outcome uncertain; inspect {attempt_path} before using --retry-paid")
    if not args.allow_paid:
        raise SystemExit("Generation requires human authorization and --allow-paid")

    audio_dir.mkdir(parents=True, exist_ok=True)
    attempt_path.write_text(json.dumps({"started_at": now(), "mode": mode, "fingerprint": fingerprint}) + "\n")
    step = f"voice_{mode}"
    update_job(job_path, step, "running")
    try:
        audio = generate(env["ELEVENLABS_API_KEY"], env["ELEVENLABS_VOICE_ID"], payload)
        if not audio.startswith(b"ID3") and audio[:2] not in (b"\xff\xfb", b"\xff\xf3", b"\xff\xf2"):
            raise RuntimeError("ElevenLabs returned bytes without an MP3 header")
        out_path.write_bytes(audio)
        meta_path.write_text(json.dumps({
            "created_at": now(),
            "voice_id": env["ELEVENLABS_VOICE_ID"],
            "model_id": payload["model_id"],
            "language_code": payload["language_code"],
            "voice_settings": settings,
            "characters": len(script),
            "script_sha256": hashlib.sha256(script.encode()).hexdigest(),
            "audio_sha256": hashlib.sha256(audio).hexdigest(),
        }, ensure_ascii=False, indent=2) + "\n")
        attempt_path.unlink()
        updates: dict[str, object] = {
            "artifacts": {f"elevenlabs_{mode}": str(out_path)},
            "steps": {"voice_smoke_approval" if args.smoke_test else "voice_approval": "awaiting_approval"},
        }
        update_job(job_path, step, "completed", **updates)
        print(out_path)
    except Exception as exc:
        update_job(job_path, step, "failed")
        raise SystemExit(f"{exc}; generation status uncertain, do not retry automatically") from None


if __name__ == "__main__":
    main()
