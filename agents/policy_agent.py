"""
Policy Agent — looks up the policy and extracts coverage details.
"""
from agents.base_agent import BaseAgent

# Simulated policy database for demo
POLICY_DB = {
    "POL-1001": {
        "policy_id": "POL-1001",
        "policy_status": "ACTIVE",
        "coverage_type": "ACCIDENTAL_DAMAGE",
        "coverage_limit": 100000.0,
        "deductible": 5000.0,
        "copay": 0.0,
        "currency": "INR",
        "policy_start": "2025-01-01",
        "policy_expiry": "2027-01-01",
        "exclusions": ["drunk_driving", "racing"],
        "sub_limits": {},
        "source": "POLICY_DOCUMENT",
    },
    "POL-1002": {
        "policy_id": "POL-1002",
        "policy_status": "ACTIVE",
        "coverage_type": "HEALTH",
        "coverage_limit": 500000.0,
        "deductible": 10000.0,
        "copay": 10.0,
        "currency": "INR",
        "policy_start": "2025-06-01",
        "policy_expiry": "2027-06-01",
        "exclusions": ["cosmetic_surgery", "pre_existing_conditions"],
        "sub_limits": {"room_rent": 5000},
        "source": "POLICY_DOCUMENT",
    },
    "POL-1003": {
        "policy_id": "POL-1003",
        "policy_status": "EXPIRED",
        "coverage_type": "ACCIDENTAL_DAMAGE",
        "coverage_limit": 200000.0,
        "deductible": 10000.0,
        "copay": 0.0,
        "currency": "INR",
        "policy_start": "2025-01-01",
        "policy_expiry": "2026-08-15",  # Expired!
        "exclusions": [],
        "sub_limits": {},
        "source": "POLICY_DOCUMENT",
    },
}


class PolicyAgent(BaseAgent):
    name = "PolicyAgent"

    def system_prompt(self) -> str:
        return """You are the Policy Agent for an insurance company.
Your job is to look up the policy document and extract coverage details.

Return ONLY valid JSON with these exact fields:
{
  "policy_id": "string",
  "policy_status": "ACTIVE|EXPIRED|CANCELLED|SUSPENDED|LAPSED",
  "coverage_type": "string",
  "coverage_limit": number,
  "deductible": number,
  "copay": number (0-100, percentage),
  "currency": "ISO-4217",
  "policy_start": "YYYY-MM-DD",
  "policy_expiry": "YYYY-MM-DD",
  "exclusions": ["list"],
  "sub_limits": {},
  "source": "POLICY_DOCUMENT"
}"""

    def mock_process(self, input_data: dict) -> dict:
        policy_id = input_data.get("policy_id", "")
        # Allow override for demo scenarios that inject bad policy data
        if "__policy_override__" in input_data:
            override = input_data["__policy_override__"]
            base = POLICY_DB.get(policy_id, POLICY_DB["POL-1001"]).copy()
            base.update(override)
            return base
        return POLICY_DB.get(policy_id, POLICY_DB["POL-1001"]).copy()
