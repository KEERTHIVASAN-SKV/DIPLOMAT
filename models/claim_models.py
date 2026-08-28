from pydantic import BaseModel, Field
from typing import Optional

class EstimatedDamage(BaseModel):
    amount: float = Field(..., description="Damage amount")
    currency: str = Field(..., description="ISO-4217 currency code, e.g. INR")

class ClaimOutput(BaseModel):
    claim_id: str
    policy_id: str
    incident_date: str                  # YYYY-MM-DD
    incident_type: str                  # ACCIDENT, THEFT, FIRE, HEALTH...
    incident_description: str
    claimant_name: str
    estimated_damage: EstimatedDamage
    supporting_documents: list[str] = Field(default_factory=list)
