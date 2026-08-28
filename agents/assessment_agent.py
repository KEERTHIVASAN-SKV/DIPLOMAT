"""
Assessment Agent — evaluates damage/loss and produces a financial assessment.
"""
from agents.base_agent import BaseAgent


class AssessmentAgent(BaseAgent):
    name = "AssessmentAgent"

    def system_prompt(self) -> str:
        return """You are the Assessment Agent for an insurance company.
Your job is to evaluate the damage/loss described in the claim and produce a financial assessment.

Return ONLY valid JSON with these exact fields:
{
  "claim_id": "string",
  "damage_items": [{"part": "string", "amount": number, "description": "string"}],
  "assessed_amount": number (MUST equal the exact sum of all damage_items amounts),
  "currency": "INR",
  "source": "ASSESSMENT_REPORT",
  "evidence_ids": ["list of document IDs"],
  "notes": "string"
}

CRITICAL: assessed_amount MUST be the exact arithmetic sum of all damage_items amounts.
Do NOT round differently. Do NOT add or remove items from the sum."""

    def mock_process(self, input_data: dict) -> dict:
        """Pass-through: demo scenarios include pre-built assessment data."""
        assessment = input_data.get("__assessment__", {})
        if assessment:
            # Inject claim_id from context
            assessment["claim_id"] = input_data.get("claim_id", assessment.get("claim_id", ""))
        return assessment if assessment else {
            "claim_id": input_data.get("claim_id", ""),
            "damage_items": [
                {"part": "bumper", "amount": 30000.0, "description": "Front bumper replacement"},
                {"part": "headlight", "amount": 20000.0, "description": "Left headlight"},
                {"part": "labor", "amount": 10000.0, "description": "Labor charges"},
            ],
            "assessed_amount": 60000.0,
            "currency": "INR",
            "source": "ASSESSMENT_REPORT",
            "evidence_ids": ["DOC-001", "PHOTO-002"],
            "notes": "Standard assessment",
        }
