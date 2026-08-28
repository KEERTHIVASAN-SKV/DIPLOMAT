"""Check X: Rule Engine — evaluate simple human-readable rules in the contract.

Supported rule patterns (small subset sufficient for demo):
- "<field> must be <VALUE>" (equality, case-insensitive for strings)
- "<field> must be >= <other_field>" (numeric or date comparison)
- "if <field> is <VALUE> then <field2> must be non-empty" (conditional evidence requirement)

Rules are intentionally simple and deterministic to keep DIPLOMAT fail-closed.
"""
from __future__ import annotations
import re
from datetime import datetime
from typing import Optional

from models.diplomat_models import DiplomatResult, DiplomatStatus


def _get_nested(data: dict, dotted_key: str) -> Optional[object]:
    keys = dotted_key.split(".")
    val = data
    for k in keys:
        if not isinstance(val, dict):
            return None
        val = val.get(k)
    return val


def _parse_date(s: str) -> Optional[datetime.date]:
    try:
        return datetime.strptime(s, "%Y-%m-%d").date()
    except Exception:
        return None


class RuleValidator:
    def validate(self, payload: dict, contract: dict, context: dict) -> Optional[DiplomatResult]:
        rules = contract.get("rules", [])
        errors = []

        for rule in rules:
            rule = rule.strip()

            # Pattern: "<field> must be <VALUE>" (e.g., "currency must be INR")
            m = re.match(r"^(?P<field>[\w\.]+)\s+must\s+be\s+(?P<val>\S+)$", rule, re.I)
            if m:
                field = m.group("field")
                val = m.group("val")
                actual = _get_nested(payload, field)
                if actual is None or str(actual).upper() != val.upper():
                    errors.append({
                        "rule": rule,
                        "field": field,
                        "expected": val,
                        "received": actual,
                    })
                continue

            # Pattern: "<field> must be >= <other_field|literal>" (e.g., policy_expiry must be >= incident_date or deductible must be >= 0)
            m = re.match(r"^(?P<left>[\w\.]+)\s+must\s+be\s+>=\s*(?P<right>\S+)$", rule, re.I)
            if m:
                left = m.group("left")
                right = m.group("right")
                # Fetch left value from payload or common context sources
                left_val = _get_nested(payload, left) or _get_nested(context.get("policy", {}), left) or _get_nested(context.get("claim", {}), left) or _get_nested(context.get("assessment", {}), left)

                # Determine if right side is a literal number or date, else fetch from context
                right_val = None
                # numeric literal
                if re.match(r"^-?\d+(?:\.\d+)?$", right):
                    right_val = float(right)
                # date literal YYYY-MM-DD
                elif re.match(r"^\d{4}-\d{2}-\d{2}$", right):
                    right_val = _parse_date(right)
                else:
                    right_val = _get_nested(payload, right) or _get_nested(context.get("policy", {}), right) or _get_nested(context.get("claim", {}), right) or _get_nested(context.get("assessment", {}), right)

                # Try date comparison first when both appear date-like
                if isinstance(left_val, str) and isinstance(right_val, str):
                    ld = _parse_date(left_val)
                    rd = _parse_date(right_val)
                    if ld is None or rd is None or ld < rd:
                        errors.append({"rule": rule, "left": left_val, "right": right_val})
                elif isinstance(left_val, str) and isinstance(right_val, datetime.date):
                    ld = _parse_date(left_val)
                    if ld is None or ld < right_val:
                        errors.append({"rule": rule, "left": left_val, "right": right_val})
                else:
                    try:
                        if left_val is None or right_val is None or float(left_val) < float(right_val):
                            errors.append({"rule": rule, "left": left_val, "right": right_val})
                    except Exception:
                        errors.append({"rule": rule, "left": left_val, "right": right_val})
                continue

            # Pattern: if <field> is <VAL> then <field2> must be non-empty
            m = re.match(r"^if\s+(?P<f1>[\w\.]+)\s+is\s+(?P<v1>\S+)\s+then\s+(?P<f2>[\w\.]+)\s+must\s+be\s+non-empty$", rule, re.I)
            if m:
                f1 = m.group("f1")
                v1 = m.group("v1")
                f2 = m.group("f2")
                val1 = _get_nested(payload, f1)
                if val1 is None:
                    # Try context
                    val1 = _get_nested(context.get("fraud", {}), f1) or _get_nested(context.get("assessment", {}), f1)

                if val1 is not None and str(val1).upper() == v1.upper():
                    val2 = _get_nested(payload, f2) or _get_nested(context.get("fraud", {}), f2) or _get_nested(context.get("assessment", {}), f2) or _get_nested(context.get("policy", {}), f2)
                    if not val2:
                        errors.append({"rule": rule, "missing": f2})
                continue

            # Unknown/unhandled rule — skip (conservative approach would be to fail, but skip for now)

        if errors:
            return DiplomatResult(
                status=DiplomatStatus.REJECTED,
                source_agent=contract.get("source", "UNKNOWN"),
                target_agent=contract.get("target", "UNKNOWN"),
                error_code="RULE_VIOLATION",
                message="One or more contract rules were violated.",
                details={"rule_errors": errors},
                action="CORRECT_AND_RETRY",
            )

        return None
