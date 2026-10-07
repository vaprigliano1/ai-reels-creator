#!/usr/bin/env python3
"""Decode preview and extract cut-boundary frames. Does not certify visual quality."""
import argparse
import json
from pathlib import Path
import subprocess
from common import json_write, sha256, now


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--job-dir", required=True, type=Path)
    parser.add_argument("--plan", required=True, type=Path)
    args = parser.parse_args()
    job = args.job_dir.resolve(strict=True)
    preview = job / "preview.mp4"
    if not args.plan.resolve(strict=True).is_relative_to(job):
        raise SystemExit("Plan must belong to this job")
    plan = json.loads(args.plan.read_text())
    fps = int(plan.get("fps", 30))
    information = json.loads(subprocess.run(["ffprobe", "-v", "error", "-show_streams", "-show_format", "-of", "json", str(preview)],
                                           capture_output=True, text=True, check=True).stdout)
    decoded = subprocess.run(["ffmpeg", "-hide_banner", "-v", "error", "-i", str(preview), "-f", "null", "-"], capture_output=True, text=True)
    video = next(s for s in information["streams"] if s["codec_type"] == "video")
    total = sum(round(float(s["duration"])*fps) for s in plan["shots"])
    elapsed, boundaries = 0, []
    for shot in plan["shots"][:-1]:
        elapsed += round(float(shot["duration"])*fps)
        boundaries.append(elapsed)
    frames = sorted({max(0, min(total-1, boundary+offset)) for boundary in [0, total//2, total-1, *boundaries]
                     for offset in (-3, -2, -1, 0, 1, 2, 3)})
    output = job / "qa" / ("preview_" + sha256(preview)[:12])
    output.mkdir(parents=True, exist_ok=True)
    for frame in frames:
        subprocess.run(["ffmpeg", "-hide_banner", "-v", "error", "-y", "-i", str(preview), "-ss", str(frame/fps),
                        "-frames:v", "1", str(output / f"frame_{frame:05d}.png")], capture_output=True, check=True)
    report = {"created_at": now(), "preview_sha256": sha256(preview), "decoded_without_errors": decoded.returncode == 0 and not decoded.stderr.strip(),
              "dimensions_match": [video["width"], video["height"]] == [int(plan.get("width", 1080)), int(plan.get("height", 1920))],
              "audio_present": any(s["codec_type"] == "audio" for s in information["streams"]),
              "duration_matches_plan": abs(float(information["format"]["duration"]) - total/fps) <= 0.12,
              "cut_frames": frames, "visual_review_required": True,
              "not_checked_automatically": ["jitter", "pronunciation", "lip_sync", "contrast", "rights", "semantic_cut_flashes"]}
    json_write(output / "technical_report.json", report)
    state_path = job / "job.json"
    state = json.loads(state_path.read_text())
    state["steps"]["qa"] = "awaiting_approval"
    state.setdefault("artifacts", {})["qa_report"] = str(output / "technical_report.json")
    json_write(state_path, state)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    raise SystemExit(0 if all(report[k] for k in ("decoded_without_errors", "dimensions_match", "audio_present", "duration_matches_plan")) else 2)


if __name__ == "__main__":
    main()
