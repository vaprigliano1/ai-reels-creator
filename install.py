#!/usr/bin/env python3
"""Install into a new workspace. No API calls and no credential discovery."""
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import venv


def install(workspace: Path, install_skill: bool = False, setup_python: bool = False,
            skill_root: Path | None = None) -> Path:
    source = Path(__file__).resolve().parent
    workspace = workspace.expanduser().resolve()
    if workspace.exists() and (not workspace.is_dir() or any(workspace.iterdir())):
        raise ValueError("Use a new or empty workspace; existing files will not be overwritten")
    target_skill = None
    if install_skill:
        root = skill_root or (Path(os.environ["CODEX_HOME"]) / "skills"
                              if os.environ.get("CODEX_HOME") else Path.home() / ".codex/skills")
        target_skill = root / "channel-video"
        if target_skill.exists() or target_skill.is_symlink():
            raise ValueError("channel-video skill already exists; inspect it before installing another version")
    workspace.mkdir(parents=True, exist_ok=True)
    for name in ("AGENTS.md", "channel_context.md", "channel_profile.json", ".env.example", ".gitignore"):
        shutil.copyfile(source / "project" / name, workspace / name)
    shutil.copyfile(workspace / ".env.example", workspace / ".env")
    (workspace / ".env").chmod(0o600)
    shutil.copyfile(source / "requirements.txt", workspace / "requirements.txt")
    local_skill = workspace / ".agent/skills/channel-video"
    shutil.copytree(source / "skills/channel-video", local_skill,
                    ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    for name in ("inputs", "videos", "private-references"):
        (workspace / name).mkdir()
    if target_skill:
        target_skill.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(source / "skills/channel-video", target_skill,
                        ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    if setup_python:
        venv.create(workspace / ".venv", with_pip=True)
        python = workspace / ".venv" / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
        subprocess.run([str(python), "-m", "pip", "install", "-r", str(workspace / "requirements.txt")], check=True)
    return workspace


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace", required=True, type=Path)
    parser.add_argument("--install-skill", action="store_true")
    parser.add_argument("--setup-python", action="store_true")
    args = parser.parse_args()
    if sys.version_info < (3, 11):
        raise SystemExit("Python 3.11+ is required")
    try:
        workspace = install(args.workspace, args.install_skill, args.setup_python)
    except (ValueError, OSError, subprocess.CalledProcessError) as exc:
        raise SystemExit(str(exc)) from None
    print(json.dumps({"workspace": str(workspace), "onboarding_required": True,
                      "credentials_created": "blank local .env; fill with your own values",
                      "paid_calls": 0}, ensure_ascii=False))


if __name__ == "__main__":
    main()
