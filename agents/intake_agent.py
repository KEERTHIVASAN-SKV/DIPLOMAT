from typing import Dict, List, Any, Optional


class IntakeAgent:
    """Extracts structured data from insurance documents with source citations."""
    
    def __init__(self, use_mock: bool = True):
        self.use_mock = use_mock
    
    def extract(
        self, 
        policy_doc: dict, 
        bill_doc: dict, 
        discharge_doc: dict, 
        inject_fault: Optional[str] = None
    ) -> dict:
        """
        Extract structured data from insurance documents.
        
        Args:
            policy_doc: Policy document dict
            bill_doc: Bill document dict
            discharge_doc: Discharge summary document dict
            inject_fault: Fault injection type ("room_rent_misread", "missing_date", "ped_hallucination")
        
        Returns:
            Dict with extracted fields, each having value, source, and page
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
