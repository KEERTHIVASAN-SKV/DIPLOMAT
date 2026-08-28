"""Base class for all DIPLOMAT agents."""
import json
import os
from abc import ABC, abstractmethod
from typing import Any

import config
from pydantic import ValidationError


AGENT_MODEL_MAP = {
    "ClaimAgent": "models.claim_models.ClaimOutput",
    "PolicyAgent": "models.policy_models.PolicyOutput",
    "AssessmentAgent": "models.assessment_models.AssessmentOutput",
    "FraudAgent": "models.fraud_models.FraudOutput",
    "SettlementAgent": "models.settlement_models.SettlementOutput",
}


class BaseAgent(ABC):
    """
    All agents inherit from this base.

    In MOCK_MODE (default for demo): returns pre-defined scenario data.
    In LIVE_MODE: calls the Gemini API with a structured prompt.
    """

    name: str = "BaseAgent"

    def __init__(self):
        self._llm = None
        if not config.MOCK_MODE and config.GOOGLE_API_KEY:
            try:
                import google.generativeai as genai
                genai.configure(api_key=config.GOOGLE_API_KEY)
                self._llm = genai.GenerativeModel(
                    model_name=config.GEMINI_MODEL,
                    system_instruction=self.system_prompt(),
                    generation_config={"response_mime_type": "application/json"},
                )
            except Exception as e:
                print(f"[{self.name}] Warning: Could not initialize Gemini — {e}. Falling back to mock.")

    @abstractmethod
    def system_prompt(self) -> str:
        """System prompt for the LLM."""

    @abstractmethod
    def mock_process(self, input_data: dict) -> dict:
        """Deterministic mock output for demo scenarios."""

    def process(self, input_data: dict) -> dict:
        """Call the agent. Uses LLM if available, else mock."""
        if self._llm is not None:
            try:
                response = self._llm.generate_content(json.dumps(input_data, indent=2))
                return json.loads(response.text)
            except Exception as e:
                print(f"[{self.name}] LLM call failed: {e}. Using mock fallback.")
        out = self.mock_process(input_data)
        # Validate output against pydantic models where available
        model_path = AGENT_MODEL_MAP.get(self.name)
        if model_path:
            try:
                module_path, class_name = model_path.rsplit('.', 1)
                mod = __import__(module_path, fromlist=[class_name])
                ModelClass = getattr(mod, class_name)
                validated = ModelClass(**out)
                return validated.model_dump() if hasattr(validated, 'model_dump') else validated.dict()
            except ValidationError as ve:
                print(f"[{self.name}] Output validation failed: {ve}. Returning raw output.")
            except Exception as e:
                print(f"[{self.name}] Unexpected error during output validation: {e}")
        return out
