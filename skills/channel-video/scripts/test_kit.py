"""No-network behavior tests, using only synthetic temporary workspaces."""
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from unittest.mock import patch
from common import sha256, json_write


HERE = Path(__file__).resolve().parent


def load(name):
    spec = importlib.util.spec_from_file_location(name, HERE / (name + ".py"))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def fixture(root):
    root = root.resolve()
    env = root / ".env"
    env.write_text("ELEVENLABS_API_KEY=test-only\nELEVENLABS_VOICE_ID=test-voice\nELEVENLABS_MODEL_ID=test-model\n"
                   "ELEVENLABS_STT_MODEL_ID=test-stt\nHEYGEN_API_KEY=test-only\nHEYGEN_AVATAR_ID=test-avatar\nHEYGEN_ENGINE=avatar_iv\n")
    json_write(root / "channel_profile.json", {"approved": True, "channel_name": "Test channel", "language_code": "en", "voice_settings": {}})
    (root / "channel_context.md").write_text("Synthetic test context")
    topic = root / "videos/topic"
    topic.mkdir(parents=True)
    reel = topic / "reel_test.md"
    reel.write_text("Synthetic script")
    speech = topic / "falas_test.txt"
    speech.write_text("First paragraph.\n\nSecond paragraph.\n\nThird paragraph.\n\nFourth paragraph.")
    with patch.object(sys, "argv", ["init_job.py", str(reel)]), redirect_stdout(io.StringIO()):
        load("init_job").main()
    return env, topic / "video_test", speech


