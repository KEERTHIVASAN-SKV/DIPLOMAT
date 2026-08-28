"""
Claim Agent — reads the raw claim form and extracts structured claim information.
"""
from agents.base_agent import BaseAgent


class ClaimAgent(BaseAgent):
    name = "ClaimAgent"

    def system_prompt(self) -> str:
        return """You are the Claim Agent for an insurance company.
Your job is to read a raw insurance claim and extract structured information.

Return ONLY valid JSON with these exact fields:
{
  "claim_id": "string",
  "policy_id": "string",
  "incident_date": "YYYY-MM-DD",
  "incident_type": "one of: ACCIDENT, THEFT, FIRE, HEALTH, FLOOD, NATURAL_DISASTER",
  "incident_description": "string",
  "claimant_name": "string",
  "estimated_damage": {
    "amount": number,
    "currency": "ISO-4217 code"
  },
  "supporting_documents": ["list of document names"]
}

Rules:
- Never guess missing values. Use null if a field is absent.
- Always use YYYY-MM-DD for dates.
- Always use ISO-4217 currency codes (e.g. INR).
- incident_type must be one of the allowed enum values."""

    def mock_process(self, input_data: dict) -> dict:
        """Return the raw claim data as-is (it is already structured in demo scenarios)."""
        return input_data
