# Scenario and event schema

The source of truth is data/scenarios.json. The top-level object contains:

- protocol_version: ChainWatch v0.1
- schema_version: chainwatch.scenario.v0.1
- scenarios: exactly 24 scenario objects

Each scenario has:

- id: stable unique identifier
- family: one of the four locked family names
- description: short human-readable case description
- events: ordered authorization events
- action: the action being monitored
- ground_truth: legitimate or unsafe

Each event has:

- id: stable identifier local to the scenario
- kind: grant or delegation
- source: actor granting or delegating authority
- delegate: actor receiving authority
- scope: list of operation names
- authorization_id: stable authorization record identifier, or null when the
  record is missing
- provenance.status: verified, missing, or inconsistent
- provenance.source and provenance.record_id when available

An action has:

- actor: actor attempting the operation
- operation: requested operation name
- local_authorization_claim: true, false, or null
- evidence_refs: event IDs claimed as the authorization chain

Evidence semantics are explicit:

- verified means the event has a stable authorization and provenance record.
- missing means the required record is absent; absence is not inferred to mean
  either safe or unsafe.
- inconsistent means available records conflict; it is not silently repaired
  or collapsed into a verified event.
