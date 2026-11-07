# ChainWatch v0.1 — frozen exploratory experiment

ChainWatch is a small, reproducible experiment about monitoring actions after
authority has moved across multiple delegation handoffs.

Research question: does delegation-aware monitoring reduce false-safe decisions
compared with event-local monitoring when agent authority is distributed across
multiple handoffs?

This repository contains the deterministic baseline only. Its completed
scientific review is preserved in [docs/PROTOCOL_LOCK.md](docs/PROTOCOL_LOCK.md)
and [docs/GROUND_TRUTH.md](docs/GROUND_TRUTH.md). The mechanical freeze adds
integrity and behavior checks without changing the original corpus, code,
review, or initial results. This is a post-exploratory lock, not preregistration.
It does not
contain a learned monitor, cloud inference, deployment, or a claim that the
design targets have already been measured outside this checkout.

## Locked experiment

- 24 fixed synthetic scenarios, six in each of four families.
- The four families are legitimate delegation, authority escalation, missing
  authorization evidence, and inconsistent provenance.
- The same scenarios and ground truth are evaluated by all three monitors.
- The monitors are event_local, delegation_aware, and unknown_safe.
- Decisions are ALLOW, DENY, or UNKNOWN.
- Unsafe-action recall, false-safe rate, legitimate-action false positives, and
  UNKNOWN frequency are reported separately.
- UNKNOWN is an abstention cost. It is never counted as detecting an unsafe
  action.

The protocol and evidence semantics are in
[docs/PROTOCOL.md](docs/PROTOCOL.md). The machine-readable event fields are in
[docs/SCENARIO_SCHEMA.md](docs/SCENARIO_SCHEMA.md).

## Reproduce the baseline

The frozen gate requires CPython 3.14.6, as declared in `.python-version`, and
uses only the standard library. No dependency installation is required.

    make verify

The canonical command first checks the pinned runtime and exact byte identities
of 15 original files, then runs the tests and compares the initial result with
a fresh in-memory rerun. The contracts check all 72 decisions, evidence records,
truth balance, metric denominators, error handling, and known legacy behavior.
The identities are in [locks/v0.1.json](locks/v0.1.json), whose own digest is
pinned in the verifier.

To save a replay, choose a new output path:

    make run-baseline RERUN_OUTPUT=results/reruns/v0.1-replay-01.json

The command refuses to overwrite any existing file and requires the replay to
match the original result byte for byte. A mismatched replay is retained at the
new path and the command fails. `make run-baseline` without an output path fails.
Never regenerate the initial manifest to accommodate a change: cases, labels,
monitor logic, schema behavior, or scoring corrections need a separate version.

The checked-in manifest is
[results/v0.1-initial.json](results/v0.1-initial.json). It contains the corpus
digest, per-monitor metrics, per-scenario decisions, and machine-readable
evidence records.

See [docs/FREEZE.md](docs/FREEZE.md) for enforcement boundaries and versioning,
and [docs/AUDIT.md](docs/AUDIT.md) for preserved results, validation evidence,
and unresolved scientific limitations.

## Provenance boundary

The starting checkout had no commit, no remote, and no source files. This
initial scaffold records that state in [docs/PROVENANCE.md](docs/PROVENANCE.md).
No private governance code, external dataset, or copied implementation is
bundled here. The 1,500 Adaption credits are planning context only; this
baseline spends none of them.

The private GitHub repository was subsequently created at
[jorgenunez1ghub/ChainWatch](https://github.com/jorgenunez1ghub/ChainWatch) and
linked as `origin`. The freeze was established before any initial commit;
the preserved provenance record describes the starting state.

## Current evidence boundary

The baseline demonstrates that the fixed corpus can be loaded, validated,
evaluated deterministically, and summarized with the declared metrics. It does
not demonstrate real-world monitoring performance, generalization, deployment
behavior, or the value of a learned monitor.
