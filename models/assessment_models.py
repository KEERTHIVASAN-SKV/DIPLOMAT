from pydantic import BaseModel, Field

class DamageItem(BaseModel):
    part: str
    amount: float
    description: str = ""

class AssessmentOutput(BaseModel):
    claim_id: str
    damage_items: list[DamageItem]
    assessed_amount: float
    currency: str
    source: str = "ASSESSMENT_REPORT"
    evidence_ids: list[str] = Field(default_factory=list)
    notes: str = ""
