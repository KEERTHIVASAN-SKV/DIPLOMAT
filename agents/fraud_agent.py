"""
Fraud Agent — analyzes claim patterns and produces a structured risk assessment.
"""
from agents.base_agent import BaseAgent

# Simulated fraud history database
FRAUD_HISTORY = {
    "CLM-1001": [],
    "CLM-1002": [],
    "CLM-1003": [],
    "CLM-1004": [],
    "CLM-1005": [],
    "CLM-1006": ["CLM-0091", "CLM-0102"],  # Has history of claims
}


class FraudAgent(BaseAgent):
    name = "FraudAgent"

    def system_prompt(self) -> str:
        return """You are the Fraud and Risk Agent for an insurance company.
Your job is to analyze the claim for suspicious patterns and produce a structured risk assessment.

Return ONLY valid JSON with these exact fields:
{
  "claim_id": "string",
  "risk_level": "LOW|MEDIUM|HIGH",
  "risk_score": number (0.0 to 1.0),
  "reasons": ["list of risk reasons"],
  "evidence_ids": ["list of evidence document IDs"],
  "recommendation": "PROCEED|HUMAN_REVIEW|REJECT",
  "checked_against": ["list of previous claim IDs checked"]
}

Rules:
- If risk_level is HIGH or MEDIUM, you MUST provide reasons and evidence_ids.
- risk_score must match risk_level: LOW=0.0-0.4, MEDIUM=0.4-0.75, HIGH=0.75-1.0."""

    def mock_process(self, input_data: dict) -> dict:
        """Pass-through: demo scenarios include pre-built fraud data."""
        fraud_data = input_data.get("__fraud__", {})
        if fraud_data:
            fraud_data["claim_id"] = input_data.get("claim_id", fraud_data.get("claim_id", ""))
            return fraud_data

        claim_id = input_data.get("claim_id", "")
        previous = FRAUD_HISTORY.get(claim_id, [])

        if previous:
            return {
                "claim_id": claim_id,
                "risk_level": "HIGH",
                "risk_score": 0.85,
                "reasons": ["multiple_recent_claims", "frequency_anomaly"],
                "evidence_ids": previous,
                "recommendation": "HUMAN_REVIEW",
                "checked_against": previous,
            }
        return {
            "claim_id": claim_id,
            "risk_level": "LOW",
            "risk_score": 0.12,
            "reasons": [],
            "evidence_ids": ["FRAUD-CHECK-001"],
            "recommendation": "PROCEED",
            "checked_against": [],
        }
