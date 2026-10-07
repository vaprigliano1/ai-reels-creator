#!/usr/bin/env python3
"""Consolidate one existing complete render; never generate media or grant rights."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess


def digest(path: Path) -> str:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def save_final(job_path: Path, source: Path, basis: str, replace: bool = False) -> dict:
    job_path = job_path.resolve(strict=True)
    source = source.resolve(strict=True)
    state = json.loads(job_path.read_text())
    if basis == "approved" and not (
        state.get("steps", {}).get("final_approval") == "completed"
        or (state.get("approval_gate") or {}).get("final_video_approved") is True
    ):
        raise ValueError("Record final editorial approval in the job before using --basis approved")
    slug = state["slug"]
    if not re.fullmatch(r"[a-z0-9_]+", slug):
        raise ValueError("Unsafe or unsupported pauta slug")
    theme = Path(state["reel"]).resolve(strict=True).parent
    if job_path.parent.parent != theme or not source.is_relative_to(job_path.parent):
        raise ValueError("Job and source must belong to the same thematic production directory")
    if source.suffix.lower() != ".mp4":
        raise ValueError("Final delivery must be an existing MP4")
    probe = json.loads(subprocess.run([
        "ffprobe", "-v", "error", "-show_entries", "stream=codec_type:format=duration",
        "-of", "json", str(source),
    ], capture_output=True, text=True, check=True).stdout)
    types = {s["codec_type"] for s in probe["streams"]}
    if not {"video", "audio"} <= types or float(probe["format"]["duration"]) <= 0:
        raise ValueError("Expected a complete render with both video and audio")
    source_sha = digest(source)
    final_dir = theme / "video final"
    final_dir.mkdir(exist_ok=True)
    if final_dir.is_symlink():
        raise ValueError("Refusing a symlink final directory")
    unexpected = [p.name for p in final_dir.iterdir()
                  if not p.is_file() or not re.fullmatch(r"final_[a-z0-9_]+\.mp4", p.name)]
    if unexpected:
        raise ValueError(f"Final directory contains non-delivery entries; inspect before relocating: {unexpected}")
    destination = final_dir / f"final_{slug}.mp4"
    if destination.is_symlink():
        raise ValueError("Refusing to replace a symlink delivery target")
    now = datetime.now(timezone.utc)
    archived = None
    if destination.exists() and digest(destination) != source_sha:
        if not replace:
            raise ValueError("A different final already exists; inspect it before using --replace")
        archive_dir = job_path.parent / "edit/history/final_delivery" / now.strftime("%Y%m%dT%H%M%S%fZ")
        archive_dir.mkdir(parents=True, exist_ok=False)
        archived = archive_dir / destination.name
        shutil.move(str(destination), str(archived))
    if not destination.exists():
        # x-mode avoids accidental overwrite; source remains untouched.
        with source.open("rb") as src, destination.open("xb") as dst:
            shutil.copyfileobj(src, dst)
    if digest(destination) != source_sha:
        raise RuntimeError("Delivery hash mismatch")
    previous = state.get("final_delivery")
    if previous and previous.get("sha256") != source_sha:
        state.setdefault("final_delivery_history", []).append(previous)
    artifacts = state.setdefault("artifacts", {})
    old_final = artifacts.get("final")
    if old_final and old_final != str(destination):
        paths = state.setdefault("legacy_final_paths", [])
        if old_final not in paths:
            paths.append(old_final)
    artifacts.update(final=str(destination), final_dir=str(final_dir), final_sha256=source_sha)
    delivery = {
        "path": str(destination), "source": str(source), "sha256": source_sha,
        "saved_at": now.isoformat(), "basis": basis, "reencoded": False,
        "editorial_approval_state_unchanged": True, "publication_rights_unchanged": True,
    }
    if archived:
        delivery["previous_delivery_archived_to"] = str(archived)
    state["final_delivery"] = delivery
    state["updated_at"] = now.isoformat()
    job_path.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n")
    return delivery


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--job", required=True, type=Path)
    parser.add_argument("--source", required=True, type=Path,
                        help="Explicit existing complete render selected by the caller; no fallback")
    parser.add_argument("--basis", required=True, choices=("approved", "user_requested_consolidation"))
    parser.add_argument("--replace", action="store_true", help="Archive previous delivery outside final folder")
    args = parser.parse_args()
    print(json.dumps(save_final(args.job, args.source, args.basis, args.replace), ensure_ascii=False))


if __name__ == "__main__":
    main()
