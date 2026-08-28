"""
Insurance Pipeline Orchestrator
================================
Wires all 5 agents together with DIPLOMAT gateways between each pair.
"""
import os
from pathlib import Path
from typing import Optional

from agents.claim_agent import ClaimAgent
from agents.policy_agent import PolicyAgent
from agents.assessment_agent import AssessmentAgent
from agents.fraud_agent import FraudAgent
from agents.settlement_agent import SettlementAgent
from diplomat.gateway import DiplomatGateway
from models.diplomat_models import DiplomatResult, DiplomatStatus, HandoffRecord

CONTRACTS_DIR = Path(__file__).parent.parent / "contracts"


class PipelineResult:
    def __init__(self, claim_id: str):
        self.claim_id = claim_id
        self.final_status: str = "PENDING"   # APPROVED | REJECTED | HUMAN_REVIEW
        self.blocked_at: Optional[str] = None
        self.handoff_log: list[dict] = []
        self.agent_outputs: dict = {}
        self.final_output: Optional[dict] = None
        self.error: Optional[DiplomatResult] = None

    def to_dict(self) -> dict:
        return {
            "claim_id": self.claim_id,
            "final_status": self.final_status,
            "blocked_at": self.blocked_at,
            "handoff_log": self.handoff_log,
            "final_output": self.final_output,
        }


class InsurancePipeline:
    """
    Full multi-agent insurance claim pipeline with DIPLOMAT between each step.
    """

    def __init__(self):
        # Agents
        self.claim_agent = ClaimAgent()
        self.policy_agent = PolicyAgent()
        self.assessment_agent = AssessmentAgent()
        self.fraud_agent = FraudAgent()
        self.settlement_agent = SettlementAgent()

        # DIPLOMAT Gateways
        self.gw_claim_to_policy = DiplomatGateway(
            str(CONTRACTS_DIR / "claim_to_policy.json")
        )
        self.gw_policy_to_assessment = DiplomatGateway(
            str(CONTRACTS_DIR / "policy_to_assessment.json")
        )
        self.gw_assessment_to_fraud = DiplomatGateway(
            str(CONTRACTS_DIR / "assessment_to_fraud.json")
        )
        self.gw_fraud_to_settlement = DiplomatGateway(
            str(CONTRACTS_DIR / "fraud_to_settlement.json")
        )

    def run(self, raw_claim: dict, on_step=None) -> PipelineResult:
        """
        Process a claim through the full pipeline.

        Args:
            raw_claim: The raw claim dict (from test scenario or customer input).
            on_step: Optional callback(step_name, agent_output, diplomat_result) for UI.

        Returns:
            PipelineResult with full audit trail.
        """
        result = PipelineResult(raw_claim.get("claim_id", "UNKNOWN"))
        context: dict = {}   # Accumulates validated agent outputs

        def _log(step: str, payload: dict, dr: DiplomatResult):
            entry = {
                "step": step,
                "status": dr.status.value,
                "source_agent": dr.source_agent,
                "target_agent": dr.target_agent,
                "error_code": dr.error_code,
                "message": dr.message,
                "details": dr.details,
            }
            result.handoff_log.append(entry)
            if on_step:
                on_step(step, payload, dr)

        # ══════════════════════════════════════════════
        # STEP 1: Claim Agent
        # ══════════════════════════════════════════════
        claim_output = self.claim_agent.process(raw_claim)
        result.agent_outputs["ClaimAgent"] = claim_output

        dr = self.gw_claim_to_policy.validate(claim_output, context)
        _log("ClaimAgent → PolicyAgent", claim_output, dr)

        if dr.status == DiplomatStatus.REJECTED:
            result.final_status = "REJECTED"
            result.blocked_at = "ClaimAgent → PolicyAgent"
            result.error = dr
            return result

        if dr.status == DiplomatStatus.HUMAN_REVIEW:
            result.final_status = "HUMAN_REVIEW"
            result.blocked_at = "ClaimAgent → PolicyAgent"
            result.error = dr
            return result

        context["claim"] = claim_output

        # ══════════════════════════════════════════════
        # STEP 2: Policy Agent
        # ══════════════════════════════════════════════
        policy_input = {**claim_output}
        policy_output = self.policy_agent.process(policy_input)
        result.agent_outputs["PolicyAgent"] = policy_output

        dr = self.gw_policy_to_assessment.validate(policy_output, context)
        _log("PolicyAgent → AssessmentAgent", policy_output, dr)

        if dr.status == DiplomatStatus.REJECTED:
            result.final_status = "REJECTED"
            result.blocked_at = "PolicyAgent → AssessmentAgent"
            result.error = dr
            return result

        if dr.status == DiplomatStatus.HUMAN_REVIEW:
            result.final_status = "HUMAN_REVIEW"
            result.blocked_at = "PolicyAgent → AssessmentAgent"
            result.error = dr
            return result

        context["policy"] = policy_output

        # ══════════════════════════════════════════════
        # STEP 3: Assessment Agent
        # ══════════════════════════════════════════════
        assessment_input = {**claim_output, "__assessment__": raw_claim.get("__assessment__", {})}
        assessment_output = self.assessment_agent.process(assessment_input)
        result.agent_outputs["AssessmentAgent"] = assessment_output

        dr = self.gw_assessment_to_fraud.validate(assessment_output, context)
        _log("AssessmentAgent → FraudAgent", assessment_output, dr)

        if dr.status == DiplomatStatus.REJECTED:
            result.final_status = "REJECTED"
            result.blocked_at = "AssessmentAgent → FraudAgent"
            result.error = dr
            return result

        if dr.status == DiplomatStatus.HUMAN_REVIEW:
            result.final_status = "HUMAN_REVIEW"
            result.blocked_at = "AssessmentAgent → FraudAgent"
            result.error = dr
            return result

        context["assessment"] = assessment_output

        # ══════════════════════════════════════════════
        # STEP 4: Fraud Agent
        # ══════════════════════════════════════════════
        fraud_input = {**claim_output, "__fraud__": raw_claim.get("__fraud__", {})}
        fraud_output = self.fraud_agent.process(fraud_input)
        result.agent_outputs["FraudAgent"] = fraud_output

        dr = self.gw_fraud_to_settlement.validate(fraud_output, context)
        _log("FraudAgent → SettlementAgent", fraud_output, dr)

        if dr.status == DiplomatStatus.REJECTED:
            result.final_status = "REJECTED"
            result.blocked_at = "FraudAgent → SettlementAgent"
            result.error = dr
            return result

        if dr.status == DiplomatStatus.HUMAN_REVIEW:
            result.final_status = "HUMAN_REVIEW"
            result.blocked_at = "FraudAgent → SettlementAgent"
            result.error = dr
            return result

        context["fraud"] = fraud_output

        # ══════════════════════════════════════════════
        # STEP 5: Settlement Agent
        # ══════════════════════════════════════════════
        settlement_input = {
            "claim_id": claim_output["claim_id"],
            "assessed_amount": assessment_output["assessed_amount"],
            "coverage_limit": policy_output["coverage_limit"],
            "deductible": policy_output["deductible"],
            "copay": policy_output["copay"],
            "currency": policy_output["currency"],
        }
        settlement_output = self.settlement_agent.process(settlement_input)
        result.agent_outputs["SettlementAgent"] = settlement_output

        result.final_status = settlement_output.get("status", "APPROVED")
        result.final_output = settlement_output
        return result
