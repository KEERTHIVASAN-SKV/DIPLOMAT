from typing import Tuple, List, Dict, Any


class VeritasGate:
    """Input verification gate that catches document misreads before they poison calculations."""
    
    def __init__(self):
        pass
    
    def validate(
        self, 
        extraction: dict, 
        bill_doc: dict, 
        discharge_doc: dict, 
        policy_doc: dict
    ) -> Tuple[bool, List[dict]]:
        """
        Run deterministic checks on extracted data.
        
        Args:
            extraction: Extracted claim data
            bill_doc: Original bill document
            discharge_doc: Original discharge document
            policy_doc: Original policy document
        
        Returns:
            Tuple of (is_valid, list_of_bounces)
        """
        bounces = []
        
        # C1_BILL_INTEGRITY: Sum of line items must equal bill total
        line_items = extraction.get("line_items", [])
        line_items_sum = sum(item.get("amount", 0) for item in line_items)
        bill_total = extraction.get("bill_total", {}).get("value", 0)
        
        if line_items_sum != bill_total:
            bounces.append({
                "check": "C1_BILL_INTEGRITY",
                "severity": "CRITICAL",
                "message": f"Line items sum does not match bill total",
                "expected": bill_total,
                "got": line_items_sum,
                "difference": abs(bill_total - line_items_sum)
            })
        
        # C2_CROSS_DOC_DATE: Admission dates must match across documents
        bill_admission_date = bill_doc.get("admission_date", "")
        discharge_admission_date = discharge_doc.get("admission_date", "")
        extraction_admission_date = extraction.get("admission_date", {}).get("value", "")
        
        if not (bill_admission_date == discharge_admission_date == extraction_admission_date):
            bounces.append({
                "check": "C2_CROSS_DOC_DATE",
                "severity": "CRITICAL",
                "message": "Admission date mismatch across documents",
                "bill_date": bill_admission_date,
                "discharge_date": discharge_admission_date,
                "extraction_date": extraction_admission_date
            })
        
        # C2_CROSS_DOC_NAME: Patient names must match across documents (case-insensitive)
        bill_patient_name = bill_doc.get("patient_name", "").lower()
        discharge_patient_name = discharge_doc.get("patient_name", "").lower()
        extraction_patient_name = extraction.get("patient_name", {}).get("value", "").lower()
        
        if not (bill_patient_name == discharge_patient_name == extraction_patient_name):
            bounces.append({
                "check": "C2_CROSS_DOC_NAME",
                "severity": "CRITICAL",
                "message": "Patient name mismatch across documents",
                "bill_name": bill_doc.get("patient_name", ""),
                "discharge_name": discharge_doc.get("patient_name", ""),
                "extraction_name": extraction.get("patient_name", {}).get("value", "")
            })
        
        # C3_SOURCE_CITATION (room rent): Value must appear in source citation
        room_rent_per_day_value = str(extraction.get("room_rent_per_day", {}).get("value", ""))
        room_rent_per_day_source = extraction.get("room_rent_per_day", {}).get("source", "")
        
        if room_rent_per_day_value not in room_rent_per_day_source:
            bounces.append({
                "check": "C3_SOURCE_CITATION",
                "severity": "CRITICAL",
                "message": "Room rent per day value not found in source citation - possible OCR misread",
                "field": "room_rent_per_day",
                "value": room_rent_per_day_value,
                "source": room_rent_per_day_source,
                "hint": "OCR may have misread the room rent rate"
            })
        
        # C3_SOURCE_CITATION (line items): Each amount must appear in its source
        for idx, item in enumerate(line_items):
            item_amount = str(item.get("amount", ""))
            item_source = item.get("source", "")
            
            if item_amount not in item_source:
                bounces.append({
                    "check": "C3_SOURCE_CITATION",
                    "severity": "CRITICAL",
                    "message": f"Line item amount not found in source citation",
                    "field": "line_items",
                    "item_index": idx,
                    "item_id": item.get("item_id", ""),
                    "description": item.get("description", ""),
                    "value": item_amount,
                    "source": item_source,
                    "hint": "OCR may have misread the line item amount"
                })
        
        # C6_POLICY_LINK: Policy ID must match
        extraction_policy_id = extraction.get("policy_id", {}).get("value", "")
        policy_doc_id = policy_doc.get("policy_id", "")
        
        if extraction_policy_id != policy_doc_id:
            bounces.append({
                "check": "C6_POLICY_LINK",
                "severity": "CRITICAL",
                "message": "Policy ID mismatch between extraction and policy document",
                "extraction_policy_id": extraction_policy_id,
                "policy_doc_id": policy_doc_id
            })
        
        # Return validation result
        is_valid = len(bounces) == 0
        return (is_valid, bounces)
