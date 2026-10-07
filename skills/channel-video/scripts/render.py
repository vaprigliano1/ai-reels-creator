#!/usr/bin/env python3
"""Portable local vertical compositor. No provider API calls."""
import argparse
import json
import math
from pathlib import Path
import shutil
import subprocess
import textwrap
from PIL import Image, ImageDraw, ImageFont
from common import approved_audio, contained, json_write, load_env, now, sha256, workspace_job, workspace_profile


def run(args):
    result = subprocess.run(args, capture_output=True, text=True)
    if result.returncode:
        raise RuntimeError("Media command failed: " + result.stderr[-1600:])
    return result.stdout


def probe(path):
    return json.loads(run(["ffprobe", "-v", "error", "-show_streams", "-show_format", "-of", "json", str(path)]))


def validate(job, plan):
    width, height, fps = int(plan.get("width", 1080)), int(plan.get("height", 1920)), int(plan.get("fps", 30))
    if width < 32 or height < 32 or width % 2 or height % 2 or not 23 <= fps <= 60:
        raise ValueError("Even dimensions >=32 and 23-60 fps are required")
    audio = contained(job, plan["audio"])
    digest = approved_audio(job, audio)
    duration = float(probe(audio)["format"]["duration"])
    avatar = contained(job, plan["avatar"])
    metadata = avatar.with_suffix(".json")
    if not metadata.is_file() or json.loads(metadata.read_text()).get("source_audio_sha256") != digest:
        raise ValueError("Avatar metadata must match this exact approved audio")
    info = probe(avatar)
    if abs(float(info["format"]["duration"]) - duration) > 0.2:
        raise ValueError("Avatar/audio duration mismatch; do not stretch or replace audio")
    video = next(s for s in info["streams"] if s["codec_type"] == "video")
    if not (str(video.get("tags", {}).get("alpha_mode")) == "1" or "a" in video.get("pix_fmt", "")):
        raise ValueError("Avatar has no declared alpha; inspect transparency instead of compositing an opaque rectangle")
    manifest = json.loads(contained(job, plan["manifest"]).read_text())
    if manifest.get("audio_sha256") != digest:
        raise ValueError("Media manifest timestamps belong to another take")
    slots = {slot["id"]: slot for slot in manifest["slots"]}
    if len(slots) != len(manifest["slots"]):
        raise ValueError("Duplicate manifest IDs")
    seen, frames, boundaries = set(), [], []
    for shot in plan["shots"]:
        path = contained(job, shot["file"])
        if path in seen:
            raise ValueError("Background asset is repeated; choose another shot or revise explicitly")
        seen.add(path)
        slot = slots.get(shot["id"], {})
        if slot.get("approval_status") != "approved" or slot.get("local_file") != shot["file"] or slot.get("file_sha256") != sha256(path):
            raise ValueError("Shot does not match an approved, checksum-valid asset")
        if shot["type"] not in {"image", "video"} or shot.get("pan", "left") not in {"left", "right"}:
            raise ValueError("Unsupported shot type or pan")
        count = round(float(shot["duration"]) * fps)
        if count < 1 or not 0.7 <= float(shot.get("sharp_fraction", 1)) <= 1:
            raise ValueError("Invalid shot duration or sharp height")
        if shot["type"] == "video":
            length = float(probe(path)["format"]["duration"])
            offset = float(shot.get("source_in", 0))
            if offset < 0 or offset + count / fps > length + 0.04:
                raise ValueError("Selected interval extends beyond its local video file")
        frames.append(count)
        boundaries.append(sum(frames) / fps)
    if not frames or abs(sum(frames) / fps - duration) > 0.1:
        raise ValueError("Shot duration must match the audio to within 0.1s")
    crop = plan["avatar_crop"]
    if len(crop) != 4 or any(int(v) != v or v < 0 for v in crop) or crop[2] < 2 or crop[3] < 2:
        raise ValueError("Specify a measured avatar_crop [x,y,width,height]")
    if crop[0] + crop[2] > video["width"] or crop[1] + crop[3] > video["height"]:
        raise ValueError("Avatar crop exceeds source size")
    avatar_width = float(plan.get("avatar_width_fraction", 0.44))
    if not 0.1 <= avatar_width <= 0.8 or width * avatar_width * crop[3] / crop[2] > height:
        raise ValueError("Avatar proportions do not fit the frame")
    cue_data = json.loads(contained(job, plan["caption_cues"]).read_text())
    if cue_data.get("audio_sha256") != digest:
        raise ValueError("Caption cues belong to another audio")
    previous = 0.0
    for cue in cue_data["cues"]:
        if not 0 <= float(cue["start"]) < float(cue["end"]) <= duration + 0.1 or float(cue["start"]) < previous:
            raise ValueError("Caption cues are invalid or overlapping")
        previous = float(cue["end"])
    for overlay in plan.get("overlays", []):
        path = contained(job, overlay["file"])
        slot = slots.get(overlay["id"], {})
        if slot.get("approval_status") != "approved" or slot.get("local_file") != overlay["file"] or slot.get("file_sha256") != sha256(path):
            raise ValueError("Overlay is not an approved checksum-valid asset")
        if not 0 <= overlay["start"] < overlay["end"] <= duration + 0.1:
            raise ValueError("Invalid overlay interval")
    return {"width": width, "height": height, "fps": fps, "frames": frames,
            "duration": sum(frames) / fps, "boundaries": boundaries[:-1], "audio_sha256": digest}


