"""
DIPLOMAT Gate - Insurance claim calculation verification
"""
from typing import Tuple, List, Dict, Any


class DiplomatGate:
    """Validates insurance claim calculations and deductions."""
    
    def __init__(self, policy_doc: dict):
        self.policy = policy_doc
        self.rule_registry = self._build_rule_registry()
    
    def _build_rule_registry(self):
        """Build rule registry using PolicyEngine."""
        from agents.policy_engine import PolicyEngine
        return PolicyEngine(self.policy).registry
    
    def validate(self, settlement: dict, extraction: dict) -> Tuple[bool, List[dict]]:
        """
        Run validation checks on settlement calculations.
        
        Args:
            settlement: Settlement/adjudication result
            extraction: Extracted claim data
        
        Returns:
            Tuple of (is_valid, list_of_bounces)
        """
        bounces = []
        
        # C4_CITATION_RULE: Every deduction must have a valid clause_id
        deductions = settlement.get("deductions", [])
        
        for idx, deduction in enumerate(deductions):
            clause_id = deduction.get("clause_id")
            
            # Check if clause_id is missing or null
            if clause_id is None:
                bounces.append({
                    "check": "C4_CITATION_RULE",
                    "severity": "CRITICAL",
                    "message": f"Deduction missing clause_id citation",
                    "deduction_id": deduction.get("deduction_id", f"deduction_{idx}"),
                    "deduction_index": idx,
                    "description": deduction.get("description", "")
                })
                continue
            
            # Check if clause_id exists in rule registry
            if clause_id not in self.rule_registry:
                valid_clauses = list(self.rule_registry.keys())
                bounces.append({
                    "check": "C4_CITATION_RULE",
                    "severity": "CRITICAL",
                    "message": f"Invalid clause_id: {clause_id} not found in policy",
                    "deduction_id": deduction.get("deduction_id", f"deduction_{idx}"),
                    "deduction_index": idx,
                    "invalid_clause_id": clause_id,
                    "valid_clauses": valid_clauses
                })
        
        # C5_RECOMPUTE_RULE: Independently recompute each deduction
        for idx, deduction in enumerate(deductions):
            clause_id = deduction.get("clause_id")
            
            # Skip if clause_id is invalid (already bounced above)
            if clause_id is None or clause_id not in self.rule_registry:
                continue
            
            actual_amount = deduction.get("amount", 0)
            expected_amount = None
            
            # Recompute based on clause_id
            if clause_id == "R1":  # Room rent sublimit
                actual_rate = extraction.get("room_rent_per_day", {}).get("value", 0)
                limit = self.policy.get("room_rent_limit", 0)
                days = extraction.get("room_rent_days", {}).get("value", 0)
                
                if actual_rate > limit:
                    expected_amount = (actual_rate - limit) * days
                else:
                    expected_amount = 0
            
            elif clause_id == "R2":  # Room rent proportionate
                actual_rate = extraction.get("room_rent_per_day", {}).get("value", 0)
                limit = self.policy.get("room_rent_limit", 0)
                
                # Calculate linked charges (surgery + diagnostics)
                line_items = extraction.get("line_items", [])
                linked_total = sum(
                    item.get("amount", 0)
                    for item in line_items
                    if item.get("category") in ["surgery", "diagnostics"]
                )
                
                if actual_rate > 0:
                    proportion = (actual_rate - limit) / actual_rate
                    expected_amount = linked_total * proportion
                else:
                    expected_amount = 0
            
            elif clause_id == "R3":  # Non-payable items
                line_items = extraction.get("line_items", [])
                expected_amount = sum(
                    item.get("amount", 0)
                    for item in line_items
                    if item.get("category") == "non_payable"
                )
            
            elif clause_id == "R4":  # Copay
                base_amount = deduction.get("base_amount", 0)
                percent = self.policy.get("copay_percent", 0)
                expected_amount = base_amount * percent / 100
            
            # Check if recomputed amount matches
            if expected_amount is not None:
                difference = abs(expected_amount - actual_amount)
                if difference > 0.01:
                    bounces.append({
                        "check": "C5_RECOMPUTE_RULE",
                        "severity": "CRITICAL",
                        "message": f"Deduction amount mismatch: recomputation failed",
                        "deduction_id": deduction.get("deduction_id", f"deduction_{idx}"),
                        "clause_id": clause_id,
                        "expected": round(expected_amount, 2),
                        "got": round(actual_amount, 2),
                        "difference": round(difference, 2),
                        "agent_calculation": deduction.get("calculation", "")
                    })
        
        # C6_IDENTITY: payable must equal bill_total - total_deductions
        bill_total = settlement.get("bill_total", 0)
        total_deductions = settlement.get("total_deductions", 0)
        payable = settlement.get("payable", 0)
        
        expected_payable = bill_total - total_deductions
        payable_difference = abs(expected_payable - payable)
        
        if payable_difference > 0.01:
            bounces.append({
                "check": "C6_IDENTITY",
                "severity": "CRITICAL",
                "message": "Payable amount does not match bill_total - total_deductions",
                "bill_total": bill_total,
                "total_deductions": total_deductions,
                "expected_payable": round(expected_payable, 2),
                "got_payable": round(payable, 2),
                "difference": round(payable_difference, 2)
            })
        
        # C7_PED_LINKAGE: Pre-existing deductions must have evidence
        for idx, deduction in enumerate(deductions):
            category = deduction.get("category", "")
            
            if category == "pre_existing":
                if "ped_evidence" not in deduction or deduction.get("ped_evidence") is None:
                    bounces.append({
                        "check": "C7_PED_LINKAGE",
                        "severity": "CRITICAL",
                        "message": "Pre-existing disease deduction missing evidence field",
                        "deduction_id": deduction.get("deduction_id", f"deduction_{idx}"),
                        "deduction_index": idx,
                        "description": deduction.get("description", ""),
                        "required_field": "ped_evidence"
                    })
        
        # Return validation result
        is_valid = len(bounces) == 0
        return (is_valid, bounces)
