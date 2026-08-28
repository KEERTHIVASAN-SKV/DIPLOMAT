"""Check 2: Data Type Validation."""
import re
from models.diplomat_models import DiplomatResult, DiplomatStatus


def _get_nested(data: dict, dotted_key: str):
    keys = dotted_key.split(".")
    val = data
    for k in keys:
        if not isinstance(val, dict):
            return None
        val = val.get(k)
    return val


class TypeValidator:
    TYPE_MAP = {
        "string": str,
        "number": (int, float),
        "boolean": bool,
        "array": list,
        "dict": dict,
    }

    def validate(self, payload: dict, contract: dict, context: dict) -> DiplomatResult | None:
        required = contract.get("required_fields", {})
        errors = []

        for field, type_spec in required.items():
            val = _get_nested(payload, field)
            if val is None:
                continue  # Already caught by FieldValidator

            base_type = type_spec.split(":")[0]
            expected_type = self.TYPE_MAP.get(base_type)

            if expected_type is None:
                continue  # Unknown type spec, skip

            if not isinstance(val, expected_type):
                errors.append({
                    "field": field,
                    "expected": base_type,
                    "received": type(val).__name__,
                    "value": str(val)[:100],
                })

        if errors:
            return DiplomatResult(
                status=DiplomatStatus.REJECTED,
                source_agent=contract["source"],
                target_agent=contract["target"],
                error_code="TYPE_VIOLATION",
                message="One or more fields have incorrect data types.",
                details={"type_errors": errors},
                action="CORRECT_AND_RETRY",
            )
        return None
