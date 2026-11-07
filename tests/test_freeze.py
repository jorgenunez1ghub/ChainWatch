from __future__ import annotations

from contextlib import redirect_stderr, redirect_stdout
import copy
import hashlib
import io
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from chainwatch import freeze
from chainwatch.models import load_scenarios
from chainwatch.runner import build_manifest


class FreezeTests(unittest.TestCase):
    def setUp(self) -> None:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.lock = freeze.verify_integrity(ROOT)
        for relative in [*self.lock["files"], str(freeze.LOCK_PATH)]:
            target = self.root / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / relative, target)

    def test_original_file_identities_and_runtime_match(self) -> None:
        self.assertEqual(len(self.lock["files"]), 15)
        self.assertEqual(self.lock["source_identity"]["git_commit"], None)
        self.assertEqual(freeze.verify_integrity(self.root), self.lock)
        freeze.verify_runtime(self.lock)

    def test_every_frozen_file_rejects_byte_only_drift(self) -> None:
        for relative in self.lock["files"]:
            path = self.root / relative
            original = path.read_bytes()
            path.write_bytes(original + b"\n")
            with self.subTest(path=relative), self.assertRaisesRegex(freeze.FreezeError, relative.replace(".", r"\.")):
                freeze.verify_integrity(self.root)
            path.write_bytes(original)

    def test_coordinated_corpus_and_regenerated_result_cannot_redefine_v01(self) -> None:
        source = self.root / freeze.CORPUS_PATH
        raw = json.loads(source.read_text())
        raw["scenarios"][0]["ground_truth"] = "unsafe"
        source.write_text(json.dumps(raw))
        regenerated = build_manifest(load_scenarios(source), source)
        regenerated["corpus"]["path"] = str(freeze.CORPUS_PATH)
        (self.root / freeze.RESULT_PATH).write_text(json.dumps(regenerated))
        with self.assertRaises(freeze.FreezeError) as failure:
            freeze.verify_integrity(self.root)
        self.assertIn(str(freeze.CORPUS_PATH), str(failure.exception))
        self.assertIn(str(freeze.RESULT_PATH), str(failure.exception))

    def test_editing_the_lock_to_match_drift_is_rejected(self) -> None:
        relative = str(freeze.CORPUS_PATH)
        path = self.root / relative
        content = path.read_bytes() + b"\n"
        path.write_bytes(content)
        lock = copy.deepcopy(self.lock)
        lock["files"][relative] = {"sha256": hashlib.sha256(content).hexdigest(), "size_bytes": len(content)}
        (self.root / freeze.LOCK_PATH).write_text(json.dumps(lock))
        with self.assertRaisesRegex(freeze.FreezeError, "lock identity mismatch"):
            freeze.verify_integrity(self.root)

    def test_missing_file_and_symlink_substitution_are_rejected(self) -> None:
        path = self.root / freeze.CORPUS_PATH
        original = path.read_bytes()
        path.unlink()
        with self.assertRaisesRegex(freeze.FreezeError, "cannot read frozen artifact"):
            freeze.verify_integrity(self.root)
        replacement = self.root / "same-bytes.json"
        replacement.write_bytes(original)
        path.symlink_to(replacement)
        with self.assertRaisesRegex(freeze.FreezeError, "regular file"):
            freeze.verify_integrity(self.root)

    def test_different_runtime_is_reported(self) -> None:
        with patch("chainwatch.freeze.platform.python_version", return_value="3.13.0"):
            with self.assertRaisesRegex(freeze.FreezeError, "requires CPython 3.14.6"):
                freeze.verify_runtime(self.lock)

    def test_replay_is_byte_identical_in_a_new_location(self) -> None:
        output = self.root / "reruns/new.json"
        freeze.replay(output, self.root)
        self.assertEqual(output.read_bytes(), (ROOT / freeze.RESULT_PATH).read_bytes())
        freeze.verify_integrity(self.root)

    def test_replay_refuses_all_existing_targets_including_frozen_inputs(self) -> None:
        sentinel = self.root / "existing.json"
        sentinel.write_text("preserve me")
        for relative in [*self.lock["files"], str(freeze.LOCK_PATH), "existing.json"]:
            path = self.root / relative
            original = path.read_bytes()
            with self.subTest(path=relative), self.assertRaisesRegex(freeze.FreezeError, "refusing to overwrite"):
                freeze.replay(path, self.root)
            self.assertEqual(path.read_bytes(), original)

    def test_replay_does_not_clobber_a_file_created_after_the_initial_check(self) -> None:
        output = self.root / "race.json"
        original_open = Path.open

        def create_before_exclusive_open(path, mode="r", *args, **kwargs):
            if path == output and mode == "xb":
                with original_open(output, "wb") as stream:
                    stream.write(b"created by another writer")
            return original_open(path, mode, *args, **kwargs)

        with patch.object(Path, "open", create_before_exclusive_open):
            with self.assertRaisesRegex(freeze.FreezeError, "refusing to overwrite"):
                freeze.replay(output, self.root)
        self.assertEqual(output.read_bytes(), b"created by another writer")

    def test_drift_stops_replay_before_evaluating_or_writing(self) -> None:
        (self.root / "src/chainwatch/monitors.py").write_text("changed source")
        output = self.root / "must-not-exist.json"
        with patch("chainwatch.runner.build_manifest") as build:
            with self.assertRaises(freeze.FreezeError):
                freeze.replay(output, self.root)
        build.assert_not_called()
        self.assertFalse(output.exists())

    def test_standalone_check_rejects_source_drift_before_importing_the_package(self) -> None:
        script = self.root / "src/chainwatch/freeze.py"
        shutil.copyfile(ROOT / "src/chainwatch/freeze.py", script)
        (self.root / "src/chainwatch/__init__.py").write_text(
            'raise RuntimeError("changed package was executed")\n'
        )
        checked = subprocess.run(
            [sys.executable, str(script), "check"],
            cwd=self.root, capture_output=True, text=True, check=False,
        )
        self.assertEqual(checked.returncode, 1)
        self.assertIn("src/chainwatch/__init__.py: frozen byte identity mismatch", checked.stderr)
        self.assertNotIn("changed package was executed", checked.stderr)

    def test_mismatched_replay_is_preserved_and_reported_as_failure(self) -> None:
        output = self.root / "failed-replay.json"
        failed = {"corpus": {"path": "irrelevant"}, "unexpected": "result"}
        with patch("chainwatch.runner.build_manifest", return_value=failed):
            with self.assertRaisesRegex(freeze.FreezeError, "failed artifact preserved"):
                freeze.replay(output, self.root)
        self.assertEqual(json.loads(output.read_text())["unexpected"], "result")
        freeze.verify_integrity(self.root)

    def test_cli_returns_failure_for_drift_and_success_for_clean_copy(self) -> None:
        stdout, stderr = io.StringIO(), io.StringIO()
        with patch.object(freeze, "ROOT", self.root), redirect_stdout(stdout), redirect_stderr(stderr):
            self.assertEqual(freeze.main(["check"]), 0)
            (self.root / freeze.RESULT_PATH).write_text("corrupted artifact")
            self.assertEqual(freeze.main(["check"]), 1)
        self.assertIn("15 files", stdout.getvalue())
        self.assertIn(str(freeze.RESULT_PATH), stderr.getvalue())


if __name__ == "__main__":
    unittest.main()
