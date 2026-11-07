# Mechanical freeze of the v0.1 exploratory experiment

Recorded 2026-11-07. This enforces the completed review in
[PROTOCOL_LOCK.md](PROTOCOL_LOCK.md) and [GROUND_TRUTH.md](GROUND_TRUTH.md).
Those documents remain unchanged. No monitor, schema-loader, scoring, case,
label, or original result correction is included in this freeze.

## What is bound

[../locks/v0.1.json](../locks/v0.1.json) records SHA-256 and byte length for
15 original files: the corpus, initial result, five original Python modules,
five original protocol/review documents, `.python-version`, `pyproject.toml`,
and the original test suite. This includes the runner and loader as well as
the monitors. The canonical JSON corpus digest is recorded separately from
the exact file-byte identity.

The lock's exact-byte SHA-256 is
`8a5d3342cd4a845a20e84ff0b84417a974c4bfdeef3f6fe93687365a663bbc66`,
pinned in [../src/chainwatch/freeze.py](../src/chainwatch/freeze.py). Editing
the corpus and regenerating its result, or updating the lock's file hashes,
does not satisfy the gate. There is no command that refreshes the v0.1 lock.
The snapshot has no commit identity: this checkout was on an unborn `main`
branch when locked. The later creation of a private GitHub remote does not
supply a historical commit or make the experiment preregistered.

The added verifier, added contract tests, this audit documentation, README,
Makefile, and ignore rules are maintenance tooling outside those 15 original
artifacts. Fixing tooling must retain the lock anchor and frozen behavior.

## Supported commands

Run these from the repository root with CPython 3.14.6 available as `python3`,
or select its executable with `make PYTHON=/path/to/python3 verify`.

| Command | Contract |
| --- | --- |
| `make verify` | Check byte identities and exact runtime first, run all tests, then compare the original manifest with an in-memory replay. Integrity precedes execution of original package code, including under parallel Make. |
| `make check-integrity` | Check the 15 file identities, lock anchor, and CPython version without importing the original package. |
| `make test` | Run the tests alone; the canonical handoff gate remains `make verify`. |
| `make check-manifest` | Historical reproduction check alone; it does not enforce the freeze by itself. |
| `make run-baseline RERUN_OUTPUT=/path/to/new.json` | Check integrity/runtime, evaluate all 24 cases with all monitors, exclusively create a new file, and require exact byte equality with the initial result. |

The canonical integrity entry point executes the standalone verifier rather
than importing `chainwatch` before checking its source. Replay reads this
checkout's corpus and retains `data/scenarios.json` as the manifest display
path, so moving the checkout does not change the result bytes. Existing output
files, including frozen files and symlinks, are refused; exclusive file creation
also handles another writer creating the target after the initial check.
A mismatch leaves the new artifact available for inspection and returns failure.
An exception invalidates the run; it is never converted into UNKNOWN or a
silently excluded scenario.

No third-party dependency manager is used by this standard-library-only project.
There is nothing to install or resolve, so no unrelated dependency manager or
dependency lockfile was introduced. `locks/v0.1.json` is an experiment identity
lock, not a dependency lock or a guarantee about the Python binary's origin.

## Contract coverage

[../tests/test_v01_contract.py](../tests/test_v01_contract.py) has explicit
expectations transcribed from the review, rather than deriving expected
decisions from the monitor being tested. It checks all 24 ordered IDs, truth
and family allocations, observations, all 72 decisions and evidence records,
counts and denominators, and the unsafe DENY/ALLOW/UNKNOWN partition.
Ground-truth flips and irrelevant local claims leave the applicable monitor
outputs unchanged; malformed declared inputs and monitor failures do not
silently become abstentions.

Characterization tests deliberately retain v0.1's graph/reference mismatch,
reference-only `used_event_ids`, ignored kind/authorization-ID/order constraints,
and zero-denominator behavior. They are regression evidence, not endorsements
of production authorization semantics. The initial artifact only has nonzero
metric denominators. The audit's family table leaves absent truth groups
undefined instead of calling them perfect or assigning them a success rate.

[../tests/test_freeze.py](../tests/test_freeze.py) tests byte-only edits to
every frozen artifact, coordinated corpus/result drift, lock edits, missing
files, symlink replacement, runtime mismatch, source checks before package
import, byte-identical replay, overwrite/race protection, and failed replay
retention. All destructive fixtures use temporary copies.

## Boundaries and later corrections

This is a local drift guard, not filesystem immutability or an externally signed
archive. A person able to edit both the verifier and the lock can bypass it.
The unchanged legacy `chainwatch.cli run` is still a low-level writer that can
overwrite a supplied path. Use the supported replay command; the integrity gate
detects changes made through direct editing or legacy commands after the fact.
Neither reproduction checks nor contract tests independently establish the
scientific truth of labels or generalization.

Changes to cases, labels, monitor logic, evidence semantics, loader acceptance,
or scoring must use a new experiment version with separate implementation,
corpus/result paths, identity lock, and a stated rationale. Keep the v0.1 paths
and lock intact. Run both versions for an explicitly labeled comparison rather
than replacing this artifact. Candidate corrections and scientific gaps are
listed in [AUDIT.md](AUDIT.md); none has been implemented as part of v0.1.
