"""
DIPLOMAT Gateway
================
The fail-closed trust layer between insurance AI agents.
Every agent handoff must pass through here before the next agent receives data.
"""
import json
import os
from pathlib import Path
from typing import Optional

from models.diplomat_models import DiplomatResult, DiplomatStatus, HandoffRecord
from diplomat.validators.field_validator import FieldValidator
from diplomat.validators.type_validator import TypeValidator
from diplomat.validators.format_validator import FormatValidator
from diplomat.validators.semantic_validator import SemanticValidator
from diplomat.validators.consistency_validator import ConsistencyValidator
from diplomat.validators.evidence_validator import EvidenceValidator
from diplomat.validators.financial_validator import FinancialValidator
from diplomat.validators.rule_validator import RuleValidator
import config


class DiplomatGateway:
    """
    Validates a data payload from one agent before it is allowed
    to reach the next agent.

    FAIL CLOSED: if any check fails, the handoff is immediately blocked
    and a structured rejection is returned. No information crosses unless
    all 7 checks pass.
    """

    def __init__(self, contract_path: str):
        with open(contract_path, "r", encoding="utf-8") as f:
            self.contract = json.load(f)

        self._validators = [
            ("Check 1 — Required Fields",      FieldValidator()),
            ("Check 2 — Data Types",            TypeValidator()),
            ("Check 3 — Formats",               FormatValidator()),
            ("Check X — Contract Rules",        RuleValidator()),
            ("Check 4 — Semantic Meaning",      SemanticValidator()),
            ("Check 5 — Cross-Agent Consistency", ConsistencyValidator()),
            ("Check 6 — Evidence",              EvidenceValidator()),
            ("Check 7 — Financial Rules",       FinancialValidator()),
        ]

    def validate(
        self,
        payload: dict,
        context: dict = None,
    ) -> DiplomatResult:
        """
        Run all 7 checks. Returns PASS only if every check passes.
        Fails closed on the first violation.

        Args:
            payload:  The agent's output dict to validate.
            context:  Dict of previous agent outputs keyed by agent name
                      (e.g., {"claim": {...}, "policy": {...}}).
        Returns:
            DiplomatResult with status PASS | REJECTED | HUMAN_REVIEW
        """
        if context is None:
            context = {}

        for check_name, validator in self._validators:
            result: Optional[DiplomatResult] = validator.validate(payload, self.contract, context)
            if result is not None:
                result.details["failed_check"] = check_name
                return result

        # All checks passed — final human-review escalation checks
        return self._check_escalation(payload, context)

    def _check_escalation(self, payload: dict, context: dict) -> DiplomatResult:
        """Post-validation escalation: high value or high risk → HUMAN_REVIEW."""
        source = self.contract["source"]
        target = self.contract["target"]

        # High fraud risk
        risk_score = payload.get("risk_score")
        if risk_score is not None and float(risk_score) >= config.HIGH_RISK_SCORE_THRESHOLD:
            return DiplomatResult(
                status=DiplomatStatus.HUMAN_REVIEW,
                source_agent=source,
                target_agent=target,
                error_code="HIGH_FRAUD_RISK",
                message=f"Risk score {risk_score:.2f} exceeds autonomous approval threshold ({config.HIGH_RISK_SCORE_THRESHOLD}). Escalating to human.",
                details={"risk_score": risk_score, "threshold": config.HIGH_RISK_SCORE_THRESHOLD},
                action="HUMAN_REVIEW",
            )

        recommendation = payload.get("recommendation")
        if recommendation == "HUMAN_REVIEW":
            return DiplomatResult(
                status=DiplomatStatus.HUMAN_REVIEW,
                source_agent=source,
                target_agent=target,
                error_code="AGENT_REQUESTED_REVIEW",
                message="Fraud agent recommended human review.",
                details={"recommendation": recommendation},
                action="HUMAN_REVIEW",
            )

        # High-value claim from Claim Agent
        est_damage = payload.get("estimated_damage", {})
        if isinstance(est_damage, dict):
            amount = est_damage.get("amount", 0)
            if float(amount) >= config.HIGH_VALUE_THRESHOLD:
                return DiplomatResult(
                    status=DiplomatStatus.HUMAN_REVIEW,
                    source_agent=source,
                    target_agent=target,
                    error_code="HIGH_VALUE_CLAIM",
                    message=f"Claim amount ₹{amount:,.0f} exceeds autonomous approval threshold. Escalating to human.",
                    details={"amount": amount, "threshold": config.HIGH_VALUE_THRESHOLD},
                    action="HUMAN_REVIEW",
                )

        return DiplomatResult(
            status=DiplomatStatus.PASS,
            source_agent=source,
            target_agent=target,
            message="All DIPLOMAT checks passed. Handoff approved.",
            action="CONTINUE",
        )

    @property
    def contract_id(self) -> str:
        return self.contract.get("contract_id", "UNKNOWN")
