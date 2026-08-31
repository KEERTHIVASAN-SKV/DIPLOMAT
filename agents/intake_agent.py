from typing import Dict, List, Any, Optional
import json
import google.generativeai as genai
from config import GOOGLE_API_KEY, GEMINI_MODEL, MOCK_MODE


class IntakeAgent:
    """Extracts structured data from insurance documents with source citations."""
    
    def __init__(self, use_mock: bool = MOCK_MODE):
        self.use_mock = use_mock
        
        # Initialize Gemini if we have an API key and not in mock mode
        if not self.use_mock and GOOGLE_API_KEY:
            genai.configure(api_key=GOOGLE_API_KEY)
            self.model = genai.GenerativeModel(
                model_name=GEMINI_MODEL,
                generation_config={
                    "response_mime_type": "application/json",
                    "temperature": 0.3,  # Raised from 0.1 to 0.3 for genuine misreads
                }
            )
        else:
            self.model = None
    
    def extract(
        self, 
        policy_doc: dict, 
        bill_doc: dict, 
        discharge_doc: dict, 
        inject_fault: Optional[str] = None,
        previous_bounces: Optional[List[dict]] = None
    ) -> dict:
        """
        Extract structured data from insurance documents.
        
        Args:
            policy_doc: Policy document dict
            bill_doc: Bill document dict
            discharge_doc: Discharge summary document dict
            inject_fault: Fault injection type ("room_rent_misread", "missing_date", "ped_hallucination")
            previous_bounces: List of bounce dicts from previous validation failures
        
        Returns:
            Dict with extracted fields, each having value, source, and page
        """
        # Use mock extraction if no model available or in mock mode
        if self.use_mock or not self.model or not GOOGLE_API_KEY:
            result = self._mock_extract(policy_doc, bill_doc, discharge_doc, inject_fault)
            result["_extraction_method"] = "mock"
            return result
        
        # Build prompt for LLM extraction
        prompt = self._build_extraction_prompt(policy_doc, bill_doc, discharge_doc, inject_fault, previous_bounces)
        
        # Consolidated retry logic for both JSON parse and validation errors
        max_attempts = 2
        for attempt in range(max_attempts):
            try:
                response = self.model.generate_content(prompt)
                extracted_data = json.loads(response.text)
                
                # Validate the structure
                if self._validate_extraction(extracted_data):
                    extracted_data["_extraction_method"] = "llm"
                    return extracted_data
                else:
                    if attempt < max_attempts - 1:
                        print(f"⚠️ LLM returned invalid structure, retrying (attempt {attempt + 1}/{max_attempts})...")
                    else:
                        print("⚠️ LLM validation failed after retry, falling back to mock extraction")
            
            except (json.JSONDecodeError, Exception) as e:
                if attempt < max_attempts - 1:
                    print(f"⚠️ LLM extraction error: {e}, retrying (attempt {attempt + 1}/{max_attempts})...")
                else:
                    print(f"⚠️ LLM extraction error after retry: {e}, falling back to mock extraction")
        
        # Fallback to mock if all attempts failed
        result = self._mock_extract(policy_doc, bill_doc, discharge_doc, inject_fault)
        result["_extraction_method"] = "mock"
        return result
    
    def _build_extraction_prompt(
        self, 
        policy_doc: dict, 
        bill_doc: dict, 
        discharge_doc: dict, 
        inject_fault: Optional[str] = None,
        previous_bounces: Optional[List[dict]] = None
    ) -> str:
        """Build the extraction prompt for the LLM."""
        
        # Add adversarial instructions for fault injection
        fault_instruction = ""
        if inject_fault == "room_rent_misread":
            fault_instruction = "\n\nNOTE: The room rent per day line in the bill appears slightly smudged or unclear. Use your best judgment to read the value, but it may be difficult to make out clearly."
        elif inject_fault == "missing_date":
            fault_instruction = "\n\nNOTE: The admission date in the discharge summary is partially illegible. Infer a reasonable date based on other contextual information if needed."
        elif inject_fault == "ped_hallucination":
            fault_instruction = "\n\nNOTE: The pre-existing conditions section may have some handwritten notes that are hard to read. Extract any conditions you can identify, even if you're not completely certain."
        
        # Add bounce feedback if this is a retry
        bounce_feedback = ""
        if previous_bounces and len(previous_bounces) > 0:
            bounce_feedback = f"""

⚠️ IMPORTANT - YOUR PREVIOUS ATTEMPT WAS REJECTED:
{json.dumps(previous_bounces, indent=2)}

These are the specific issues found in your last extraction. Carefully correct each of these problems in your new attempt."""
        
        prompt = f"""You are an expert medical claims processor. Extract structured data from the following insurance documents.

POLICY DOCUMENT:
{json.dumps(policy_doc, indent=2)}

BILL DOCUMENT:
{json.dumps(bill_doc, indent=2)}

DISCHARGE SUMMARY:
{json.dumps(discharge_doc, indent=2)}
{fault_instruction}
{bounce_feedback}

Extract the following fields. For EACH field, provide:
- "value": the extracted value
- "source": a citation describing where you found this information. The source field MUST contain the literal extracted value as plain text, exactly as returned in the value field, with no currency symbols, no commas, no reformatting — e.g. if room_rent_per_day value is 3000, the source string must contain the exact substring '3000' somewhere in it, such as 'Bill line: room_rent_per_day = 3000 INR/day'.
- "page": the page number (use 1 for all fields in this case)

For line_items, each item should include: item_id, description, category, amount, source, page. Each line item's source field MUST likewise contain the literal amount value as plain text, exactly as returned in the amount field, with no currency symbols, no commas, no reformatting — e.g. if amount is 4500, the source string must contain the exact substring '4500' somewhere in it, such as 'Bill line: surgery = 4500 INR'.

Return ONLY valid JSON in this exact structure:
{{
  "policy_id": {{"value": "...", "source": "...", "page": 1}},
  "patient_name": {{"value": "...", "source": "...", "page": 1}},
  "admission_date": {{"value": "YYYY-MM-DD", "source": "...", "page": 1}},
  "room_rent_per_day": {{"value": <number>, "source": "...", "page": 1}},
  "room_rent_days": {{"value": <number>, "source": "...", "page": 1}},
  "room_rent_total": {{"value": <number>, "source": "...", "page": 1}},
  "line_items": [
    {{
      "item_id": "...",
      "description": "...",
      "category": "...",
      "amount": <number>,
      "source": "...",
      "page": 1
    }}
  ],
  "bill_total": {{"value": <number>, "source": "...", "page": 1}},
  "diagnosis": {{"value": "...", "source": "...", "page": 1}},
  "pre_existing_conditions": {{"value": ["..."], "source": "...", "page": 1}}
}}

Be precise and cite your sources accurately."""
        
        return prompt
    
    def _validate_extraction(self, data: dict) -> bool:
        """Validate that the extracted data has the correct structure."""
        required_fields = [
            "policy_id", "patient_name", "admission_date", 
            "room_rent_per_day", "room_rent_days", "room_rent_total",
            "line_items", "bill_total", "diagnosis", "pre_existing_conditions"
        ]
        
        # Check all required fields exist
        for field in required_fields:
            if field not in data:
                return False
            
            # Check structure for non-list fields
            if field != "line_items":
                if not isinstance(data[field], dict):
                    return False
                if not all(k in data[field] for k in ["value", "source", "page"]):
                    return False
        
        # Validate line_items structure
        if not isinstance(data["line_items"], list):
            return False
        
        for item in data["line_items"]:
            required_item_fields = ["item_id", "description", "category", "amount", "source", "page"]
            if not all(k in item for k in required_item_fields):
                return False
        
        return True
    
    def _mock_extract(
        self, 
        policy_doc: dict, 
        bill_doc: dict, 
        discharge_doc: dict, 
        inject_fault: Optional[str] = None
    ) -> dict:
        """
        Mock extraction using deterministic dict lookups.
        This is the fallback when MOCK_MODE is enabled or LLM fails.
        """
        # Extract policy information
        policy_id = {
            "value": policy_doc.get("policy_id", ""),
            "source": f"Policy document: policy_id={policy_doc.get('policy_id', '')}",
            "page": 1
        }
        
        # Extract patient name from discharge summary
        patient_name = {
            "value": discharge_doc.get("patient_name", ""),
            "source": f"Discharge summary: patient_name={discharge_doc.get('patient_name', '')}",
            "page": 1
        }
        
        # Extract admission date from discharge summary
        admission_date_value = discharge_doc.get("admission_date", "")
        if inject_fault == "missing_date":
            admission_date_value = "2026-08-02"
        
        admission_date = {
            "value": admission_date_value,
            "source": f"Discharge summary: admission_date={discharge_doc.get('admission_date', '')}",
            "page": 1
        }
        
        # Extract room rent details from bill
        room_rent_per_day_value = bill_doc.get("room_rent_per_day", 0)
        room_rent_days_value = bill_doc.get("room_rent_days", 0)
        room_rent_total_value = bill_doc.get("room_rent_total", 0)
        
        if inject_fault == "room_rent_misread":
            room_rent_per_day_value = 9999
            room_rent_total_value = 29997
        
        room_rent_per_day = {
            "value": room_rent_per_day_value,
            "source": f"Bill: room_rent_per_day={bill_doc.get('room_rent_per_day', 0)}",
            "page": 1
        }
        
        room_rent_days = {
            "value": room_rent_days_value,
            "source": f"Bill: room_rent_days={bill_doc.get('room_rent_days', 0)}",
            "page": 1
        }
        
        room_rent_total = {
            "value": room_rent_total_value,
            "source": f"Bill: room_rent_total={bill_doc.get('room_rent_total', 0)}",
            "page": 1
        }
        
        # Extract line items from bill
        line_items = []
        for item in bill_doc.get("line_items", []):
            line_items.append({
                "item_id": item.get("item_id", ""),
                "description": item.get("description", ""),
                "category": item.get("category", ""),
                "amount": item.get("amount", 0),
                "source": f"Bill line item: {item.get('description', '')} - {item.get('amount', 0)}",
                "page": 1
            })
        
        # Extract bill total
        bill_total = {
            "value": bill_doc.get("bill_total", 0),
            "source": f"Bill: bill_total={bill_doc.get('bill_total', 0)}",
            "page": 1
        }
        
        # Extract diagnosis from discharge summary
        diagnosis = {
            "value": discharge_doc.get("diagnosis", ""),
            "source": f"Discharge summary: diagnosis={discharge_doc.get('diagnosis', '')}",
            "page": 1
        }
        
        # Extract pre-existing conditions
        pre_existing_value = discharge_doc.get("pre_existing_conditions", [])
        if inject_fault == "ped_hallucination":
            pre_existing_value = ["diabetes"]
        
        pre_existing_conditions = {
            "value": pre_existing_value,
            "source": f"Discharge summary: pre_existing_conditions={discharge_doc.get('pre_existing_conditions', [])}",
            "page": 1
        }
        
        return {
            "policy_id": policy_id,
            "patient_name": patient_name,
            "admission_date": admission_date,
            "room_rent_per_day": room_rent_per_day,
            "room_rent_days": room_rent_days,
            "room_rent_total": room_rent_total,
            "line_items": line_items,
            "bill_total": bill_total,
            "diagnosis": diagnosis,
            "pre_existing_conditions": pre_existing_conditions
        }
