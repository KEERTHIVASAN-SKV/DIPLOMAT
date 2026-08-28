from pydantic import BaseModel, Field

class SettlementOutput(BaseModel):
    claim_id: str
    assessed_amount: float
    coverage_limit: float
    deductible: float
    copay_percentage: float
    copay_amount: float
    payable_amount: float
    currency: str
    status: str             # APPROVED, HUMAN_REVIEW, REJECTED
    calculation_breakdown: dict = Field(default_factory=dict)
    notes: str = ""
