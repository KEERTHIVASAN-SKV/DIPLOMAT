"""Check 1: Required Fields — all required fields must be present and not null."""
from models.diplomat_models import DiplomatResult, DiplomatStatus


def _get_nested(data: dict, dotted_key: str):
    keys = dotted_key.split(".")
    val = data
    for k in keys:
        if not isinstance(val, dict):
            return None
        val = val.get(k)
        if val is None:
            return None
    return val


class FieldValidator:
    def validate(self, payload: dict, contract: dict, context: dict) -> DiplomatResult | None:
        required = contract.get("required_fields", {})
        missing = []
        for field in required:
            val = _get_nested(payload, field)
            if val is None or val == "":
                missing.append(field)

        if missing:
            return DiplomatResult(
                status=DiplomatStatus.REJECTED,
                source_agent=contract["source"],
                target_agent=contract["target"],
                error_code="MISSING_REQUIRED_FIELDS",
                message=f"Required fields are missing or null.",
                details={"missing_fields": missing},
                action="CORRECT_AND_RETRY",
            )
        return None
