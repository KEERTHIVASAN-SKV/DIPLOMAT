import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from orchestrator.pipeline import InsurancePipeline

SCENARIOS = {
    "valid_medical": ("claim_07_medical_valid.json", "APPROVED"),
    "expired_policy_medical": ("claim_08_medical_expired_policy.json", "REJECTED"),
    "missing_currency_medical": ("claim_09_medical_missing_currency.json", "REJECTED"),
    "high_risk_medical": ("claim_10_medical_high_risk_review.json", "HUMAN_REVIEW"),
}


class MedicalClaimPipelineTest(unittest.TestCase):
    def test_medical_claim_scenarios(self):
        for scenario_name, (file_name, expected_status) in SCENARIOS.items():
            claim_path = ROOT / "test_claims" / file_name
            self.assertTrue(claim_path.exists(), f"Expected demo claim at {claim_path}")

            with claim_path.open("r", encoding="utf-8") as f:
                raw_claim = json.load(f)

            result = InsurancePipeline().run(raw_claim)
            self.assertEqual(
                result.final_status,
                expected_status,
                f"Scenario {scenario_name} failed: {result.error.message if result.error else result.handoff_log}",
            )


if __name__ == "__main__":
    unittest.main()
