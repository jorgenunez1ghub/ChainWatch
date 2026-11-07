# ChainWatch v0.1 — post-exploratory protocol lock

Recorded 2026-11-07. Status: documented, content-addressed lock after the initial
exploratory evaluation. This is not preregistration. The authors had seen the
initial results before this review. There is no starting commit SHA because the
repository remains an unborn branch; no commit or publication is implied.

## Question and unit of analysis

On the fixed 24 synthetic scenarios, how do the three specified deterministic
decision rules differ in unsafe ALLOW decisions, unsafe DENY decisions,
legitimate DENY decisions, and abstention when authority spans handoffs?

The broader motivation is whether delegation awareness reduces false-safe
decisions. This experiment measures behavior on authored fixtures, not a causal
effect isolated from baseline design or performance on a sampled population.
One scenario contains one target action and is the analysis unit. All monitors
evaluate each scenario; there is no training split, randomization, or inference.

## Hypotheses and decision criteria

These are post-exploratory expectations, not prospectively tested hypotheses.

- H1: delegation_aware has fewer unsafe ALLOW decisions than event_local on
  the 12 unsafe cases. Report the paired count difference and case IDs, with
  unsafe DENY and UNKNOWN counts alongside it. A lower ALLOW count alone does
  not establish better detection.
- H2: missing evidence produces uncertainty in chain monitoring. Describe
  UNKNOWN counts in MAE-01 through MAE-06. A causal claim that removing evidence
  increases false-safe risk is not testable here: there are no matched intact
  counterparts, and the chain monitors abstain on missing evidence.
- H3: unknown_safe shifts inconsistent-provenance decisions from DENY to
  UNKNOWN relative to delegation_aware. Compare the six IP cases. Under the
  rule that only ALLOW permits execution, this does not reduce execution
  eligibility relative to delegation_aware; both withhold execution there.

## Frozen scenario set and truth

Exactly six cases per family; 12 legitimate and 12 unsafe overall. LD has six
legitimate cases; AE has six unsafe cases; MAE and IP each have three of each.
All 24 IDs, rationales, and evidence states appear in GROUND_TRUTH.md.
Ground truth concerns underlying authority, never the desired monitor output.
UNKNOWN is a decision, not an authorization-truth label.

## Monitor contract and evidence semantics

- event_local reads only local_authorization_claim: true → ALLOW, false → DENY,
  null → UNKNOWN. This is a claim-only comparator, not a strong event-local
  policy checker. All unsafe fixtures assert true, so its failure is built
  into this authored corpus. Comparisons confound information and algorithm.
- delegation_aware checks referenced status flags first: inconsistent → DENY;
  otherwise missing → UNKNOWN. It searches all verified events for paths from
  root_operator to the actor; every child scope must be a subset of its parent.
  Any valid path permitting the operation → ALLOW; only expanded paths or a
  requested operation outside valid scopes → DENY; no path → UNKNOWN.
- unknown_safe is identical except inconsistent → UNKNOWN. Both chain monitors
  already support UNKNOWN for missing evidence. Neither is a lenient monitor.
- Missing means unavailable evidence, not proof of unauthorized behavior.
  Inconsistent means an authored conflict flag, not a cryptographically
  established contradiction. Conflict takes precedence over missing.
- Execution eligibility is defined analytically as decision == ALLOW for all
  monitors. DENY and UNKNOWN withhold execution. No executor is implemented.

Implementation limitations: kind and authorization_id do not constrain graph
edges; event chronology, revocation, expiry, signatures, and redelegation rights
are not modeled. Status checks use evidence_refs but path search uses all
verified events. Reported used_event_ids are supplied references, not a trace
of the selected path. Ground truth remains accessible to monitor functions
though unused. These limit conclusions; fixes require versioned follow-up.

## Metrics and reporting

Report raw counts and denominators before percentages, overall and by family.
For unsafe N=12: recall = DENY/12; false-safe = ALLOW/12; unsafe abstention =
UNKNOWN/12. These three rates sum to one. For legitimate N=12: false positives
= DENY/12; false abstentions = UNKNOWN/12; legitimate allowance = ALLOW/12.
Overall UNKNOWN frequency = UNKNOWN/24; coverage = (ALLOW+DENY)/24;
execution eligibility = ALLOW/24. Family denominators use that family's actual
truth counts; an empty denominator is undefined, never interpreted as success.

The preserved runner currently emits the four primary metrics and truth-specific
UNKNOWN rates. Coverage and execution eligibility are derived summaries, not
additional fields claimed to exist in the initial artifact. Evidence availability
is a fixture attribute: 12 fully verified, six missing, six inconsistent cases;
it is not an accuracy measure. Report legitimate abstention as workload proxy,
without inventing human-review time or cost.

No weighted aggregate score: cost weights lack an operational basis and could
hide tradeoffs. No significance tests or population confidence claims: cases
are authored, related, and not a random independent sample. A future sample of
100 cases alone would not guarantee significance or validity; a prospective
design needs sampling assumptions, effect sizes, and an appropriate analysis.

## Exclusion and change rules

Include all 24 cases for every monitor. Do not drop difficult cases, duplicates
in behavior, legitimate conflicts, or missing records after seeing results.
Malformed schema or execution failure invalidates that run and must be reported;
do not silently exclude a case or convert an exception into UNKNOWN. Preserve
the failed artifact separately. There are no planned exclusions in v0.1.

Any change to cases, labels, semantics, monitor logic, or scoring requires a new
version and a change rationale. Keep this initial result and corpus intact.
Corrections to documentation must disclose substantive reinterpretations.
Future claims need fresh artifacts with source identity and commands. A rerun
of v0.1 is replication of this exploratory result, not a held-out test.

## Preserved identities

SHA-256 of exact file bytes (distinct from the canonical JSON digest):

| File | SHA-256 |
| --- | --- |
| data/scenarios.json | 98978c796b9935f9ed4d79b8173afaab3e389b6a20dc0149f99bdd56745b82e6 |
| results/v0.1-initial.json | e00902e24244b6e25192b34ef33345ff0e14e3975897a012f6124a58360d5afc |
| src/chainwatch/monitors.py | 57e7a11db3a59cd214f27cbe1bb2c132d2a8ba995e0f7ed93109c7b0e6919815 |

Canonical corpus JSON digest in the initial manifest:
d0017d759b3f00867db8527e9fe9fd5bc70447933d007d8f154b7b864a41f2a7.
Verification: make verify. Its manifest comparison uses the same implementation;
it establishes deterministic reproduction, not independent scientific validation.
