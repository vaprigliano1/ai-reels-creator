"""Repository hygiene checks. No real credentials are loaded or printed."""
import json
from pathlib import Path
import re
import shutil
import subprocess
import unittest


ROOT = Path(__file__).resolve().parents[1]
SECRET_PATTERNS = {
    "provider_key": rb"\bsk_[A-Za-z0-9_-]{24,}\b",
    "openai_key": rb"\bsk-(?:proj-|svcacct-)?[A-Za-z0-9_-]{24,}\b",
    "github_token": rb"\b(?:gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{30,})\b",
    "aws_key": rb"\b(?:AKIA|ASIA)[A-Z0-9]{16}\b",
    "private_key": rb"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----",
}


def repository_files():
    if shutil.which("git") and (ROOT / ".git").exists():
        names = subprocess.check_output(["git", "-C", str(ROOT), "ls-files", "-z"]).decode().split("\0")
        return [ROOT / name for name in names if name and (ROOT / name).is_file()]
    return [path for path in ROOT.rglob("*") if path.is_file()
            and not any(part in {".git", ".venv", "__pycache__", ".pytest_cache"}
                        for part in path.relative_to(ROOT).parts)]


class PrivacyTests(unittest.TestCase):
    def test_configuration_templates_are_blank_and_unapproved(self):
        for line in (ROOT / "templates/channel/.env.example").read_text().splitlines():
            if line.strip() and not line.lstrip().startswith("#"):
                name, value = line.split("=", 1)
                self.assertEqual(value.strip(), "", f"Configuration must be blank: {name}")
        profile = json.loads((ROOT / "templates/channel/channel_profile.json").read_text())
        self.assertIs(profile["approved"], False)
        for key in ("channel_name", "audience", "language_code", "tone", "visual_direction"):
            self.assertEqual(profile[key], "")
        self.assertEqual(profile["voice_settings"], {})

    def test_no_private_or_generated_files_are_tracked(self):
        excluded_parts = {".venv", "__pycache__", "inputs", "videos", "private-references", "logs"}
        excluded_suffixes = {".pem", ".key", ".p12", ".mp4", ".mov", ".webm", ".mp3", ".m4a", ".wav"}
        for path in repository_files():
            name = path.relative_to(ROOT).as_posix()
            self.assertFalse(excluded_parts.intersection(path.relative_to(ROOT).parts), name)
            self.assertNotIn(path.suffix.lower(), excluded_suffixes, name)
            if path.name.startswith(".env"):
                self.assertEqual(path.name, ".env.example", name)
            self.assertNotEqual(path.name, "job.json", name)

    def test_no_key_like_values_in_sources(self):
        for path in repository_files():
            data = path.read_bytes()
            for label, pattern in SECRET_PATTERNS.items():
                self.assertIsNone(re.search(pattern, data),
                                  f"Potential {label} in {path.relative_to(ROOT)}; value withheld")

    @unittest.skipUnless(shutil.which("git"), "Git missing")
    def test_sensitive_paths_are_ignored(self):
        if not (ROOT / ".git").exists():
            self.skipTest("Ignore checks require a Git checkout")
        for name in (".env", ".env.local", "inputs/private.pdf", "videos/topic/preview.mp4",
                     "private-references/recording.mp3", "logs/request.log", ".venv/bin/python"):
            result = subprocess.run(["git", "-C", str(ROOT), "check-ignore", "--no-index", "-q", name])
            self.assertEqual(result.returncode, 0, name)
        result = subprocess.run(["git", "-C", str(ROOT), "check-ignore", "--no-index", "-q",
                                 "templates/channel/.env.example"])
        self.assertEqual(result.returncode, 1)


class DocumentationTests(unittest.TestCase):
    def test_documentation_links_resolve(self):
        documents = [ROOT / "README.md", *sorted((ROOT / "docs").glob("*.md"))]
        for document in documents:
            for target in re.findall(r"\[[^\]]+\]\(([^)]+)\)", document.read_text()):
                if "://" in target or target.startswith("#"):
                    continue
                path = (document.parent / target.split("#", 1)[0]).resolve()
                self.assertTrue(path.is_relative_to(ROOT), f"Link leaves repository: {document.name}")
                self.assertTrue(path.exists(), f"Broken link in {document.name}: {target}")


if __name__ == "__main__":
    unittest.main(verbosity=2)
