"""Integrity and safe replay tooling; the reviewed v0.1 implementation is unchanged."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import platform
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
LOCK_PATH = Path("locks/v0.1.json")
# This anchor is intentionally independent of the editable identities in the lock.
# A new experiment needs its own version and lock, not an updated v0.1 anchor.
LOCK_SHA256 = "8a5d3342cd4a845a20e84ff0b84417a974c4bfdeef3f6fe93687365a663bbc66"
CORPUS_PATH = Path("data/scenarios.json")
RESULT_PATH = Path("results/v0.1-initial.json")


class FreezeError(ValueError):
    """The preserved experiment cannot be verified or safely replayed."""


def verify_integrity(root: Path = ROOT) -> dict[str, Any]:
    """Check exact file bytes before importing or executing the frozen experiment."""
    lock_path = root / LOCK_PATH
    if lock_path.is_symlink():
        raise FreezeError(f"lock must be a regular file: {LOCK_PATH}")
    try:
        lock_bytes = lock_path.read_bytes()
    except OSError as error:
        raise FreezeError(f"cannot read {LOCK_PATH}: {error}") from error
    if hashlib.sha256(lock_bytes).hexdigest() != LOCK_SHA256:
        raise FreezeError(f"lock identity mismatch: {LOCK_PATH}; do not relock v0.1")
    lock = json.loads(lock_bytes)
    errors = []
    for relative, identity in lock["files"].items():
        path = root / relative
        if path.is_symlink():
            errors.append(f"{relative}: frozen artifact must be a regular file")
            continue
        try:
            content = path.read_bytes()
        except OSError as error:
            errors.append(f"{relative}: cannot read frozen artifact: {error}")
            continue
        if (
            len(content) != identity["size_bytes"]
            or hashlib.sha256(content).hexdigest() != identity["sha256"]
        ):
            errors.append(f"{relative}: frozen byte identity mismatch")
    if errors:
        raise FreezeError("\n".join(errors))
    return lock


def verify_runtime(lock: dict[str, Any]) -> None:
    required = lock["runtime"]
    actual = (platform.python_implementation(), platform.python_version())
    expected = (required["implementation"], required["version"])
    if actual != expected:
        raise FreezeError(
            f"frozen replay requires {expected[0]} {expected[1]}; "
            f"running {actual[0]} {actual[1]}"
        )


def replay(output: Path, root: Path = ROOT) -> None:
    """Write a new replay artifact, never replace an existing file."""
    lock = verify_integrity(root)
    verify_runtime(lock)
    if output.exists() or output.is_symlink():
        raise FreezeError(f"refusing to overwrite existing output: {output}")

    # Import only after source identities have passed. Keep the historical
    # manifest's display path while reading the corpus from this checkout.
    from chainwatch.models import load_scenarios
    from chainwatch.runner import build_manifest

    scenarios = load_scenarios(root / CORPUS_PATH)
    manifest = build_manifest(scenarios, root / CORPUS_PATH)
    manifest["corpus"]["path"] = CORPUS_PATH.as_posix()
    content = (
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True, allow_nan=False)
        + "\n"
    ).encode("utf-8")
    output.parent.mkdir(parents=True, exist_ok=True)
    try:
        with output.open("xb") as stream:
            stream.write(content)
    except FileExistsError as error:
        raise FreezeError(f"refusing to overwrite existing output: {output}") from error
    if content != (root / RESULT_PATH).read_bytes():
        raise FreezeError(f"replay mismatch; failed artifact preserved at {output}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="chainwatch.freeze")
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("check", help="verify frozen bytes and the pinned runtime")
    replay_parser = commands.add_parser("replay", help="write a new, verified v0.1 replay")
    replay_parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args(argv)
    try:
        if args.command == "check":
            lock = verify_integrity(ROOT)
            verify_runtime(lock)
            print(f"verified v0.1 byte identities: {len(lock['files'])} files; runtime pinned")
        else:
            replay(args.output, ROOT)
            print(f"verified byte-identical v0.1 replay: {args.output}")
    except (FreezeError, OSError, ValueError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
