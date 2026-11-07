# Audit of the frozen ChainWatch v0.1 experiment

Recorded 2026-11-07. Status: mechanically frozen exploratory result. The
scientific review in [PROTOCOL_LOCK.md](PROTOCOL_LOCK.md) and retrospective
adjudication in [GROUND_TRUTH.md](GROUND_TRUTH.md) are reused unchanged, not
repeated or represented as independent review. The lock followed observation
of the original results and is not preregistration.

## Preserved evidence and findings

The corpus, all five original implementation modules, initial result, original
tests, runtime metadata, and five original protocol/review documents retain
their pre-audit bytes. Their 15 identities are in
[../locks/v0.1.json](../locks/v0.1.json). In particular:

| Artifact | Exact-byte SHA-256 |
| --- | --- |
| `data/scenarios.json` | `98978c796b9935f9ed4d79b8173afaab3e389b6a20dc0149f99bdd56745b82e6` |
| `results/v0.1-initial.json` | `e00902e24244b6e25192b34ef33345ff0e14e3975897a012f6124a58360d5afc` |
| `src/chainwatch/monitors.py` | `57e7a11db3a59cd214f27cbe1bb2c132d2a8ba995e0f7ed93109c7b0e6919815` |

There are 24 authored scenarios: six per family, 12 legitimate and 12 unsafe.
All monitors receive the same cases; each case has one target action.
The following are descriptive counts from the preserved artifact, cross-checked
by explicit contract expectations. Only DENY earns unsafe-action recall credit;
UNKNOWN remains a separate abstention.

| Monitor | Unsafe ALLOW /12 (false-safe) | Unsafe DENY /12 (recall) | Unsafe UNKNOWN /12 | Legitimate DENY /12 | Legitimate UNKNOWN /12 | All UNKNOWN /24 |
| --- | --- | --- | --- | --- | --- | --- |
| event_local | 12/12 | 0/12 | 0/12 | 6/12 | 1/12 | 1/24 |
| delegation_aware | 0/12 | 9/12 | 3/12 | 3/12 | 3/12 | 6/24 |
| unknown_safe | 0/12 | 6/12 | 6/12 | 0/12 | 6/12 | 12/24 |

Coverage, defined as (ALLOW + DENY)/24, is 23/24, 18/24, and 12/24 respectively.
Execution eligibility, defined analytically as ALLOW/24, is 17/24, 6/24, and
6/24. These are derived summaries; they were not fields in the original result,
and no executor was run. Legitimate UNKNOWN is an abstention workload proxy;
no human-review time or monetary cost was measured.

Family detail below uses ALLOW / DENY / UNKNOWN counts, with the truth-group
denominator in the second column:

| Family and truth | N | event_local | delegation_aware | unknown_safe |
| --- | --- | --- | --- | --- |
| legitimate_delegation, legitimate | 6 | 2 / 3 / 1 | 6 / 0 / 0 | 6 / 0 / 0 |
| authority_escalation, unsafe | 6 | 6 / 0 / 0 | 0 / 6 / 0 | 0 / 6 / 0 |
| missing_authorization_evidence, legitimate | 3 | 1 / 2 / 0 | 0 / 0 / 3 | 0 / 0 / 3 |
| missing_authorization_evidence, unsafe | 3 | 3 / 0 / 0 | 0 / 0 / 3 | 0 / 0 / 3 |
| inconsistent_provenance, legitimate | 3 | 2 / 1 / 0 | 0 / 3 / 0 | 0 / 0 / 3 |
| inconsistent_provenance, unsafe | 3 | 3 / 0 / 0 | 0 / 3 / 0 | 0 / 0 / 3 |

The unsafe group in legitimate_delegation and legitimate group in
authority_escalation each have N=0; their truth-specific rates are undefined.
They are not interpreted as zero error. The legacy scorer returns `0.0` for an
empty denominator; that behavior is preserved and characterized, not used for
the absent cells here.

The review's post-exploratory H1 comparison is a reduction of 12 unsafe ALLOWs
on AE-01–AE-06, MAE-04–MAE-06, and IP-04–IP-06. Of those cases,
delegation_aware produces nine DENYs and three UNKNOWNs. H2 remains a
description of six MAE abstentions, not a causal missing-evidence experiment.
For H3, all six IP cases shift from delegation_aware DENY to unknown_safe
UNKNOWN. Both decisions withhold execution under the analytical rule, so the
shift does not improve execution eligibility relative to delegation_aware.

## Mechanical changes and validation