def fit_filter(w, h, fraction):
    target = max(2, round(h * fraction / 2) * 2)
    foreground = f"scale={w}:{target}:force_original_aspect_ratio=increase,crop={w}:{target},setsar=1"
    if target == h:
        return f"[0:v]{foreground}[out]"
    return (f"[0:v]split[a][b];[a]scale={w}:{h}:force_original_aspect_ratio=increase,crop={w}:{h},boxblur=20:2[blur];"
            f"[b]{foreground}[sharp];[blur][sharp]overlay=0:(H-h)/2[out]")


def make_shot(job, shot, output, count, spec):
    w, h, fps = spec["width"], spec["height"], spec["fps"]
    source = contained(job, shot["file"])
    command = ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-threads", "2"]
    if shot["type"] == "image":
        command += ["-loop", "1", "-framerate", str(fps), "-i", str(source)]
        sharp = max(2, round(h * float(shot.get("sharp_fraction", 1)) / 2) * 2)
        # 2x canvas smooths integer crop movement; no scale oscillation.
        sw, sh = round(w * 2.2 / 2) * 2, sharp * 2
        motion = f"(iw-ow)*n/{max(1, count-1)}"
        if shot.get("pan", "left") == "left":
            motion = f"(iw-ow)-({motion})"
        pan = f"scale={sw}:{sh}:force_original_aspect_ratio=increase,crop={w*2}:{sh}:x='{motion}':y='(ih-oh)/2',scale={w}:{sharp},setsar=1"
        if sharp == h:
            filters = f"[0:v]{pan}[out]"
        else:
            filters = (f"[0:v]split[a][b];[a]scale={w}:{h}:force_original_aspect_ratio=increase,crop={w}:{h},boxblur=20:2[blur];"
                       f"[b]{pan}[sharp];[blur][sharp]overlay=0:(H-h)/2[out]")
    else:
        command += ["-i", str(source)]
        base = fit_filter(w, h, float(shot.get("sharp_fraction", 1)))
        filters = f"[0:v]trim=start={float(shot.get('source_in', 0))}:duration={count/fps},setpts=PTS-STARTPTS,fps={fps}[trimmed];" + base.replace("[0:v]", "[trimmed]")
    command += ["-filter_complex_threads", "1", "-filter_complex", filters, "-map", "[out]", "-an",
                "-frames:v", str(count), "-r", str(fps), "-c:v", "libx264", "-preset", "veryfast", "-crf", "18",
                "-pix_fmt", "yuv420p", "-g", str(fps), "-flags", "+cgop", "-movflags", "+faststart", str(output)]
    run(command)


def caption_layer(job, plan, spec, output_dir, font_path):
    w, h, fps = spec["width"], spec["height"], spec["fps"]
    cues = json.loads(contained(job, plan["caption_cues"]).read_text())["cues"]
    size = int(plan.get("caption_size", 46))
    font = ImageFont.truetype(font_path, size) if font_path else ImageFont.load_default(size=size)
    clear = output_dir / "clear.png"
    Image.new("RGBA", (w, h)).save(clear)
    schedule, cursor = [], 0
    for index, cue in enumerate(cues):
        start = round(float(cue["start"]) * fps)
        end = min(sum(spec["frames"]), round(float(cue["end"]) * fps))
        if end <= start:
            continue
        if start > cursor:
            schedule.append((clear, start-cursor))
        canvas = Image.new("RGBA", (w, h))
        drawing = ImageDraw.Draw(canvas)
        words, lines, line = str(cue["text"]).split(), [], ""
        for word in words:
            proposed = (line + " " + word).strip()
            if drawing.textlength(proposed, font=font) > w * 0.84 and line:
                lines.append(line)
                line = word
            else:
                line = proposed
        if line:
            lines.append(line)
        if len(lines) > 2 or any(drawing.textlength(line, font=font) > w * 0.9 for line in lines):
            raise ValueError("Caption exceeds two lines; revise cues instead of silently cutting text")
        y = h * float(plan.get("caption_center_y_fraction", 0.58)) - len(lines) * size * 0.6
        for line in lines:
            x = (w - drawing.textlength(line, font=font)) / 2
            drawing.text((x, y), line, font=font, fill="white", stroke_width=max(1, size//18), stroke_fill=(0, 0, 0, 230))
            y += size * 1.2
        path = output_dir / f"cue_{index:04d}.png"
        canvas.save(path)
        schedule.append((path, end-start))
        cursor = end
    total = sum(spec["frames"])
    if cursor < total:
        schedule.append((clear, total-cursor))
    if not schedule:
        schedule = [(clear, total)]
    listing = output_dir / "captions.ffconcat"
    # Generated filenames only; no untrusted path interpolation in concat scripts.
    listing.write_text("ffconcat version 1.0\n" + "".join(f"file {path.name}\noption framerate {fps}\nduration {count/fps:.9f}\n" for path, count in schedule)
                       + f"file {schedule[-1][0].name}\noption framerate {fps}\n")
    output = output_dir / "captions.webm"
    run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-f", "concat", "-safe", "0", "-i", str(listing),
         "-vf", f"fps={fps}", "-frames:v", str(total), "-c:v", "libvpx-vp9", "-pix_fmt", "yuva420p",
         "-auto-alt-ref", "0", "-b:v", "0", "-crf", "32", "-threads", "2", str(output)])
    return output


