from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any

from .models import CorpusError, load_scenarios
from .runner import build_manifest


def _write_json(path: Path, document: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(document, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="chainwatch")
    subparsers = parser.add_subparsers(dest="command", required=True)

    run_parser = subparsers.add_parser("run", help="run all deterministic monitors")
    run_parser.add_argument("--scenarios", required=True, type=Path)
    run_parser.add_argument("--output", required=True, type=Path)

    verify_parser = subparsers.add_parser(
        "verify",
        help="compare a fresh deterministic result with a saved manifest",
    )
    verify_parser.add_argument("--scenarios", required=True, type=Path)
    verify_parser.add_argument("--manifest", required=True, type=Path)
    return parser


def _run(args: argparse.Namespace) -> int:
    scenarios = load_scenarios(args.scenarios)
    manifest = build_manifest(scenarios, args.scenarios)
    _write_json(args.output, manifest)
    print(
        f"wrote {args.output} with {len(scenarios)} scenarios and "
        f"{len(manifest['monitors'])} monitors"
    )
    return 0


def _verify(args: argparse.Namespace) -> int:
    scenarios = load_scenarios(args.scenarios)
    expected = build_manifest(scenarios, args.scenarios)
    try:
        actual = json.loads(args.manifest.read_text(encoding="utf-8"))
    except OSError as error:
        print(f"manifest read failed: {error}", file=sys.stderr)
        return 1
    except json.JSONDecodeError as error:
        print(f"manifest JSON is invalid: {error}", file=sys.stderr)
        return 1

    if actual != expected:
        print(f"manifest mismatch: {args.manifest}", file=sys.stderr)
        return 1
    print(f"verified deterministic manifest: {args.manifest}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = _parser()
    args = parser.parse_args(argv)
    try:
        if args.command == "run":
            return _run(args)
        return _verify(args)
    except (CorpusError, ValueError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
