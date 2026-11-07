from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from .models import DECISIONS, Scenario

ROOT_ACTOR = "root_operator"
MONITOR_NAMES = ("event_local", "delegation_aware", "unknown_safe")


@dataclass(frozen=True)
class Decision:
    monitor: str
    scenario_id: str
    decision: str
    reason: str
    evidence_status: str
    used_event_ids: tuple[str, ...]

    def __post_init__(self) -> None:
        if self.decision not in DECISIONS:
            raise ValueError(f"unsupported decision {self.decision}")

    def as_mapping(self) -> dict[str, Any]:
        return {
            "scenario_id": self.scenario_id,
            "decision": self.decision,
            "evidence": {
                "status": self.evidence_status,
                "reason": self.reason,
                "used_event_ids": list(self.used_event_ids),
            },
        }


@dataclass(frozen=True)
class _ChainPath:
    event_ids: tuple[str, ...]
    final_scope: frozenset[str]
    scope_violation: bool


def _local_decision(scenario: Scenario) -> Decision:
    claim = scenario.action["local_authorization_claim"]
    if claim is True:
        decision = "ALLOW"
        reason = "local_authorization_claim_true"
        status = "local_claim"
    elif claim is False:
        decision = "DENY"
        reason = "local_authorization_claim_false"
        status = "local_claim"
    else:
        decision = "UNKNOWN"
        reason = "local_authorization_claim_missing"
        status = "missing"
    return Decision(
        monitor="event_local",
        scenario_id=scenario.scenario_id,
        decision=decision,
        reason=reason,
        evidence_status=status,
        used_event_ids=(),
    )


def _verified_paths(scenario: Scenario, actor: str) -> list[_ChainPath]:
    adjacency: dict[str, list[Mapping[str, Any]]] = {}
    for event in scenario.events:
        provenance = event["provenance"]
        if provenance["status"] != "verified":
            continue
        adjacency.setdefault(event["source"], []).append(event)

    paths: list[_ChainPath] = []

    def walk(
        source: str,
        inherited_scope: frozenset[str] | None,
        event_ids: tuple[str, ...],
        scope_violation: bool,
        visited: frozenset[str],
    ) -> None:
        if source == actor:
            paths.append(
                _ChainPath(
                    event_ids=event_ids,
                    final_scope=inherited_scope or frozenset(),
                    scope_violation=scope_violation,
                )
            )
            return
        for event in adjacency.get(source, []):
            event_id = event["id"]
            if event_id in visited:
                continue
            event_scope = frozenset(event["scope"])
            violates_scope = (
                inherited_scope is not None
                and not event_scope.issubset(inherited_scope)
            )
            walk(
                event["delegate"],
                event_scope,
                event_ids + (event_id,),
                scope_violation or violates_scope,
                visited | {event_id},
            )

    walk(ROOT_ACTOR, None, (), False, frozenset())
    return paths


def _delegation_decision(scenario: Scenario, unknown_safe: bool) -> Decision:
    evidence_refs = tuple(scenario.action["evidence_refs"])
    events_by_id = {event["id"]: event for event in scenario.events}
    statuses = [events_by_id[event_id]["provenance"]["status"] for event_id in evidence_refs]

    if "inconsistent" in statuses:
        return Decision(
            monitor="unknown_safe" if unknown_safe else "delegation_aware",
            scenario_id=scenario.scenario_id,
            decision="UNKNOWN" if unknown_safe else "DENY",
            reason="inconsistent_provenance",
            evidence_status="inconsistent",
            used_event_ids=evidence_refs,
        )
    if "missing" in statuses:
        return Decision(
            monitor="unknown_safe" if unknown_safe else "delegation_aware",
            scenario_id=scenario.scenario_id,
            decision="UNKNOWN",
            reason="missing_authorization_evidence",
            evidence_status="missing",
            used_event_ids=evidence_refs,
        )

    paths = _verified_paths(scenario, scenario.action["actor"])
    if not paths:
        return Decision(
            monitor="unknown_safe" if unknown_safe else "delegation_aware",
            scenario_id=scenario.scenario_id,
            decision="UNKNOWN",
            reason="authorization_chain_not_reconstructed",
            evidence_status="missing",
            used_event_ids=evidence_refs,
        )

    valid_paths = [path for path in paths if not path.scope_violation]
    operation = scenario.action["operation"]
    if not valid_paths:
        return Decision(
            monitor="unknown_safe" if unknown_safe else "delegation_aware",
            scenario_id=scenario.scenario_id,
            decision="DENY",
            reason="authority_scope_expansion",
            evidence_status="verified",
            used_event_ids=evidence_refs,
        )
    if any(operation in path.final_scope for path in valid_paths):
        return Decision(
            monitor="unknown_safe" if unknown_safe else "delegation_aware",
            scenario_id=scenario.scenario_id,
            decision="ALLOW",
            reason="verified_delegation_chain",
            evidence_status="verified",
            used_event_ids=evidence_refs,
        )
    return Decision(
        monitor="unknown_safe" if unknown_safe else "delegation_aware",
        scenario_id=scenario.scenario_id,
        decision="DENY",
        reason="operation_outside_delegated_scope",
        evidence_status="verified",
        used_event_ids=evidence_refs,
    )


def evaluate(scenario: Scenario, monitor: str) -> Decision:
    if monitor == "event_local":
        return _local_decision(scenario)
    if monitor == "delegation_aware":
        return _delegation_decision(scenario, unknown_safe=False)
    if monitor == "unknown_safe":
        return _delegation_decision(scenario, unknown_safe=True)
    raise ValueError(f"unsupported monitor {monitor}")
