from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
from typing import Any, Mapping

PROTOCOL_VERSION = "ChainWatch v0.1"
SCHEMA_VERSION = "chainwatch.scenario.v0.1"
FAMILIES = (
    "legitimate_delegation",
    "authority_escalation",
    "missing_authorization_evidence",
    "inconsistent_provenance",
)
GROUND_TRUTHS = ("legitimate", "unsafe")
EVENT_KINDS = ("grant", "delegation")
PROVENANCE_STATUSES = ("verified", "missing", "inconsistent")
DECISIONS = ("ALLOW", "DENY", "UNKNOWN")


class CorpusError(ValueError):
    """Raised when the fixed scenario corpus violates its locked schema."""


def _mapping(value: Any, context: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise CorpusError(f"{context} must be an object")
    return value


def _string(value: Any, context: str) -> str:
    if not isinstance(value, str) or not value:
        raise CorpusError(f"{context} must be a non-empty string")
    return value


@dataclass(frozen=True)
class Scenario:
    scenario_id: str
    family: str
    description: str
    events: tuple[Mapping[str, Any], ...]
    action: Mapping[str, Any]
    ground_truth: str

    @classmethod
    def from_mapping(cls, raw: Mapping[str, Any]) -> Scenario:
        mapping = _mapping(raw, "scenario")
        scenario = cls(
            scenario_id=_string(mapping.get("id"), "scenario.id"),
            family=_string(mapping.get("family"), "scenario.family"),
            description=_string(mapping.get("description"), "scenario.description"),
            events=tuple(
                _mapping(event, "scenario.events[]") for event in mapping.get("events", [])
            ),
            action=_mapping(mapping.get("action"), "scenario.action"),
            ground_truth=_string(mapping.get("ground_truth"), "scenario.ground_truth"),
        )
        validate_scenario(scenario)
        return scenario


def validate_scenario(scenario: Scenario) -> None:
    if scenario.family not in FAMILIES:
        raise CorpusError(f"{scenario.scenario_id}: unknown family {scenario.family}")
    if scenario.ground_truth not in GROUND_TRUTHS:
        raise CorpusError(
            f"{scenario.scenario_id}: unknown ground truth {scenario.ground_truth}"
        )
    if not scenario.events:
        raise CorpusError(f"{scenario.scenario_id}: events must not be empty")

    event_ids: set[str] = set()
    for index, event in enumerate(scenario.events):
        context = f"{scenario.scenario_id}.events[{index}]"
        event_id = _string(event.get("id"), f"{context}.id")
        if event_id in event_ids:
            raise CorpusError(f"{scenario.scenario_id}: duplicate event id {event_id}")
        event_ids.add(event_id)

        kind = _string(event.get("kind"), f"{context}.kind")
        if kind not in EVENT_KINDS:
            raise CorpusError(f"{context}.kind must be grant or delegation")
        _string(event.get("source"), f"{context}.source")
        _string(event.get("delegate"), f"{context}.delegate")

        scope = event.get("scope")
        if not isinstance(scope, list) or any(
            not isinstance(operation, str) or not operation for operation in scope
        ):
            raise CorpusError(f"{context}.scope must be a list of operation names")

        authorization_id = event.get("authorization_id")
        if authorization_id is not None and (
            not isinstance(authorization_id, str) or not authorization_id
        ):
            raise CorpusError(f"{context}.authorization_id must be a string or null")

        provenance = _mapping(event.get("provenance"), f"{context}.provenance")
        status = _string(provenance.get("status"), f"{context}.provenance.status")
        if status not in PROVENANCE_STATUSES:
            raise CorpusError(
                f"{context}.provenance.status must be verified, missing, or inconsistent"
            )
        if status == "verified":
            if authorization_id is None:
                raise CorpusError(
                    f"{context}: verified evidence requires authorization_id"
                )
            _string(provenance.get("source"), f"{context}.provenance.source")
            _string(provenance.get("record_id"), f"{context}.provenance.record_id")
        if status == "missing" and authorization_id is not None:
            raise CorpusError(
                f"{context}: missing evidence must use a null authorization_id"
            )
        if status == "inconsistent":
            if authorization_id is None:
                raise CorpusError(
                    f"{context}: inconsistent evidence requires authorization_id"
                )
            _string(provenance.get("source"), f"{context}.provenance.source")
            _string(provenance.get("record_id"), f"{context}.provenance.record_id")

    action = scenario.action
    _string(action.get("actor"), f"{scenario.scenario_id}.action.actor")
    _string(action.get("operation"), f"{scenario.scenario_id}.action.operation")
    claim = action.get("local_authorization_claim")
    if claim is not None and not isinstance(claim, bool):
        raise CorpusError(
            f"{scenario.scenario_id}.action.local_authorization_claim must be boolean or null"
        )
    evidence_refs = action.get("evidence_refs")
    if not isinstance(evidence_refs, list) or any(
        not isinstance(reference, str) or not reference for reference in evidence_refs
    ):
        raise CorpusError(
            f"{scenario.scenario_id}.action.evidence_refs must be a list of event IDs"
        )
    if len(set(evidence_refs)) != len(evidence_refs):
        raise CorpusError(f"{scenario.scenario_id}: duplicate action evidence reference")
    missing_refs = set(evidence_refs) - event_ids
    if missing_refs:
        missing = ", ".join(sorted(missing_refs))
        raise CorpusError(
            f"{scenario.scenario_id}: action references unknown event IDs: {missing}"
        )


def validate_corpus(scenarios: list[Scenario]) -> None:
    if len(scenarios) != 24:
        raise CorpusError(f"fixed corpus must contain 24 scenarios, found {len(scenarios)}")
    ids = [scenario.scenario_id for scenario in scenarios]
    if len(set(ids)) != len(ids):
        raise CorpusError("fixed corpus contains duplicate scenario IDs")
    counts = {family: 0 for family in FAMILIES}
    for scenario in scenarios:
        validate_scenario(scenario)
        counts[scenario.family] += 1
    wrong_counts = {family: count for family, count in counts.items() if count != 6}
    if wrong_counts:
        formatted = ", ".join(
            f"{family}={count}" for family, count in wrong_counts.items()
        )
        raise CorpusError(f"each family must contain six scenarios: {formatted}")


def load_scenarios(path: str | Path) -> list[Scenario]:
    corpus_path = Path(path)
    try:
        document = json.loads(corpus_path.read_text(encoding="utf-8"))
    except OSError as error:
        raise CorpusError(f"cannot read corpus {corpus_path}: {error}") from error
    except json.JSONDecodeError as error:
        raise CorpusError(f"invalid JSON in corpus {corpus_path}: {error}") from error

    mapping = _mapping(document, "corpus")
    if mapping.get("protocol_version") != PROTOCOL_VERSION:
        raise CorpusError("corpus protocol_version does not match ChainWatch v0.1")
    if mapping.get("schema_version") != SCHEMA_VERSION:
        raise CorpusError("corpus schema_version does not match chainwatch.scenario.v0.1")
    raw_scenarios = mapping.get("scenarios")
    if not isinstance(raw_scenarios, list):
        raise CorpusError("corpus.scenarios must be a list")
    scenarios = [Scenario.from_mapping(raw) for raw in raw_scenarios]
    validate_corpus(scenarios)
    return scenarios


def corpus_digest(path: str | Path) -> str:
    document = json.loads(Path(path).read_text(encoding="utf-8"))
    canonical = json.dumps(
        document,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()


def family_counts(scenarios: list[Scenario]) -> dict[str, int]:
    return {
        family: sum(scenario.family == family for scenario in scenarios)
        for family in FAMILIES
    }
