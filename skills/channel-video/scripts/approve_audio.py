#!/usr/bin/env python3
"""Record an explicit human approval for one exact ElevenLabs audio file."""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--job-dir", type=Path, required=True)
    parser.add_argument("--audio-file", type=Path, required=True)
    args = parser.parse_args()

    job_dir = args.job_dir.expanduser().resolve()
    audio = args.audio_file.expanduser().resolve()
    if not audio.is_relative_to(job_dir / "audio") or not audio.is_file():
        raise SystemExit("audio must be an existing file in the job's audio/ directory")
    meta_path = audio.with_suffix(".json")
    if not meta_path.is_file():
        raise SystemExit(f"audio metadata missing: {meta_path}")
    metadata = json.loads(meta_path.read_text())
    digest = hashlib.sha256(audio.read_bytes()).hexdigest()
    if metadata.get("audio_sha256") != digest:
        raise SystemExit("audio checksum does not match generation metadata")

    job_path = job_dir / "job.json"
    job = json.loads(job_path.read_text())
    job.setdefault("audio_approvals", {})[digest] = {"audio_file": str(audio), "approved_at": datetime.now(timezone.utc).isoformat()}
    step = "voice_smoke_approval" if "_smoke_" in audio.name else "voice_approval"
    job.setdefault("steps", {})[step] = "completed"
    job["updated_at"] = datetime.now(timezone.utc).isoformat()
    job_path.write_text(json.dumps(job, ensure_ascii=False, indent=2) + "\n")
    print(f"approved audio sha256={digest}")


if __name__ == "__main__":
    main()
