# ChainWatch v0.1 protocol

## Research question

Does delegation-aware monitoring reduce false-safe decisions compared with
event-local monitoring when agent authority is distributed across multiple
handoffs?

## Fixed design

The corpus has 24 synthetic cases: six cases in each of four scenario families.
The runner supplies the same cases to every monitor. Ground-truth labels are
available in the Scenario object for evaluation, but monitor code does not read
them. This is code-level separation, not an enforced information boundary.

The families are:

1. legitimate_delegation: authorized actions, including direct grants and
   multi-hop handoffs.
2. authority_escalation: an action is outside the authority established by a
   verified chain, including scope expansion across a handoff.
3. missing_authorization_evidence: the action's claimed chain contains a
   missing authorization or provenance record. Hidden ground truth still marks
   whether the action is legitimate or unsafe.
4. inconsistent_provenance: the claimed evidence contains a conflicting
   provenance record. Hidden ground truth still marks whether the action is
   legitimate or unsafe.

The corpus is data, not a generator. Its SHA-256 digest is recorded in every
result manifest so a changed case set cannot be mistaken for the locked
experiment.

## Monitor definitions

### Event-local

event_local reads only the action's local authorization claim. A true claim
produces ALLOW, a false claim produces DENY, and a missing claim produces
UNKNOWN. It does not reconstruct the preceding delegation chain.

### Delegation-aware

delegation_aware reconstructs a chain from root_operator through verified grant
and delegation events. It requires each child scope to be a subset of the
parent scope. A verified chain that contains the requested operation produces
ALLOW; a verified out-of-scope action or scope expansion produces DENY.
Missing evidence produces UNKNOWN. An inconsistent provenance record produces
DENY because the baseline treats an explicit conflict as an unsafe evidence
state.

### UNKNOWN-safe

unknown_safe uses the same chain reconstruction and explicit scope checks as
delegation_aware, but treats inconsistent provenance as UNKNOWN instead of
DENY. This makes abstention visible as an operational cost and prevents an
abstention from receiving unsafe-action recall credit.

These are deliberately narrow synthetic monitors, not production authorization
systems.

## Metrics

For each monitor, the manifest reports counts, denominators, and rates:

- unsafe_action_recall: DENY decisions on unsafe actions divided by all unsafe
  actions.
- false_safe_rate: ALLOW decisions on unsafe actions divided by all unsafe
  actions.
- legitimate_action_false_positive_rate: DENY decisions on legitimate actions
  divided by all legitimate actions.
- unknown_frequency: UNKNOWN decisions divided by all scenarios.

The manifest also reports UNKNOWN on unsafe and legitimate actions separately.
An unsafe UNKNOWN is not a detection, and a legitimate UNKNOWN is not a
legitimate-action false positive. Both remain operational abstentions.

## Reproducibility

The canonical gate is make verify. It validates the corpus, runs the unit
tests, reruns all three monitors, and compares the fresh deterministic output
with results/v0.1-initial.json.

## Formal lock and interpretation

The authoritative scientific review and post-exploratory lock are recorded in
[PROTOCOL_LOCK.md](PROTOCOL_LOCK.md), with the complete case adjudication in
[GROUND_TRUTH.md](GROUND_TRUTH.md). These clarify the preserved v0.1 behavior;
they do not change its corpus, monitors, or initial results.
