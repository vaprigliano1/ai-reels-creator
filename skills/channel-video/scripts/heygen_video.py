#!/usr/bin/env python3
"""Lip-sync an approved ElevenLabs audio take on a HeyGen avatar."""

from __future__ import annotations

import argparse
import hashlib
import json
import ssl
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

import certifi
from common import load_env as read_local_env, workspace_job, workspace_profile


API_BASE = "https://api.heygen.com"
TLS_CONTEXT = ssl.create_default_context(cafile=certifi.where())


def load_env(path: Path) -> dict[str, str]:
    return read_local_env(path, ("HEYGEN_API_KEY", "HEYGEN_AVATAR_ID", "HEYGEN_ENGINE"))


def request_json(method: str, path: str, api_key: str, payload: dict | None = None, idem: str | None = None) -> dict:
    data = json.dumps(payload).encode() if payload is not None else None
    headers = {"X-Api-Key": api_key, "Content-Type": "application/json"}
    if idem:
        headers["Idempotency-Key"] = idem
    req = urllib.request.Request(f"{API_BASE}{path}", data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=60, context=TLS_CONTEXT) as response:
            return json.loads(response.read().decode())
    except urllib.error.HTTPError as exc:
        raise SystemExit(f"HeyGen HTTP {exc.code}; request status may be uncertain") from None


def update_job(job_path: Path, step: str, status: str, **fields: object) -> None:
    job = json.loads(job_path.read_text())
    job["steps"][step] = status
    job["updated_at"] = datetime.now(timezone.utc).isoformat()
    for section, values in fields.items():
        if isinstance(values, dict):
            job.setdefault(section, {}).update(values)
        else:
            job[section] = values
    job_path.write_text(json.dumps(job, ensure_ascii=False, indent=2) + "\n")


def download(url: str, destination: Path) -> None:
    req = urllib.request.Request(url, headers={"User-Agent": "channel-video/1"})
    with urllib.request.urlopen(req, timeout=300, context=TLS_CONTEXT) as response:
        destination.write_bytes(response.read())


def upload_audio(audio: Path, api_key: str, idem: str) -> str:
    boundary = "channelvideo" + hashlib.sha256(audio.name.encode()).hexdigest()[:20]
    body = (
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="file"; filename="{audio.name}"\r\n'
        "Content-Type: audio/mpeg\r\n\r\n"
    ).encode() + audio.read_bytes() + f"\r\n--{boundary}--\r\n".encode()
    request = urllib.request.Request(
        f"{API_BASE}/v3/assets",
        data=body,
        headers={"X-Api-Key": api_key, "Content-Type": f"multipart/form-data; boundary={boundary}", "Idempotency-Key": idem},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=180, context=TLS_CONTEXT) as response:
            data = json.loads(response.read().decode())["data"]
            return data.get("asset_id") or data["id"]
    except urllib.error.HTTPError as exc:
        raise SystemExit(f"HeyGen audio upload HTTP {exc.code}; no new render submitted") from None


