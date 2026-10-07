#!/usr/bin/env python3
"""Read-only local readiness checks. Never prints credential values or calls APIs."""
import argparse
import importlib.util
import json
from pathlib import Path
import shutil
import sys
from common import load_env


def check(workspace: Path):
    env_path = workspace / ".env"
    values = load_env(env_path) if env_path.is_file() else {}
    required = ("ELEVENLABS_API_KEY", "ELEVENLABS_VOICE_ID", "ELEVENLABS_MODEL_ID",
                "ELEVENLABS_STT_MODEL_ID", "HEYGEN_API_KEY", "HEYGEN_AVATAR_ID", "HEYGEN_ENGINE")
    profile_path = workspace / "channel_profile.json"
    profile = json.loads(profile_path.read_text()) if profile_path.is_file() else {}
    report = {"python_3_11_plus": sys.version_info >= (3, 11),
              "dependencies": {name: importlib.util.find_spec(name) is not None for name in ("certifi", "PIL")},
              "binaries": {name: shutil.which(name) is not None for name in ("ffmpeg", "ffprobe")},
              "configuration": {name: bool(values.get(name)) for name in required},
              "channel_approved": profile.get("approved") is True,
              "context_exists": (workspace / "channel_context.md").is_file(),
              "language_configured": bool(profile.get("language_code")), "api_calls": 0}
    report["ready"] = (report["python_3_11_plus"] and all(report["dependencies"].values())
                       and all(report["binaries"].values()) and all(report["configuration"].values())
                       and report["channel_approved"] and report["context_exists"] and report["language_configured"])
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace", required=True, type=Path)
    args = parser.parse_args()
    report = check(args.workspace.expanduser().resolve())
    print(json.dumps(report, ensure_ascii=False, indent=2))
    raise SystemExit(0 if report["ready"] else 2)
