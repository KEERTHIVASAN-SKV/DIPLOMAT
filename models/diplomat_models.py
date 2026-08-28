from pydantic import BaseModel, Field
from typing import Optional, Any
from enum import Enum
from datetime import datetime

class DiplomatStatus(str, Enum):
    PASS = "PASS"
    REJECTED = "REJECTED"
    HUMAN_REVIEW = "HUMAN_REVIEW"

class DiplomatResult(BaseModel):
    status: DiplomatStatus
    source_agent: str
    target_agent: str
    error_code: Optional[str] = None
    message: Optional[str] = None
    details: dict = Field(default_factory=dict)
    action: str = "CONTINUE"   # CONTINUE, CORRECT_AND_RETRY, HUMAN_REVIEW, BLOCK

class HandoffRecord(BaseModel):
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())
    source_agent: str
    target_agent: str
    result: DiplomatResult
    payload_summary: dict = Field(default_factory=dict)