def build_video_payload(avatar_id: str, asset_id: str, mode: str, engine: str, resolution: str, reference_look_id: str | None) -> dict:
    payload = {
        "type": "avatar",
        "avatar_id": avatar_id,
        "title": f"Video {mode} external audio",
        "aspect_ratio": "9:16",
        "resolution": resolution,
        "output_format": "webm",
        "audio_asset_id": asset_id,
        "engine": {"type": engine},
    }
    if engine == "avatar_v" and reference_look_id:
        payload["engine"]["reference_look_id"] = reference_look_id
        payload["motion_prompt"] = "Natural presenter posture, subtle hand gestures, calm confident delivery, realistic restrained movement, no exaggerated motion."
    return payload


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--env", type=Path, required=True)
    parser.add_argument("--job-dir", type=Path, required=True)
    parser.add_argument("--audio-file", type=Path, required=True)
    parser.add_argument("--smoke-test", action="store_true")
    parser.add_argument("--engine", choices=("avatar_iv", "avatar_v"), default=None)
    parser.add_argument("--resolution", choices=("720p", "1080p"), default=None)
    parser.add_argument("--poll-seconds", type=int, default=10)
    parser.add_argument("--timeout-seconds", type=int, default=1800)
    parser.add_argument("--dry-run", action="store_true", help="Validate without uploading or rendering")
    parser.add_argument("--retry-paid", action="store_true", help="Explicitly retry an uncertain render submission")
    parser.add_argument("--allow-paid", action="store_true", help="Human-authorized upload/render only")
    args = parser.parse_args()

    env_path = args.env.expanduser().resolve(strict=True)
    env = load_env(env_path)
    job_dir = args.job_dir.expanduser().resolve()
    workspace_job(env_path, job_dir)
    workspace_profile(env_path)
    args.engine = args.engine or env["HEYGEN_ENGINE"]
    if args.engine not in {"avatar_iv", "avatar_v"}:
        raise SystemExit("Unsupported engine in this adapter; check current provider documentation")
    if not 1 <= args.poll_seconds <= 60 or args.timeout_seconds <= 0:
        raise SystemExit("Use a polling interval from 1 to 60 seconds and a positive timeout")
    job_path = job_dir / "job.json"
    if not job_path.exists():
        raise SystemExit(f"job.json not found in {job_dir}")

    audio = args.audio_file.expanduser().resolve()
    if not audio.is_relative_to(job_dir / "audio") or not audio.is_file() or audio.suffix.lower() != ".mp3":
        raise SystemExit("--audio-file must be an MP3 in the job's audio/ directory")
    if audio.stat().st_size == 0 or audio.stat().st_size > 32 * 1024 * 1024:
        raise SystemExit("audio file must be nonempty and at most 32 MB")
    digest = hashlib.sha256(audio.read_bytes()).hexdigest()
    job = json.loads(job_path.read_text())
    if digest not in job.get("audio_approvals", {}):
        raise SystemExit("audio is not approved in job.json; wait for explicit human approval")
    if job["audio_approvals"][digest].get("audio_file") != str(audio):
        raise SystemExit("approval does not match this audio path")
    mode = "smoke" if args.smoke_test else "full"
    step = f"heygen_lipsync_{mode}"
    render_config = build_video_payload(env["HEYGEN_AVATAR_ID"], "pending", mode, args.engine,
                                       args.resolution or ("720p" if args.smoke_test else "1080p"),
                                       env.get("HEYGEN_REFERENCE_LOOK_ID"))
    fingerprint = hashlib.sha256((digest + json.dumps(render_config, sort_keys=True)).encode()).hexdigest()[:12]
    out_path = job_dir / "heygen" / f"avatar_{mode}_{args.engine}_el_{fingerprint}.webm"
    meta_path = out_path.with_suffix(".json")
    attempt_path = out_path.with_suffix(".attempt.json")
    if args.dry_run:
        print(json.dumps({"mode": mode, "engine": args.engine, "audio_sha256": digest, "output": str(out_path), "approved": True}, ensure_ascii=False))
        return
    if out_path.exists():
        if out_path.stat().st_size > 0 and meta_path.is_file():
            meta = json.loads(meta_path.read_text())
            if meta.get("source_audio_sha256") == digest:
                print(out_path)
                return
        raise SystemExit(f"existing render lacks matching metadata; inspect before retrying: {out_path}")

    asset_key = f"heygen_audio_asset_{digest[:12]}"
    asset_id = job.get("external_ids", {}).get(asset_key)
    if not asset_id:
        if not args.allow_paid:
            raise SystemExit("Upload/render requires human authorization and --allow-paid")
        upload_idem = hashlib.sha256(f"channel-video:audio:{digest}".encode()).hexdigest()[:48]
        asset_id = upload_audio(audio, env["HEYGEN_API_KEY"], upload_idem)
        update_job(job_path, "heygen_audio_upload", "completed", external_ids={asset_key: asset_id})

    payload = build_video_payload(
        env["HEYGEN_AVATAR_ID"],
        asset_id,
        mode,
        args.engine,
        args.resolution or ("720p" if args.smoke_test else "1080p"),
        env.get("HEYGEN_REFERENCE_LOOK_ID"),
    )
    idem_material = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    idem = hashlib.sha256(f"channel-video:lip-sync:{mode}:{digest}:{idem_material}".encode()).hexdigest()[:48]
    update_job(job_path, step, "running")
    video_key = f"heygen_lipsync_{mode}_{fingerprint}"
    video_id = json.loads(job_path.read_text()).get("external_ids", {}).get(video_key)
    if not video_id:
        if not args.allow_paid:
            raise SystemExit("New render requires human authorization and --allow-paid")
        if attempt_path.exists() and not args.retry_paid:
            raise SystemExit(f"previous render submission uncertain; inspect {attempt_path} before using --retry-paid")
        attempt_path.write_text(json.dumps({"submitted_at": datetime.now(timezone.utc).isoformat(), "audio_sha256": digest}) + "\n")
        created = request_json("POST", "/v3/videos", env["HEYGEN_API_KEY"], payload, idem)
        video_id = created["data"]["video_id"]
        update_job(job_path, step, "running", external_ids={video_key: video_id})
        attempt_path.unlink()

    deadline = time.monotonic() + args.timeout_seconds
    out_path.parent.mkdir(parents=True, exist_ok=True)
    while time.monotonic() < deadline:
        result = request_json("GET", f"/v3/videos/{video_id}", env["HEYGEN_API_KEY"])
        data = result["data"]
        status = data.get("status")
        print(f"{video_id}: {status}", flush=True)
        if status == "completed":
            video_url = data["video_url"]
            download(video_url, out_path)
            persisted = {k: data[k] for k in ("video_id", "id", "status", "duration", "created_at") if k in data}
            persisted["source_audio_sha256"] = digest
            persisted["audio_asset_id"] = asset_id
            meta_path.write_text(json.dumps(persisted, ensure_ascii=False, indent=2) + "\n")
            update_job(job_path, step, "completed", artifacts={step: str(out_path)})
            print(out_path)
            return
        if status == "failed":
            update_job(job_path, step, "failed")
            raise SystemExit("HeyGen render failed; inspect provider dashboard without exposing response data")
        time.sleep(args.poll_seconds)

    update_job(job_path, step, "failed")
    raise SystemExit(f"HeyGen render timed out after {args.timeout_seconds}s")


if __name__ == "__main__":
    main()
