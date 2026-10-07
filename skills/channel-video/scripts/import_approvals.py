#!/usr/bin/env python3
"""Import explicit media decisions only for the exact reviewed manifest."""
import argparse
import json
from pathlib import Path
from common import sha256, json_write


def apply(manifest_path: Path, decisions_path: Path):
    manifest = json.loads(manifest_path.read_text())
    exported = json.loads(decisions_path.read_text())
    if exported.get("manifest_sha256") != sha256(manifest_path):
        raise ValueError("Approval belongs to another manifest revision; regenerate/review the current board")
    ids = [slot["id"] for slot in manifest["slots"]]
    if len(ids) != len(set(ids)) or set(exported.get("decisions", {})) - set(ids):
        raise ValueError("Duplicate or unknown slot IDs")
    for slot in manifest["slots"]:
        decision = exported.get("decisions", {}).get(slot["id"], {})
        status = decision.get("decision", "pending")
        if status not in {"pending", "approved", "rejected"}:
            raise ValueError("Invalid decision")
        slot["approval_status"] = status
        slot["approval_note"] = decision.get("note", "")
    json_write(manifest_path, manifest)
    return {status: sum(s["approval_status"] == status for s in manifest["slots"])
            for status in ("approved", "rejected", "pending")}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path)
    parser.add_argument("decisions", type=Path)
    args = parser.parse_args()
    print(json.dumps(apply(args.manifest.resolve(), args.decisions.resolve())))
