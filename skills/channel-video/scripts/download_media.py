#!/usr/bin/env python3
"""Download only approved direct HTTPS assets; never treat a web page as media."""
import argparse
import json
from pathlib import Path
import ssl
import urllib.error
import urllib.request
from urllib.parse import urlparse
import certifi
from common import sha256, json_write


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--job-dir", required=True, type=Path)
    parser.add_argument("--manifest", required=True, type=Path)
    args = parser.parse_args()
    job = args.job_dir.resolve(strict=True)
    manifest_path = args.manifest.resolve(strict=True)
    if not manifest_path.is_relative_to(job):
        raise SystemExit("Manifest must belong to this job")
    manifest = json.loads(manifest_path.read_text())
    output = job / "media/approved"
    output.mkdir(parents=True, exist_ok=True)
    for index, slot in enumerate(manifest["slots"]):
        if slot.get("approval_status") != "approved":
            continue
        if slot.get("local_file"):
            path = (job / slot["local_file"]).resolve(strict=True)
            if path.is_relative_to(output) and slot.get("file_sha256") == sha256(path):
                continue
            raise SystemExit("Existing media checksum/path mismatch; inspect before replacing")
        url = slot.get("media_url", "")
        if urlparse(url).scheme != "https":
            raise SystemExit(f"Slot {index + 1}: a verified direct HTTPS media URL is required")
        request = urllib.request.Request(url, headers={"User-Agent": "channel-video/1"})
        try:
            with urllib.request.urlopen(request, context=ssl.create_default_context(cafile=certifi.where()), timeout=60) as response:
                mime = response.headers.get_content_type()
                if not mime.startswith(("image/", "video/")):
                    raise ValueError("The URL did not return media; do not scrape or guess a private file URL")
                suffix = {"image/jpeg": ".jpg", "image/png": ".png", "image/webp": ".webp",
                          "video/mp4": ".mp4", "video/webm": ".webm", "video/quicktime": ".mov"}.get(mime)
                if not suffix:
                    raise ValueError("Media format needs an explicit supported acquisition method")
                destination = output / f"asset_{index:03d}{suffix}"
                if destination.exists():
                    raise ValueError("Untracked destination already exists; inspect before downloading")
                temporary = destination.with_suffix(destination.suffix + ".part")
                with temporary.open("xb") as handle:
                    total = 0
                    while chunk := response.read(1024 * 1024):
                        total += len(chunk)
                        if total > 1024 * 1024 * 1024:
                            raise ValueError("Download exceeds the 1 GB safety limit")
                        handle.write(chunk)
                temporary.replace(destination)
        except urllib.error.HTTPError as exc:
            raise SystemExit(f"Media download HTTP {exc.code}; inspect source access") from None
        slot["local_file"] = str(destination.relative_to(job))
        slot["file_sha256"] = sha256(destination)
        json_write(manifest_path, manifest)
    print("Approved direct downloads complete; licensing status unchanged")


if __name__ == "__main__":
    main()
