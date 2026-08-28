"""Check 3: Format Validation — dates, enums, currency codes, percentages."""
import re
from models.diplomat_models import DiplomatResult, DiplomatStatus

DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
ISO_CURRENCIES = {"INR", "USD", "EUR", "GBP", "JPY", "AUD", "CAD", "CHF", "SGD", "AED"}


def _get_nested(data: dict, dotted_key: str):
    keys = dotted_key.split(".")
    val = data
    for k in keys:
        if not isinstance(val, dict):
            return None
        val = val.get(k)
    return val


class FormatValidator:
    def validate(self, payload: dict, contract: dict, context: dict) -> DiplomatResult | None:
        required = contract.get("required_fields", {})
        errors = []

        for field, type_spec in required.items():
            val = _get_nested(payload, field)
            if val is None:
                continue

            parts = type_spec.split(":")
            base = parts[0]
            constraint = parts[1] if len(parts) > 1 else ""

            if base == "date":
                if not isinstance(val, str) or not DATE_RE.match(val):
                    errors.append({
                        "field": field,
                        "error": "INVALID_DATE_FORMAT",
                        "expected": "YYYY-MM-DD",
                        "received": str(val)[:30],
                    })

            elif base == "enum":
                allowed = [x.strip() for x in constraint.split(",")]
                if val not in allowed:
                    errors.append({
                        "field": field,
                        "error": "INVALID_ENUM_VALUE",
                        "expected_one_of": allowed,
                        "received": str(val)[:50],
                    })

            elif base == "currency":
                if not isinstance(val, str) or val.upper() not in ISO_CURRENCIES:
                    errors.append({
                        "field": field,
                        "error": "INVALID_CURRENCY_CODE",
                        "expected": "ISO-4217 code e.g. INR",
                        "received": str(val)[:10],
                    })

            elif base == "number" and constraint == "percentage":
                if isinstance(val, (int, float)) and not (0 <= val <= 100):
                    errors.append({
                        "field": field,
                        "error": "OUT_OF_RANGE",
                        "expected": "0 to 100",
                        "received": val,
                    })

            elif base == "number" and constraint == "probability":
                if isinstance(val, (int, float)) and not (0.0 <= val <= 1.0):
                    errors.append({
                        "field": field,
                        "error": "OUT_OF_RANGE",
                        "expected": "0.0 to 1.0",
                        "received": val,
                    })

            elif base == "number" and constraint == "positive":
                if isinstance(val, (int, float)) and val <= 0:
                    errors.append({
                        "field": field,
                        "error": "NOT_POSITIVE",
                        "expected": "> 0",
                        "received": val,
                    })

            elif base == "number" and constraint == "non-negative":
                if isinstance(val, (int, float)) and val < 0:
                    errors.append({
                        "field": field,
                        "error": "NEGATIVE_VALUE",
                        "expected": ">= 0",
                        "received": val,
                    })

            elif base == "array" and constraint == "non-empty":
                if isinstance(val, list) and len(val) == 0:
                    errors.append({
                        "field": field,
                        "error": "EMPTY_ARRAY",
                        "expected": "at least 1 item",
                        "received": "[]",
                    })

        if errors:
            return DiplomatResult(
                status=DiplomatStatus.REJECTED,
                source_agent=contract["source"],
                target_agent=contract["target"],
                error_code="FORMAT_VIOLATION",
                message="One or more fields have invalid formats.",
                details={"format_errors": errors},
                action="CORRECT_AND_RETRY",
            )
        return None
