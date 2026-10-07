#!/usr/bin/env python3
"""Transcribe one approved audio file and prepare conservative caption cues."""
import argparse
import json
from pathlib import Path
import ssl
import urllib.error
import urllib.request
import certifi
from common import approved_audio, json_write, load_env, now, workspace_job, workspace_profile


def cues_from_words(words, limit=5):
    cues, group = [], []
    for word in words:
        if word.get("type", "word") != "word" or not str(word.get("text", "")).strip():
            continue
        group.append(word)
        if len(group) >= limit or str(word["text"]).rstrip().endswith((".", "!", "?")):
            cues.append({"start": float(group[0]["start"]), "end": float(group[-1]["end"]),
                         "text": " ".join(str(w["text"]).strip() for w in group)})
            group = []
    if group:
        cues.append({"start": float(group[0]["start"]), "end": float(group[-1]["end"]),
                     "text": " ".join(str(w["text"]).strip() for w in group)})
    return cues


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--env", required=True, type=Path)
    parser.add_argument("--job-dir", required=True, type=Path)
    parser.add_argument("--audio-file", required=True, type=Path)
    parser.add_argument("--allow-paid", action="store_true")
    parser.add_argument("--retry-paid", action="store_true")
    args = parser.parse_args()
    env_path, job, audio = args.env.resolve(strict=True), args.job_dir.resolve(strict=True), args.audio_file.resolve(strict=True)
    workspace_job(env_path, job)
    profile = workspace_profile(env_path)
    env = load_env(env_path, ("ELEVENLABS_API_KEY", "ELEVENLABS_STT_MODEL_ID"))
    digest = approved_audio(job, audio)
    output = job / "transcripts" / f"words_{digest[:12]}.json"
    attempt = output.with_suffix(".attempt.json")
    if output.exists():
        result = json.loads(output.read_text())
        if result.get("audio_sha256") != digest:
            raise SystemExit("Transcription audio hash mismatch")
    else:
        if not args.allow_paid:
            raise SystemExit("Transcription requires human authorization and --allow-paid")
        if attempt.exists() and not args.retry_paid:
            raise SystemExit("Previous transcription outcome uncertain; inspect before authorizing another call")
        boundary = "channelstt" + digest[:16]
        body = bytearray()
        fields = {"model_id": env["ELEVENLABS_STT_MODEL_ID"], "language_code": profile["language_code"],
                  "diarize": "false", "tag_audio_events": "false"}
        for key, value in fields.items():
            body.extend(f'--{boundary}\r\nContent-Disposition: form-data; name="{key}"\r\n\r\n{value}\r\n'.encode())
        body.extend(f'--{boundary}\r\nContent-Disposition: form-data; name="file"; filename="take.mp3"\r\nContent-Type: audio/mpeg\r\n\r\n'.encode())
        body.extend(audio.read_bytes())
        body.extend(f"\r\n--{boundary}--\r\n".encode())
        json_write(attempt, {"started_at": now(), "audio_sha256": digest})
        request = urllib.request.Request("https://api.elevenlabs.io/v1/speech-to-text", data=bytes(body),
            headers={"xi-api-key": env["ELEVENLABS_API_KEY"], "Content-Type": f"multipart/form-data; boundary={boundary}"}, method="POST")
        try:
            with urllib.request.urlopen(request, timeout=180, context=ssl.create_default_context(cafile=certifi.where())) as response:
                raw = json.loads(response.read())
        except urllib.error.HTTPError as exc:
            raise SystemExit(f"Transcription HTTP {exc.code}; do not retry automatically") from None
        result = {"audio_sha256": digest, "language_code": raw.get("language_code"),
                  "text": raw.get("text", ""), "words": raw.get("words", []), "created_at": now()}
        if not result["words"]:
            raise SystemExit("No word timestamps returned; inspect before retrying")
        json_write(output, result)
        attempt.unlink()
    cues = job / "transcripts" / f"cues_{digest[:12]}.json"
    json_write(cues, {"audio_sha256": digest, "cues": cues_from_words(result["words"])})
    state_path = job / "job.json"
    state = json.loads(state_path.read_text())
    state["steps"]["transcription"] = "completed"
    state.setdefault("artifacts", {}).update(transcription=str(output), caption_cues=str(cues))
    json_write(state_path, state)
    print(cues)


if __name__ == "__main__":
    main()
