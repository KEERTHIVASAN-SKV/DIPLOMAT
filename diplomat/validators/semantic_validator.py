"""Check 4: Semantic Validation — fields that carry meaning must carry all their context."""
from models.diplomat_models import DiplomatResult, DiplomatStatus


def _get_nested(data: dict, dotted_key: str):
    keys = dotted_key.split(".")
    val = data
    for k in keys:
        if not isinstance(val, dict):
            return None
        val = val.get(k)
    return val


class SemanticValidator:
    def validate(self, payload: dict, contract: dict, context: dict) -> DiplomatResult | None:
        semantic_reqs = contract.get("semantic_requirements", {})
        errors = []

        for parent_field, required_companions in semantic_reqs.items():
            parent_val = _get_nested(payload, parent_field)
            if parent_val is None:
                continue  # Already handled by FieldValidator

            if isinstance(parent_val, dict):
                # nested object — all companions must be keys in the object
                missing_companions = [c for c in required_companions if c not in parent_val or parent_val[c] is None]
            else:
                # scalar — companions must exist as sibling fields in payload
                missing_companions = [c for c in required_companions if _get_nested(payload, c) is None]

            if missing_companions:
                errors.append({
                    "field": parent_field,
                    "error": "MISSING_SEMANTIC_CONTEXT",
                    "missing_companions": missing_companions,
                    "reason": f"'{parent_field}' carries financial meaning and requires {missing_companions} for unambiguous interpretation.",
                })

        if errors:
            return DiplomatResult(
                status=DiplomatStatus.REJECTED,
                source_agent=contract["source"],
                target_agent=contract["target"],
                error_code="SEMANTIC_CONTRACT_VIOLATION",
                message="Fields with financial meaning are missing required semantic context.",
                details={"semantic_errors": errors},
                action="CORRECT_AND_RETRY",
            )
        return None
