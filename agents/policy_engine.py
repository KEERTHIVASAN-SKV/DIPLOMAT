from typing import Dict, List, Any


class PolicyEngine:
    """Pure lookup table for policy rules - NO LLM."""
    
    def __init__(self, policy_doc: dict):
        self.policy_doc = policy_doc
        self.registry = self._build_registry()
    
    def _build_registry(self) -> dict:
        """
        Build policy rules registry.
        
        Returns:
            Dict of rule_id -> rule details
        """
        registry = {}
        
        # R1: Room rent sublimit
        registry["R1"] = {
            "rule_id": "R1",
            "type": "sublimit",
            "limit": self.policy_doc.get("room_rent_limit", 0),
            "applies_to": ["room_rent"],
            "description": "Room rent sublimit"
        }
        
        # R2: Room rent proportionate deduction
        registry["R2"] = {
            "rule_id": "R2",
            "type": "proportionate",
            "enabled": self.policy_doc.get("proportionate_deduction", False),
            "applies_to": ["surgery", "diagnostics"],
            "description": "Proportionate deduction on linked charges"
        }
        
        # R3: Non-payable items exclusion
        registry["R3"] = {
            "rule_id": "R3",
            "type": "exclusion",
            "items": self.policy_doc.get("non_payable_items", []),
            "applies_to": ["non_payable"],
            "description": "Non-payable items"
        }
        
        # R4: Copay deduction
        registry["R4"] = {
            "rule_id": "R4",
            "type": "deduction",
            "percent": self.policy_doc.get("copay_percent", 0),
            "description": "Copay deduction"
        }
        
        # R5: Waiting period for pre-existing diseases
        registry["R5"] = {
            "rule_id": "R5",
            "type": "exclusion",
            "conditions": self.policy_doc.get("ped_waiting_period_conditions", []),
            "applies_to": ["pre_existing"],
            "description": "Waiting period for pre-existing diseases"
        }
        
        return registry
    
    def get_applicable_rules(self, extraction: dict) -> List[dict]:
        """
        Get rules that apply to this specific claim based on extracted data.
        
        Args:
            extraction: Extracted claim data
        
        Returns:
            List of applicable rules
        """
        applicable = []
        
        # R1: Always applicable if room rent exists
        if extraction.get("room_rent_total", {}).get("value", 0) > 0:
            applicable.append(self.registry["R1"])
        
        # R2: Applicable if proportionate deduction is enabled and room rent exceeded
        room_rent_per_day = extraction.get("room_rent_per_day", {}).get("value", 0)
        room_rent_limit = self.registry["R1"]["limit"]
        if self.registry["R2"]["enabled"] and room_rent_per_day > room_rent_limit:
            # Check if there are surgery or diagnostics items
            line_items = extraction.get("line_items", [])
            has_linked_charges = any(
                item.get("category") in ["surgery", "diagnostics"] 
                for item in line_items
            )
            if has_linked_charges:
                applicable.append(self.registry["R2"])
        
        # R3: Applicable if there are non-payable items in the bill
        line_items = extraction.get("line_items", [])
        has_non_payable = any(
            item.get("category") == "non_payable" 
            for item in line_items
        )
        if has_non_payable:
            applicable.append(self.registry["R3"])
        
        # R4: Always applicable if copay is configured
        if self.registry["R4"]["percent"] > 0:
            applicable.append(self.registry["R4"])
        
        # R5: Applicable if patient has pre-existing conditions in waiting period
        pre_existing = extraction.get("pre_existing_conditions", {}).get("value", [])
        ped_conditions = self.registry["R5"]["conditions"]
        has_ped_match = any(
            condition in ped_conditions 
            for condition in pre_existing
        )
        if has_ped_match:
            applicable.append(self.registry["R5"])
        
        return applicable
