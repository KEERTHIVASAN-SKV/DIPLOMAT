from typing import Dict, List, Any, Optional


class AdjudicatorAgent:
    """Pure calculator for claim adjudication - NO LLM."""
    
    def __init__(self, policy_doc: dict):
        self.policy_doc = policy_doc
    
    def adjudicate(
        self, 
        extraction: dict, 
        rules: List[dict], 
        inject_fault: Optional[str] = None
    ) -> dict:
        """
        Calculate claim deductions and payable amount.
        
        Args:
            extraction: Extracted claim data
            rules: Applicable policy rules
            inject_fault: Fault injection type
        
        Returns:
            Dict with bill_total, deductions, total_deductions, payable, sum_insured_remaining
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
                
                # Inject fault: missing citation
                if inject_fault == "missing_citation":
                    deduction["clause_id"] = None
                
                deductions.append(deduction)
        
        # D2: Proportionate deduction on linked charges
        if "R2" in rules_by_id:
            room_rent_per_day = extraction.get("room_rent_per_day", {}).get("value", 0)
            allowed_rate = rules_by_id["R1"]["limit"]
            
            # Calculate proportion
            if inject_fault == "wrong_proportion":
                proportion = 0.1
            else:
                proportion = (room_rent_per_day - allowed_rate) / room_rent_per_day if room_rent_per_day > 0 else 0
            
            # Sum surgery and diagnostics charges
            line_items = extraction.get("line_items", [])
            linked_charges = sum(
                item.get("amount", 0) 
                for item in line_items 
                if item.get("category") in ["surgery", "diagnostics"]
            )
            
            if linked_charges > 0:
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
        
        # Inject fault: wrong PED link
        if inject_fault == "wrong_ped_link":
            fake_ped_deduction = {
                "deduction_id": "D5",
                "description": "Pre-existing disease waiting period",
                "amount": 5000,
                "clause_id": "R5",
                "category": "pre_existing",
                "base_amount": 5000,
                "calculation": "Fake PED deduction with no evidence"
            }
            deductions.append(fake_ped_deduction)
        
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
