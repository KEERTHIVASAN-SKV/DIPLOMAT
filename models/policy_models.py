from pydantic import BaseModel, Field
from typing import Optional

class PolicyOutput(BaseModel):
    policy_id: str
    policy_status: str          # ACTIVE, EXPIRED, CANCELLED, SUSPENDED, LAPSED
    coverage_type: str          # ACCIDENTAL_DAMAGE, HEALTH, THEFT, COMPREHENSIVE
    coverage_limit: float
    deductible: float
    copay: float                # Percentage 0-100
    currency: str               # ISO-4217
    policy_start: str           # YYYY-MM-DD
    policy_expiry: str          # YYYY-MM-DD
    exclusions: list[str] = Field(default_factory=list)
    sub_limits: dict = Field(default_factory=dict)
    source: str = "POLICY_DOCUMENT"
