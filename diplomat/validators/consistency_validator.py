"""Check 5: Cross-Agent Consistency — values must not conflict with previous agent outputs."""
from models.diplomat_models import DiplomatResult, DiplomatStatus


class ConsistencyValidator:
    # Fields that must remain consistent across agents
    CONSISTENCY_RULES = [
        {
            "field": "currency",
            "context_sources": ["claim", "policy", "assessment"],
            "description": "Currency must match across all agents",
        },
        {
            "field": "claim_id",
            "context_sources": ["claim", "assessment", "fraud"],
            "description": "Claim ID must remain consistent",
        },
        {
            "field": "policy_id",
            "context_sources": ["claim", "policy"],
            "description": "Policy ID must remain consistent",
        },
    ]

    def validate(self, payload: dict, contract: dict, context: dict) -> DiplomatResult | None:
        conflicts = []

        for rule in self.CONSISTENCY_RULES:
            field = rule["field"]
            current_val = payload.get(field)
            if current_val is None:
                continue

            for source_key in rule["context_sources"]:
                prev_output = context.get(source_key, {})
                prev_val = prev_output.get(field)
                if prev_val is not None and str(prev_val).upper() != str(current_val).upper():
                    conflicts.append({
                        "field": field,
                        "current_value": current_val,
                        "conflicting_source": source_key,
                        "conflicting_value": prev_val,
                        "description": rule["description"],
                    })

        if conflicts:
            return DiplomatResult(
                status=DiplomatStatus.REJECTED,
                source_agent=contract["source"],
                target_agent=contract["target"],
                error_code="DATA_CONFLICT",
                message="Field values conflict with previously validated agent outputs.",
                details={"conflicts": conflicts},
                action="HUMAN_REVIEW",
            )
        return None
