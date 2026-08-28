"""Check 6: Evidence Validation — risk/fraud decisions must be backed by structured evidence."""
from models.diplomat_models import DiplomatResult, DiplomatStatus


class EvidenceValidator:
    def validate(self, payload: dict, contract: dict, context: dict) -> DiplomatResult | None:
        errors = []

        # Rule: if risk_level is HIGH or MEDIUM, evidence_ids and reasons must be non-empty
        risk_level = payload.get("risk_level")
        if risk_level in ("HIGH", "MEDIUM"):
            evidence_ids = payload.get("evidence_ids", [])
            reasons = payload.get("reasons", [])

            if not evidence_ids:
                errors.append({
                    "field": "evidence_ids",
                    "error": "UNSUPPORTED_RISK_DECISION",
                    "reason": f"risk_level={risk_level} requires at least one evidence_id",
                })
            if not reasons:
                errors.append({
                    "field": "reasons",
                    "error": "UNSUPPORTED_RISK_DECISION",
                    "reason": f"risk_level={risk_level} requires at least one reason",
                })

        # Rule: if recommendation is REJECT, reasons must be non-empty
        recommendation = payload.get("recommendation")
        if recommendation == "REJECT":
            reasons = payload.get("reasons", [])
            if not reasons:
                errors.append({
                    "field": "reasons",
                    "error": "UNSUPPORTED_REJECT_DECISION",
                    "reason": "recommendation=REJECT requires at least one reason",
                })

        if errors:
            return DiplomatResult(
                status=DiplomatStatus.REJECTED,
                source_agent=contract["source"],
                target_agent=contract["target"],
                error_code="INSUFFICIENT_EVIDENCE",
                message="Risk/fraud decision is not backed by required evidence.",
                details={"evidence_errors": errors},
                action="CORRECT_AND_RETRY",
            )
        return None
