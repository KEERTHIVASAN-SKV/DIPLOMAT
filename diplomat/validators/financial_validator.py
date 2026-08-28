"""Check 7: Financial Rules — deterministic constraints on financial values."""
from models.diplomat_models import DiplomatResult, DiplomatStatus
from datetime import datetime
import config


def _parse_date(s: str):
    try:
        return datetime.strptime(s, "%Y-%m-%d").date()
    except Exception:
        return None


class FinancialValidator:
    def validate(self, payload: dict, contract: dict, context: dict) -> DiplomatResult | None:
        errors = []
        source = contract["source"]

        # ── AssessmentAgent: assessed_amount must equal sum of damage_items ──
        if source == "AssessmentAgent":
            damage_items = payload.get("damage_items", [])
            assessed_amount = payload.get("assessed_amount")
            if damage_items and assessed_amount is not None:
                computed_sum = round(sum(item.get("amount", 0) for item in damage_items), 2)
                reported = round(float(assessed_amount), 2)
                if abs(computed_sum - reported) > 1.0:   # Allow ₹1 rounding tolerance
                    errors.append({
                        "check": "AMOUNT_CONFLICT",
                        "message": "Reported assessed_amount does not match sum of damage_items.",
                        "sum_of_items": computed_sum,
                        "reported_amount": reported,
                        "difference": abs(computed_sum - reported),
                    })

        # ── PolicyAgent: policy must cover the incident date ──
        if source == "PolicyAgent":
            policy_expiry = payload.get("policy_expiry")
            policy_start = payload.get("policy_start")
            claim_output = context.get("claim", {})
            incident_date_str = claim_output.get("incident_date")

            if incident_date_str and policy_expiry:
                incident_date = _parse_date(incident_date_str)
                expiry_date = _parse_date(policy_expiry)
                if incident_date and expiry_date and incident_date > expiry_date:
                    errors.append({
                        "check": "POLICY_VALIDITY_FAILURE",
                        "message": "Incident occurred after policy expiry date.",
                        "incident_date": incident_date_str,
                        "policy_expiry": policy_expiry,
                    })

            if incident_date_str and policy_start:
                incident_date = _parse_date(incident_date_str)
                start_date = _parse_date(policy_start)
                if incident_date and start_date and incident_date < start_date:
                    errors.append({
                        "check": "POLICY_NOT_YET_ACTIVE",
                        "message": "Incident occurred before policy start date.",
                        "incident_date": incident_date_str,
                        "policy_start": policy_start,
                    })

        # ── SettlementAgent: payable_amount constraints ──
        if source == "SettlementAgent":
            payable = payload.get("payable_amount", 0)
            coverage_limit = payload.get("coverage_limit", float("inf"))
            if payable < 0:
                errors.append({"check": "NEGATIVE_PAYOUT", "message": "payable_amount cannot be negative."})
            if payable > coverage_limit:
                errors.append({
                    "check": "EXCEEDS_COVERAGE_LIMIT",
                    "message": "payable_amount exceeds coverage_limit.",
                    "payable": payable,
                    "coverage_limit": coverage_limit,
                })

        # ── Currency rule (enforced for all agents) ──
        currency = payload.get("currency")
        if currency and currency.upper() != config.REQUIRED_CURRENCY:
            errors.append({
                "check": "WRONG_CURRENCY",
                "message": f"Currency must be {config.REQUIRED_CURRENCY}.",
                "expected": config.REQUIRED_CURRENCY,
                "received": currency,
            })
        # Check nested estimated_damage.currency
        est_damage = payload.get("estimated_damage", {})
        if isinstance(est_damage, dict):
            dmg_currency = est_damage.get("currency")
            if dmg_currency and dmg_currency.upper() != config.REQUIRED_CURRENCY:
                errors.append({
                    "check": "WRONG_CURRENCY",
                    "message": f"estimated_damage.currency must be {config.REQUIRED_CURRENCY}.",
                    "expected": config.REQUIRED_CURRENCY,
                    "received": dmg_currency,
                })

        if errors:
            return DiplomatResult(
                status=DiplomatStatus.REJECTED,
                source_agent=contract["source"],
                target_agent=contract["target"],
                error_code="FINANCIAL_RULE_VIOLATION",
                message="One or more financial rules were violated.",
                details={"financial_errors": errors},
                action="CORRECT_AND_RETRY",
            )
        return None
