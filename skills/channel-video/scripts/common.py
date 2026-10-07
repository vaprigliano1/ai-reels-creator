"""Workspace-scoped configuration and deterministic state helpers."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path


def now():
    return datetime.now(timezone.utc).isoformat()


def sha256(path: Path):
    with path.open("rb") as handle:
        return hashlib.file_digest(handle, "sha256").hexdigest()


def load_env(path: Path, required=()):
    # No process-env fallback and no search of home directories or other projects.
    values = {}
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip().strip('"').strip("'")
    missing = [key for key in required if not values.get(key)]
    if missing:
        raise ValueError("Missing local configuration: " + ", ".join(missing))
    return values


def workspace_profile(env_path: Path):
    profile = json.loads((env_path.parent / "channel_profile.json").read_text(encoding="utf-8"))
    if profile.get("approved") is not True or not profile.get("channel_name") or not profile.get("language_code"):
        raise ValueError("Finish and approve channel onboarding first")
    return profile


def workspace_job(env_path: Path, job_dir: Path):
    root = env_path.resolve(strict=True).parent
    job_dir = job_dir.resolve(strict=True)
    if not job_dir.is_relative_to(root / "videos"):
        raise ValueError("Job must be inside this credential file's workspace videos/ directory")
    if not (job_dir / "job.json").is_file():
        raise ValueError("job.json is missing")
    return root


def contained(root: Path, value: str, must_exist=True):
    path = (root / value).resolve(strict=must_exist)
    if not path.is_relative_to(root.resolve()):
        raise ValueError("Artifact path escapes the job directory")
    return path


def json_write(path: Path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    pending = path.with_name(path.name + ".writing")
    pending.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    pending.replace(path)


def approved_audio(job_dir: Path, audio: Path):
    job_dir = job_dir.resolve(strict=True)
    audio = audio.resolve(strict=True)
    if not audio.is_relative_to(job_dir / "audio") or not audio.is_file():
        raise ValueError("Audio must be in this job's audio/ directory")
    digest = sha256(audio)
    job = json.loads((job_dir / "job.json").read_text())
    approval = job.get("audio_approvals", {}).get(digest, {})
    if approval.get("audio_file") != str(audio):
        raise ValueError("The exact audio file has not been approved")
    return digest
