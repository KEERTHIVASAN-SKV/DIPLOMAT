"""
Settlement Agent — calculates the final payable amount from validated inputs.
"""
from agents.base_agent import BaseAgent


class SettlementAgent(BaseAgent):
    name = "SettlementAgent"

    def system_prompt(self) -> str:
        return """You are the Settlement Agent for an insurance company.
Calculate the exact payable amount using the validated inputs provided.

Return ONLY valid JSON with these exact fields:
{
  "claim_id": "string",
  "assessed_amount": number,
  "coverage_limit": number,
  "deductible": number,
  "copay_percentage": number,
  "copay_amount": number,
  "payable_amount": number,
  "currency": "INR",
  "status": "APPROVED|HUMAN_REVIEW|REJECTED",
  "calculation_breakdown": {
    "step1_eligible": number,
    "step2_after_deductible": number,
    "step3_after_copay": number,
    "step4_capped_at_limit": number
  },
  "notes": "string"
}

Calculation:
1. eligible = min(assessed_amount, coverage_limit)
2. after_deductible = eligible - deductible
3. copay_amount = after_deductible * (copay_percentage / 100)
4. payable = after_deductible - copay_amount"""

    def mock_process(self, input_data: dict) -> dict:
        assessed = float(input_data.get("assessed_amount", 0))
        limit = float(input_data.get("coverage_limit", assessed))
        deductible = float(input_data.get("deductible", 0))
        copay_pct = float(input_data.get("copay", 0))
        claim_id = input_data.get("claim_id", "")

        step1 = min(assessed, limit)
        step2 = max(0, step1 - deductible)
        copay_amount = round(step2 * copay_pct / 100, 2)
        step3 = round(step2 - copay_amount, 2)

        return {
            "claim_id": claim_id,
            "assessed_amount": assessed,
            "coverage_limit": limit,
            "deductible": deductible,
            "copay_percentage": copay_pct,
            "copay_amount": copay_amount,
            "payable_amount": step3,
            "currency": "INR",
            "status": "APPROVED",
            "calculation_breakdown": {
                "step1_eligible_amount": step1,
                "step2_after_deductible": step2,
                "step3_copay_amount": copay_amount,
                "step4_final_payable": step3,
            },
            "notes": "Settlement calculated from DIPLOMAT-validated inputs.",
        }
