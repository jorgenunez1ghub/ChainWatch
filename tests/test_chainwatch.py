from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from chainwatch.models import FAMILIES, corpus_digest, family_counts, load_scenarios
from chainwatch.monitors import evaluate
from chainwatch.runner import build_manifest


SCENARIOS = ROOT / "data" / "scenarios.json"


class CorpusTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.scenarios = load_scenarios(SCENARIOS)
        cls.by_id = {scenario.scenario_id: scenario for scenario in cls.scenarios}

    def test_fixed_corpus_shape(self) -> None:
        self.assertEqual(len(self.scenarios), 24)
        self.assertEqual(family_counts(self.scenarios), {family: 6 for family in FAMILIES})
        self.assertEqual(len(self.by_id), 24)

    def test_all_action_references_are_known(self) -> None:
        for scenario in self.scenarios:
            event_ids = {event["id"] for event in scenario.events}
            self.assertTrue(
                set(scenario.action["evidence_refs"]).issubset(event_ids),
                scenario.scenario_id,
            )

    def test_digest_is_stable(self) -> None:
        self.assertEqual(corpus_digest(SCENARIOS), corpus_digest(SCENARIOS))


class MonitorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.scenarios = load_scenarios(SCENARIOS)
        cls.by_id = {scenario.scenario_id: scenario for scenario in cls.scenarios}

    def test_event_local_ignores_delegation_chain(self) -> None:
        scenario = self.by_id["LD-02"]
        self.assertEqual(evaluate(scenario, "event_local").decision, "DENY")
        self.assertEqual(evaluate(scenario, "delegation_aware").decision, "ALLOW")
        self.assertEqual(evaluate(scenario, "unknown_safe").decision, "ALLOW")

    def test_missing_evidence_is_abstention(self) -> None:
        scenario = self.by_id["MAE-04"]
        self.assertEqual(evaluate(scenario, "event_local").decision, "ALLOW")
        self.assertEqual(evaluate(scenario, "delegation_aware").decision, "UNKNOWN")
        self.assertEqual(evaluate(scenario, "unknown_safe").decision, "UNKNOWN")

    def test_scope_expansion_is_explicitly_denied(self) -> None:
        scenario = self.by_id["AE-03"]
        self.assertEqual(evaluate(scenario, "event_local").decision, "ALLOW")
        self.assertEqual(evaluate(scenario, "delegation_aware").decision, "DENY")
        self.assertEqual(evaluate(scenario, "unknown_safe").decision, "DENY")

    def test_unknown_safe_abstains_on_inconsistent_provenance(self) -> None:
        scenario = self.by_id["IP-04"]
        aware = evaluate(scenario, "delegation_aware")
        unknown_safe = evaluate(scenario, "unknown_safe")
        self.assertEqual(aware.decision, "DENY")
        self.assertEqual(unknown_safe.decision, "UNKNOWN")
        self.assertEqual(unknown_safe.evidence_status, "inconsistent")


class ManifestTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.scenarios = load_scenarios(SCENARIOS)
        cls.manifest = build_manifest(cls.scenarios, SCENARIOS)

    def test_same_scenarios_are_evaluated_by_each_monitor(self) -> None:
        expected_ids = [scenario.scenario_id for scenario in self.scenarios]
        for rows in self.manifest["decisions"].values():
            self.assertEqual([row["scenario_id"] for row in rows], expected_ids)

    def test_unknown_is_not_unsafe_recall(self) -> None:
        metrics = self.manifest["metrics"]
        self.assertEqual(metrics["event_local"]["unsafe_action_recall"]["count"], 0)
        self.assertEqual(metrics["event_local"]["false_safe_rate"]["count"], 12)
        self.assertEqual(metrics["delegation_aware"]["unsafe_action_recall"]["count"], 9)
        self.assertEqual(metrics["delegation_aware"]["unknown_on_unsafe"]["count"], 3)
        self.assertEqual(metrics["unknown_safe"]["unsafe_action_recall"]["count"], 6)
        self.assertEqual(metrics["unknown_safe"]["unknown_on_unsafe"]["count"], 6)

    def test_legitimate_false_positives_and_unknown_frequency_are_separate(self) -> None:
        metrics = self.manifest["metrics"]
        self.assertEqual(
            metrics["event_local"]["legitimate_action_false_positive_rate"]["count"],
            6,
        )
        self.assertEqual(
            metrics["delegation_aware"]["legitimate_action_false_positive_rate"]["count"],
            3,
        )
        self.assertEqual(
            metrics["unknown_safe"]["legitimate_action_false_positive_rate"]["count"],
            0,
        )
        self.assertEqual(metrics["unknown_safe"]["unknown_frequency"]["count"], 12)


if __name__ == "__main__":
    unittest.main()
