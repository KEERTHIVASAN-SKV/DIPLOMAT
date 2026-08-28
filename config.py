import os
from dotenv import load_dotenv

load_dotenv()

GOOGLE_API_KEY: str = os.getenv("GOOGLE_API_KEY", "")
GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
MOCK_MODE: bool = os.getenv("MOCK_MODE", "true").lower() == "true"

HIGH_VALUE_THRESHOLD: float = 500_000.0
HIGH_RISK_SCORE_THRESHOLD: float = 0.75
REQUIRED_CURRENCY: str = "INR"
VALID_INCIDENT_TYPES: list[str] = ["ACCIDENT", "THEFT", "FIRE", "HEALTH", "FLOOD", "NATURAL_DISASTER"]
VALID_POLICY_STATUSES: list[str] = ["ACTIVE", "EXPIRED", "CANCELLED", "SUSPENDED", "LAPSED"]
VALID_RISK_LEVELS: list[str] = ["LOW", "MEDIUM", "HIGH"]
