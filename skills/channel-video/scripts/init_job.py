#!/usr/bin/env python3
"""Create or resume a neutral video job next to an existing reel file."""

from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path


STEP_NAMES = (
    "script",
    "voice_smoke",
    "voice_smoke_approval",
    "voice_full",
    "voice_approval",
    "heygen_audio_upload",
    "heygen_lipsync_smoke",
    "heygen_lipsync_full",
    "transcription",
    "media_research",
    "media_approval",
    "media_download",
    "composition",
    "qa",
    "final_approval",
)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("reel", type=Path, help="Path to reel_<slug>.md")
    args = parser.parse_args()

    reel = args.reel.expanduser().resolve()
    if not reel.is_file():
        raise SystemExit(f"reel not found: {reel}")
    if not reel.stem.startswith("reel_"):
        raise SystemExit("expected a file named reel_<slug>.md")

    slug = reel.stem.removeprefix("reel_")
    if not re.fullmatch(r"[a-z0-9_]+", slug):
        raise SystemExit("Use a lowercase snake_case slug")
    job_dir = reel.parent / f"video_{slug}"
    final_dir = reel.parent / "video final"
    final_dir.mkdir(parents=True, exist_ok=True)
    for relative in (
        "audio",
        "heygen",
        "transcripts",
        "media/candidates",
        "media/approved",
        "edit",
        "qa",
    ):
        (job_dir / relative).mkdir(parents=True, exist_ok=True)

    state_path = job_dir / "job.json"
    if state_path.exists():
        state = json.loads(state_path.read_text())
        for name in STEP_NAMES:
            state.setdefault("steps", {}).setdefault(name, "pending")
        state["version"] = max(state.get("version", 1), 2)
        state["updated_at"] = utc_now()
    else:
        state = {
            "version": 2,
            "slug": slug,
            "reel": str(reel),
            "falas": str(reel.with_name(f"falas_{slug}.md")),
            "job_dir": str(job_dir),
            "created_at": utc_now(),
            "updated_at": utc_now(),
            "steps": {name: ("completed" if name == "script" else "pending") for name in STEP_NAMES},
            "artifacts": {},
            "external_ids": {},
        }
    state.setdefault("artifacts", {})["final_dir"] = str(final_dir)
    state_path.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n")
    print(job_dir)


if __name__ == "__main__":
    main()