def compose(job, plan, spec, env):
    import hashlib
    fingerprint = hashlib.sha256(json.dumps(plan, sort_keys=True, ensure_ascii=False).encode()).hexdigest()[:12]
    output_dir = job / "edit" / ("render_" + fingerprint)
    if output_dir.exists():
        raise ValueError("Render work directory exists; inspect it or choose a new plan revision")
    output_dir.mkdir(parents=True)
    segments = []
    for index, (shot, count) in enumerate(zip(plan["shots"], spec["frames"])):
        destination = output_dir / f"shot_{index:04d}.mp4"
        make_shot(job, shot, destination, count, spec)
        segments.append(destination)
    listing = output_dir / "background.ffconcat"
    listing.write_text("ffconcat version 1.0\n" + "".join(f"file {path.name}\n" for path in segments))
    background = output_dir / "background.mp4"
    run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-f", "concat", "-safe", "0", "-i", str(listing), "-c:v", "copy", str(background)])
    caption = caption_layer(job, plan, spec, output_dir, env.get("CAPTION_FONT_PATH") or None)
    avatar = contained(job, plan["avatar"])
    command = ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", str(background)]
    codec = next(s["codec_name"] for s in probe(avatar)["streams"] if s["codec_type"] == "video")
    if codec == "vp9":
        command += ["-c:v", "libvpx-vp9"]
    command += ["-i", str(avatar), "-c:v", "libvpx-vp9", "-i", str(caption), "-i", str(contained(job, plan["audio"]))]
    crop = plan["avatar_crop"]
    avatar_width = max(2, round(spec["width"] * float(plan.get("avatar_width_fraction", 0.44)) / 2) * 2)
    filters = [f"[1:v]crop={crop[2]}:{crop[3]}:{crop[0]}:{crop[1]},scale={avatar_width}:-2,setsar=1[avatar]",
               "[0:v][avatar]overlay=0:H-h:eof_action=pass[base]"]
    current = "base"
    for index, overlay in enumerate(plan.get("overlays", [])):
        command += ["-loop", "1", "-i", str(contained(job, overlay["file"]))]
        filters.append(f"[{index+4}:v]scale={int(overlay['width'])}:-2[ov{index}]")
        filters.append(f"[{current}][ov{index}]overlay={int(overlay['x'])}:{int(overlay['y'])}:enable='gte(t,{float(overlay['start'])})*lt(t,{float(overlay['end'])})'[layer{index}]")
        current = f"layer{index}"
    filters.append(f"[{current}][2:v]overlay=0:0:eof_action=pass[out]")
    render = output_dir / "preview.mp4"
    command += ["-filter_complex_threads", "1", "-filter_complex", ";".join(filters), "-map", "[out]", "-map", "3:a:0",
                "-frames:v", str(sum(spec["frames"])), "-t", str(spec["duration"]), "-r", str(spec["fps"]),
                "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p", "-flags", "+cgop",
                "-c:a", "aac", "-b:a", "128k", "-ar", "48000", "-movflags", "+faststart", str(render)]
    run(command)
    preview = job / "preview.mp4"
    if preview.exists():
        archive = job / "edit/history/previews" / now().replace(":", "-")
        archive.mkdir(parents=True)
        shutil.move(str(preview), str(archive / "preview.mp4"))
    shutil.copyfile(render, preview)
    json_write(output_dir / "render_report.json", {**spec, "preview_sha256": sha256(preview), "api_calls": 0})
    state_path = job / "job.json"
    state = json.loads(state_path.read_text())
    state.setdefault("artifacts", {}).update(preview=str(preview), render_source=str(render))
    state["steps"].update(composition="completed", qa="pending", final_approval="awaiting_approval")
    json_write(state_path, state)
    return preview


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--env", required=True, type=Path)
    parser.add_argument("--job-dir", required=True, type=Path)
    parser.add_argument("--plan", required=True, type=Path)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    env_path, job, plan_path = args.env.resolve(strict=True), args.job_dir.resolve(strict=True), args.plan.resolve(strict=True)
    workspace_job(env_path, job)
    workspace_profile(env_path)
    if not plan_path.is_relative_to(job):
        raise SystemExit("Render plan must belong to this job")
    plan = json.loads(plan_path.read_text())
    spec = validate(job, plan)
    if args.dry_run:
        print(json.dumps({**spec, "paid_calls": 0}, ensure_ascii=False))
    else:
        print(compose(job, plan, spec, load_env(env_path)))


if __name__ == "__main__":
    main()