class KitTests(unittest.TestCase):
    def test_installer_refuses_overwrite_and_keeps_configuration_blank(self):
        # Included only when tests run from the distributable source tree.
        package = HERE.parents[2]
        installer_path = package / "install.py"
        if not installer_path.is_file():
            self.skipTest("Installer integration runs from the source package")
        spec = importlib.util.spec_from_file_location("kit_install", installer_path)
        installer = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(installer)
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "workspace"
            skill_root = Path(tmp) / "skills"
            installed = installer.install(target, install_skill=True, skill_root=skill_root)
            self.assertTrue((skill_root / "channel-video/SKILL.md").is_file())
            self.assertFalse(json.loads((installed / "channel_profile.json").read_text())["approved"])
            for line in (installed / ".env").read_text().splitlines():
                if line and not line.startswith("#"):
                    self.assertEqual(line.split("=", 1)[1], "")
            with self.assertRaisesRegex(ValueError, "existing files"):
                installer.install(target)
            with self.assertRaisesRegex(ValueError, "already exists"):
                installer.install(Path(tmp) / "another", install_skill=True, skill_root=skill_root)

    def test_board_escapes_untrusted_text_and_rejects_script_urls(self):
        module = load("contact_sheet")
        result = module.card({"id": "A", "narration": "<script>alert(1)</script>",
                              "source_page_url": "javascript:alert(1)", "media_url": "javascript:alert(1)",
                              "preview_url": "../media/candidates/A.jpg"})
        self.assertNotIn("<script>", result)
        self.assertNotIn("javascript:", result)
        self.assertIn("../media/candidates/A.jpg", result)

    def test_job_creates_only_empty_final_directory(self):
        with tempfile.TemporaryDirectory() as tmp:
            _, job, _ = fixture(Path(tmp))
            self.assertTrue((job / "job.json").is_file())
            self.assertEqual(list((job.parent / "video final").iterdir()), [])

    def test_tts_is_scoped_configurable_and_paid_guarded(self):
        module = load("elevenlabs_audio")
        with tempfile.TemporaryDirectory() as tmp:
            env, job, speech = fixture(Path(tmp))
            argv = ["tts", "--env", str(env), "--job-dir", str(job), "--script-file", str(speech), "--smoke-test"]
            self.assertEqual(module.extract_script(speech, True).count("paragraph"), 3)
            output = io.StringIO()
            with patch.object(sys, "argv", argv + ["--dry-run"]), redirect_stdout(output), patch.object(module, "generate") as paid:
                module.main()
                paid.assert_not_called()
            report = json.loads(output.getvalue())
            self.assertEqual(report["model"], "test-model")
            self.assertEqual(report["language"], "en")
            self.assertNotIn("voice_id", report)
            with patch.object(sys, "argv", argv), patch.object(module, "generate") as paid:
                with self.assertRaisesRegex(SystemExit, "allow-paid"):
                    module.main()
                paid.assert_not_called()
            profile = env.parent / "channel_profile.json"
            json_write(profile, {"approved": False})
            with patch.object(sys, "argv", argv + ["--allow-paid"]), patch.object(module, "generate") as paid:
                with self.assertRaisesRegex(ValueError, "onboarding"):
                    module.main()
                paid.assert_not_called()

    def test_audio_approval_and_external_audio_only_payload(self):
        heygen = load("heygen_video")
        payload = heygen.build_video_payload("test-avatar", "test-asset", "full", "avatar_iv", "1080p", None)
        self.assertEqual(payload["audio_asset_id"], "test-asset")
        for name in ("script", "voice_id", "voice_settings", "audio_url"):
            self.assertNotIn(name, payload)
        with tempfile.TemporaryDirectory() as tmp:
            env, job, _ = fixture(Path(tmp))
            audio = job / "audio/elevenlabs_full_test.mp3"
            audio.write_bytes(b"ID3test")
            json_write(audio.with_suffix(".json"), {"audio_sha256": sha256(audio)})
            argv = ["heygen", "--env", str(env), "--job-dir", str(job), "--audio-file", str(audio), "--dry-run"]
            with patch.object(sys, "argv", argv):
                with self.assertRaisesRegex(SystemExit, "not approved"):
                    heygen.main()
            approval = load("approve_audio")
            with patch.object(sys, "argv", ["approve", "--job-dir", str(job), "--audio-file", str(audio)]), redirect_stdout(io.StringIO()):
                approval.main()
            output = io.StringIO()
            with patch.object(sys, "argv", argv), redirect_stdout(output), patch.object(heygen, "upload_audio") as paid:
                heygen.main()
                paid.assert_not_called()
            self.assertTrue(json.loads(output.getvalue())["approved"])
            audio.write_bytes(b"ID3changed")
            with patch.object(sys, "argv", argv):
                with self.assertRaisesRegex(SystemExit, "not approved"):
                    heygen.main()

    def test_approval_revision_and_missing_decisions(self):
        approval = load("import_approvals")
        with tempfile.TemporaryDirectory() as tmp:
            manifest = Path(tmp) / "manifest.json"
            decisions = Path(tmp) / "decisions.json"
            json_write(manifest, {"slots": [{"id": "A"}, {"id": "B"}]})
            json_write(decisions, {"manifest_sha256": sha256(manifest), "decisions": {"A": {"decision": "approved"}}})
            result = approval.apply(manifest, decisions)
            self.assertEqual(result, {"approved": 1, "rejected": 0, "pending": 1})
            with self.assertRaisesRegex(ValueError, "another manifest"):
                approval.apply(manifest, decisions)

    def test_cues_keep_word_times_and_skip_events(self):
        module = load("transcribe")
        words = [{"type": "word", "text": "Hello", "start": 0.2, "end": 0.6},
                 {"type": "audio_event", "text": "noise", "start": 0.6, "end": 0.7},
                 {"type": "word", "text": "world.", "start": 0.8, "end": 1.1}]
        self.assertEqual(module.cues_from_words(words), [{"start": 0.2, "end": 1.1, "text": "Hello world."}])

    @unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe"), "FFmpeg/FFprobe missing")
    def test_synthetic_render_and_hash_identical_final(self):
        render, delivery = load("render"), load("save_final")
        with tempfile.TemporaryDirectory() as tmp:
            env, job, _ = fixture(Path(tmp))
            audio = job / "audio/take.mp3"
            subprocess.run(["ffmpeg", "-v", "error", "-f", "lavfi", "-i", "sine=frequency=400:duration=2", "-c:a", "libmp3lame", str(audio)], check=True)
            digest = sha256(audio)
            state = json.loads((job / "job.json").read_text())
            state["audio_approvals"] = {digest: {"audio_file": str(audio)}}
            json_write(job / "job.json", state)
            avatar = job / "heygen/avatar.mov"
            subprocess.run(["ffmpeg", "-v", "error", "-f", "lavfi", "-i", "color=c=green@0.7:s=64x80:r=30:d=2,format=rgba", "-c:v", "qtrle", str(avatar)], check=True)
            json_write(avatar.with_suffix(".json"), {"source_audio_sha256": digest})
            picture = job / "media/approved/photo.png"
            subprocess.run(["ffmpeg", "-v", "error", "-f", "lavfi", "-i", "testsrc2=s=280x320:d=1", "-frames:v", "1", str(picture)], check=True)
            clip = job / "media/approved/clip.mp4"
            subprocess.run(["ffmpeg", "-v", "error", "-f", "lavfi", "-i", "testsrc2=s=240x180:r=30:d=2", "-c:v", "libx264", str(clip)], check=True)
            json_write(job / "media/asset_manifest.json", {"audio_sha256": digest, "slots": [
                {"id": "S01", "approval_status": "approved", "local_file": "media/approved/photo.png", "file_sha256": sha256(picture)},
                {"id": "S02", "approval_status": "approved", "local_file": "media/approved/clip.mp4", "file_sha256": sha256(clip)}]})
            json_write(job / "transcripts/cues.json", {"audio_sha256": digest, "cues": [{"start": 0.1, "end": 0.8, "text": "Teste"}]})
            plan = {"width": 180, "height": 320, "fps": 30, "audio": "audio/take.mp3", "avatar": "heygen/avatar.mov",
                    "avatar_crop": [0, 0, 64, 80], "manifest": "media/asset_manifest.json", "caption_cues": "transcripts/cues.json", "caption_size": 16,
                    "shots": [{"id": "S01", "file": "media/approved/photo.png", "type": "image", "duration": 1.0},
                              {"id": "S02", "file": "media/approved/clip.mp4", "type": "video", "duration": 1.0, "source_in": 0.5, "sharp_fraction": 0.8}]}
            plan_path = job / "edit/render_plan.json"
            json_write(plan_path, plan)
            spec = render.validate(job, plan)
            preview = render.compose(job, plan, spec, {})
            self.assertTrue(preview.is_file())
            info = render.probe(preview)
            self.assertEqual({s["codec_type"] for s in info["streams"]}, {"video", "audio"})
            report_output = io.StringIO()
            with patch.object(sys, "argv", ["qa", "--job-dir", str(job), "--plan", str(plan_path)]), redirect_stdout(report_output):
                with self.assertRaises(SystemExit) as status:
                    load("qa").main()
                self.assertEqual(status.exception.code, 0)
            report = json.loads(report_output.getvalue())
            self.assertTrue(report["decoded_without_errors"])
            self.assertTrue(report["visual_review_required"])
            qa_dir = Path(json.loads((job / "job.json").read_text())["artifacts"]["qa_report"]).parent
            self.assertEqual(len(list(qa_dir.glob("frame_*.png"))), len(report["cut_frames"]))
            with self.assertRaisesRegex(ValueError, "approval"):
                delivery.save_final(job / "job.json", preview, "approved")
            result = delivery.save_final(job / "job.json", preview, "user_requested_consolidation")
            self.assertEqual(sha256(Path(result["path"])), sha256(preview))
            self.assertEqual(len(list((job.parent / "video final").iterdir())), 1)
            plan["shots"][0]["file"] = "../outside.jpg"
            with self.assertRaises((ValueError, FileNotFoundError)):
                render.validate(job, plan)


if __name__ == "__main__":
    unittest.main(verbosity=2)
