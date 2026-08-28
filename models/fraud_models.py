from pydantic import BaseModel, Field

class FraudOutput(BaseModel):
    claim_id: str
    risk_level: str         # LOW, MEDIUM, HIGH
    risk_score: float       # 0.0 - 1.0
    reasons: list[str]
    evidence_ids: list[str]
    recommendation: str     # PROCEED, HUMAN_REVIEW, REJECT
    checked_against: list[str] = Field(default_factory=list)
