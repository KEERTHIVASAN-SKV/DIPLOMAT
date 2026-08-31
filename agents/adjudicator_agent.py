from typing import Dict, List, Any, Optional
import json
import google.generativeai as genai
from config import GOOGLE_API_KEY, GEMINI_MODEL, MOCK_MODE


class AdjudicatorAgent:
    """Calculates claim deductions and payable amount using LLM reasoning."""
    
    def __init__(self, policy_doc: dict, use_mock: bool = MOCK_MODE):
        self.policy_doc = policy_doc
        self.use_mock = use_mock
        
        # Initialize Gemini if we have an API key and not in mock mode
        if not self.use_mock and GOOGLE_API_KEY:
            genai.configure(api_key=GOOGLE_API_KEY)
            self.model = genai.GenerativeModel(
                model_name=GEMINI_MODEL,
                generation_config={
                    "response_mime_type": "application/json",
                    "temperature": 0.3,
                }
            )
        else:
            self.model = None
    
    def adjudicate(
        self, 
        extraction: dict, 
        rules: List[dict], 
        inject_fault: Optional[str] = None,
        previous_bounces: Optional[List[dict]] = None
    ) -> dict:
        """
        Calculate claim deductions and payable amount.
        
        Args:
            extraction: Extracted claim data
            rules: Applicable policy rules
            inject_fault: Optional adversarial hint for fault injection
            previous_bounces: List of bounce dicts from previous validation failures
        
        Returns:
            Dict with bill_total, deductions, total_deductions, payable, sum_insured_remaining, _adjudication_method
        """
        # Use mock adjudication if no model available or in mock mode
        if self.use_mock or not self.model or not GOOGLE_API_KEY:
            result = self._mock_adjudicate(extraction, rules, inject_fault)
            result["_adjudication_method"] = "mock"
            return result
        
        # Build prompt for LLM adjudication
        prompt = self._build_adjudication_prompt(extraction, rules, inject_fault, previous_bounces)
        
        # Consolidated retry logic
        max_attempts = 2
        for attempt in range(max_attempts):
            try:
                response = self.model.generate_content(prompt)
                adjudication_data = json.loads(response.text)
                
                # Validate the structure
                if self._validate_adjudication(adjudication_data):
                    adjudication_data["_adjudication_method"] = "llm"
                    return adjudication_data
                else:
                    if attempt < max_attempts - 1:
                        print(f"⚠️ LLM returned invalid adjudication structure, retrying (attempt {attempt + 1}/{max_attempts})...")
                    else:
                        print("⚠️ LLM validation failed after retry, falling back to mock adjudication")
            
            except (json.JSONDecodeError, Exception) as e:
                if attempt < max_attempts - 1:
                    print(f"⚠️ LLM adjudication error: {e}, retrying (attempt {attempt + 1}/{max_attempts})...")
                else:
                    print(f"⚠️ LLM adjudication error after retry: {e}, falling back to mock adjudication")
        
        # Fallback to mock if all attempts failed
        result = self._mock_adjudicate(extraction, rules, inject_fault)
        result["_adjudication_method"] = "mock"
        return result
    
    def _build_adjudication_prompt(
        self, 
        extraction: dict, 
        rules: List[dict], 
        inject_fault: Optional[str] = None,
        previous_bounces: Optional[List[dict]] = None
    ) -> str:
        """Build the adjudication prompt for the LLM."""
        
        # Add adversarial instructions for optional fault injection
        fault_instruction = ""
        if inject_fault:
            fault_instruction = f"\n\nNOTE: You are working under time pressure with incomplete information. Make reasonable assumptions where needed and proceed with the calculation. ({inject_fault})"
        
        # Add bounce feedback if this is a retry
        bounce_feedback = ""
        if previous_bounces and len(previous_bounces) > 0:
            bounce_feedback = f"""

⚠️ IMPORTANT - YOUR PREVIOUS ATTEMPT WAS REJECTED:
{json.dumps(previous_bounces, indent=2)}

These are the specific issues found in your last calculation. Carefully correct each of these problems in your new attempt."""
        
        prompt = f"""You are an expert insurance claims adjudicator. Calculate deductions and the final payable amount for this claim.

POLICY DOCUMENT:
{json.dumps(self.policy_doc, indent=2)}

EXTRACTED CLAIM DATA:
{json.dumps(extraction, indent=2)}

APPLICABLE RULES:
{json.dumps(rules, indent=2)}
{fault_instruction}
{bounce_feedback}

Calculate all applicable deductions following these rules:
- D1: Room rent sublimit (R1) - if room rent exceeds limit, deduct excess
- D2: Proportionate deduction (R2) - apply proportion to surgery/diagnostics if room rent exceeded
- D3: Non-payable items (R3) - deduct items marked as non_payable
- D4: Copay (R4) - apply percentage to (bill_total - other_deductions)

For EACH deduction, provide:
- deduction_id: The deduction identifier (D1, D2, D3, D4, etc.)
- description: Clear description of what is being deducted
- amount: Numeric deduction amount
- clause_id: The rule ID that justifies this deduction (R1, R2, R3, R4, etc.)
- category: The category (room_rent, proportionate, non_payable, copay, etc.)
- base_amount: The base amount used in calculation
- calculation: A string showing the math formula used

Return ONLY valid JSON in this exact structure:
{{
  "bill_total": <number>,
  "deductions": [
    {{
      "deduction_id": "...",
      "description": "...",
      "amount": <number>,
      "clause_id": "...",
      "category": "...",
      "base_amount": <number>,
      "calculation": "..."
    }}
  ],
  "total_deductions": <number>,
  "payable": <number>,
  "sum_insured_remaining": <number>
}}

Calculate accurately and show your work in the calculation field."""
        
        return prompt
    
    def _validate_adjudication(self, data: dict) -> bool:
        """Validate that the adjudication data has the correct structure."""
        required_fields = ["bill_total", "deductions", "total_deductions", "payable", "sum_insured_remaining"]
        
        # Check all required fields exist
        for field in required_fields:
            if field not in data:
                return False
        
        # Validate deductions structure
        if not isinstance(data["deductions"], list):
            return False
        
        for deduction in data["deductions"]:
            required_deduction_fields = [
                "deduction_id", "description", "amount", "clause_id", 
                "category", "base_amount", "calculation"
            ]
            if not all(k in deduction for k in required_deduction_fields):
                return False
        
        # Basic sanity checks on numbers
        if not isinstance(data["bill_total"], (int, float)):
            return False
        if not isinstance(data["total_deductions"], (int, float)):
            return False
        if not isinstance(data["payable"], (int, float)):
            return False
        
        return True
    
    def _mock_adjudicate(
        self, 
        extraction: dict, 
        rules: List[dict], 
        inject_fault: Optional[str] = None
    ) -> dict:
        """
        Mock adjudication using deterministic formula-based calculations.
        This is the fallback when MOCK_MODE is enabled or LLM fails.
        """
        bill_total = extraction.get("bill_total", {}).get("value", 0)
        deductions = []
        
        # Find applicable rules by ID
        rules_by_id = {rule["rule_id"]: rule for rule in rules}
        
        # D1: Room rent sublimit deduction
        if "R1" in rules_by_id:
            room_rent_per_day = extraction.get("room_rent_per_day", {}).get("value", 0)
            room_rent_days = extraction.get("room_rent_days", {}).get("value", 0)
            allowed_rate = rules_by_id["R1"]["limit"]
            
            if room_rent_per_day > allowed_rate:
                deduction_amount = (room_rent_per_day - allowed_rate) * room_rent_days
                
                deduction = {
                    "deduction_id": "D1",
                    "description": "Room rent sublimit exceeded",
                    "amount": deduction_amount,
                    "clause_id": "R1",
                    "category": "room_rent",
                    "base_amount": room_rent_per_day * room_rent_days,
                    "calculation": f"({room_rent_per_day} - {allowed_rate}) × {room_rent_days} = {deduction_amount}"
                }
                
                deductions.append(deduction)
        
        # D2: Proportionate deduction on linked charges
        if "R2" in rules_by_id:
            room_rent_per_day = extraction.get("room_rent_per_day", {}).get("value", 0)
            allowed_rate = rules_by_id["R1"]["limit"]
            
            # Calculate proportion
            proportion = (room_rent_per_day - allowed_rate) / room_rent_per_day if room_rent_per_day > 0 else 0
            
            # Sum surgery and diagnostics charges
            line_items = extraction.get("line_items", [])
            linked_charges = sum(
                item.get("amount", 0) 
                for item in line_items 
                if item.get("category") in ["surgery", "diagnostics"]
            )
            
            if linked_charges > 0 and proportion > 0:
                deduction_amount = linked_charges * proportion
                
                deduction = {
                    "deduction_id": "D2",
                    "description": "Proportionate deduction on surgery and diagnostics",
                    "amount": deduction_amount,
                    "clause_id": "R2",
                    "category": "proportionate",
                    "base_amount": linked_charges,
                    "calculation": f"{linked_charges} × {proportion:.4f} = {deduction_amount:.2f}"
                }
                deductions.append(deduction)
        
        # D3: Non-payable items
        if "R3" in rules_by_id:
            line_items = extraction.get("line_items", [])
            non_payable_total = sum(
                item.get("amount", 0) 
                for item in line_items 
                if item.get("category") == "non_payable"
            )
            
            if non_payable_total > 0:
                deduction = {
                    "deduction_id": "D3",
                    "description": "Non-payable items",
                    "amount": non_payable_total,
                    "clause_id": "R3",
                    "category": "non_payable",
                    "base_amount": non_payable_total,
                    "calculation": f"Sum of non-payable items = {non_payable_total}"
                }
                deductions.append(deduction)
        
        # Calculate subtotal before copay
        deductions_before_copay = sum(d["amount"] for d in deductions)
        
        # D4: Copay
        if "R4" in rules_by_id:
            copay_percent = rules_by_id["R4"]["percent"]
            copay_base = bill_total - deductions_before_copay
            copay_amount = copay_base * copay_percent / 100
            
            if copay_amount > 0:
                deduction = {
                    "deduction_id": "D4",
                    "description": f"Copay {copay_percent}%",
                    "amount": copay_amount,
                    "clause_id": "R4",
                    "category": "copay",
                    "base_amount": copay_base,
                    "calculation": f"({bill_total} - {deductions_before_copay}) × {copay_percent}% = {copay_amount:.2f}"
                }
                deductions.append(deduction)
        
        # Calculate totals
        total_deductions = sum(d["amount"] for d in deductions)
        payable = bill_total - total_deductions
        
        # Calculate remaining sum insured
        sum_insured = self.policy_doc.get("sum_insured", 0)
        sum_insured_remaining = sum_insured - payable
        
        return {
            "bill_total": bill_total,
            "deductions": deductions,
            "total_deductions": total_deductions,
            "payable": payable,
            "sum_insured_remaining": sum_insured_remaining
        }