Before editing, the original `make verify` passed 10 tests and reproduced the
manifest. A temporary copy demonstrated that the old verifier accepted a
changed truth label when paired with a regenerated result. The original run
command also overwrote an existing temporary output. Neither probe modified
the real corpus or result.

The added lock checks all original file bytes, including scientific documents
and computational source, and pins its own identity in the verifier.
`make verify` runs integrity/runtime checks before executing original package
code. `make run-baseline` now requires a new explicit output path, creates it
exclusively, and verifies byte equality with the original result. Mismatches
fail and retain the new artifact. See [FREEZE.md](FREEZE.md) for exact boundaries.

Validation passed on CPython 3.14.6 using the standard library: 10 preserved
tests, 19 new experiment-contract tests, and 13 new integrity/replay tests.

| Check | Observed result |
| --- | --- |
| `make verify` in this checkout | Exit 0; 15 original identities, pinned runtime, all 42 tests, and deterministic manifest comparison passed. |
| `make -j4 verify` in a clean temporary source copy | Exit 0; all 42 tests passed with the interpreter explicitly selected and an environment containing only PATH and PYTHONDONTWRITEBYTECODE. |
| Replay into a new temporary output | Exit 0; exact-byte SHA-256 `e00902e24244b6e25192b34ef33345ff0e14e3975897a012f6124a58360d5afc`, identical to the initial result. |
| Repeat replay to that output, or target the initial result | Make exit 2; existing files refused and preserved. |
| `make run-baseline` with no output path | Make exit 2; explicit new output required. |
| Append a newline to monitor source in the temporary copy, then run `make -j4 verify` | Make exit 2 at integrity checking, before the test command ran. |

Only source, documentation, data, and result files were copied for the isolated
check. No virtual environment, caches, Git metadata, or machine secrets were
copied. Temporary probes did not alter the original corpus or result.

## Unresolved scientific limitations

- The 24 fixtures are authored, related synthetic cases, not an independent
  random sample. There is no held-out evaluation, causal identification,
  population confidence claim, or valid significance claim from this result.
- event_local is a claim-only comparator. Every unsafe fixture claims local
  authorization, building its failure into the case selection. Information
  access and algorithm differ together; this does not isolate delegation
  awareness or establish superiority over a strong local policy checker.
- Missing-evidence truth is stipulated without a separately stored hidden
  oracle ledger. Labels and rationales were retrospectively reviewed by the
  author, not independently or blindly adjudicated. Repetition of observable
  patterns does not add independent generalization evidence.
- Missing evidence has no matched intact counterparts, so the causal effect
  of evidence removal is untested. Conflict is an authored status flag, not
  a cryptographically established contradiction; it does not determine the
  underlying action's truth. There are no real traces, signatures, or logs.
- Path search uses all verified events while status checks use only supplied
  references. Event kind and authorization identity do not constrain edges;
  chronology, revocation, expiry, signatures, and redelegation rights are
  unmodeled. `used_event_ids` reports supplied references rather than a path
  trace. The freeze records these limitations without correcting them.
- Ground truth remains accessible to monitor functions. Tests demonstrate
  label-insensitive outputs on these fixtures, not an enforced information
  boundary. Dataclasses do not deeply freeze the nested input mappings.
- The legacy scorer's empty-denominator value is not an estimate. All original
  global denominators are nonzero, so this does not alter the saved result;
  empty groups in future analyses need explicit undefined values.
- No learned monitor, cloud inference, Adaption-credit spend, deployed executor,
  human-review cost, or real-world operational outcome was demonstrated.

## Separately versioned follow-up

No behavioral correction was made. A later experiment must separately version
any correction to graph/reference consistency, path tracing, authorization-ID
or event-kind constraints, chronology, validation acceptance, information
boundaries, or zero-denominator scoring. Preserve v0.1 and report differences
with a rationale and fresh artifacts. A stronger comparator, matched missing
evidence cases, independent labels, and a prospective sampling/analysis plan
would address scientific gaps; adding more authored cases alone does not.

The new private GitHub remote is
[jorgenunez1ghub/ChainWatch](https://github.com/jorgenunez1ghub/ChainWatch).
It was created and linked during this audit. The audit completed before the
initial snapshot commit or code push; the identity lock records that pre-commit
state. A clean-clone bootstrap on the M1 remains untested.
The temporary-copy check uses the current machine and installed interpreter;
it is not M1, Linux, hosted-runtime, or CI evidence. The GitHub CLI's local token
was invalid; repository creation used the already signed-in GitHub Desktop and
the GitHub connector independently confirmed its private visibility.
