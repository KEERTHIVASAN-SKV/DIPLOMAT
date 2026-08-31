"""
Policy Selector and Multi-Policy Support
Selects the best policy for a claim and handles policy variations
"""
from typing import List, Dict, Tuple, Optional
import json


class PolicySelector:
    """Intelligent policy selection and matching"""
    
    def __init__(self, available_policies: List[Dict]):
        self.policies = available_policies
        self.policy_index = self._build_index()
    
    def _build_index(self) -> Dict:
        """Build searchable index of policies"""
        index = {}
        for idx, policy in enumerate(self.policies):
            policy_id = policy.get("policy_id", f"policy_{idx}")
            coverage_types = policy.get("coverage_types", [])
            index[policy_id] = {
                "index": idx,
                "coverage": coverage_types,
                "sum_insured": policy.get("sum_insured", 0)
            }
        return index
    
    def find_best_policy(self, claim: Dict) -> Tuple[Dict, Dict]:
        """
        Find the best matching policy for a claim
        
        Returns:
            (selected_policy, matching_score)
        """
        diagnosis = claim.get("diagnosis", "").lower()
        procedure = claim.get("procedure", "").lower()
        bill_total = claim.get("bill_total", 0)
        
        scores = []
        
        for idx, policy in enumerate(self.policies):
            score = 0.0
            reasons = []
            
            # Check coverage types
            coverage_types = policy.get("coverage_types", [])
            for ctype in coverage_types:
                if ctype.lower() in diagnosis or ctype.lower() in procedure:
                    score += 0.3
                    reasons.append(f"Matches coverage: {ctype}")
            
            # Check sum insured adequacy
            sum_insured = policy.get("sum_insured", 0)
            if sum_insured >= bill_total:
                score += 0.4
                reasons.append(f"Adequate coverage: ₹{sum_insured}")
            elif sum_insured > bill_total * 0.8:
                score += 0.2
                reasons.append(f"Partial coverage: ₹{sum_insured}")
            
            # Check waiting periods
            pre_existing = claim.get("pre_existing_conditions", [])
            waiting_periods = policy.get("waiting_periods", {})
            
            has_waiting_issue = False
            for condition in pre_existing:
                if condition.lower() in waiting_periods:
                    has_waiting_issue = True
            
            if not has_waiting_issue:
                score += 0.2
                reasons.append("No waiting period conflicts")
            else:
                reasons.append("Has waiting period restrictions")
            
            # Check room rent sublimit
            room_limit = policy.get("room_rent_sublimit", 0)
            room_rent = claim.get("room_rent_per_day", {}).get("value", 0)
            if room_rent <= room_limit or room_limit == 0:
                score += 0.1
                reasons.append(f"Room rent acceptable")
            
            scores.append({
                "policy": policy,
                "score": score,
                "reasons": reasons,
                "match_percent": round(score * 100, 1)
            })
        
        # Return best match
        best = max(scores, key=lambda x: x["score"])
        return best["policy"], {
            "match_score": best["score"],
            "match_percent": best["match_percent"],
            "match_reasons": best["reasons"]
        }
    
    def get_alternative_policies(self, claim: Dict, count: int = 3) -> List[Dict]:
        """Get alternative matching policies"""
        policies_with_scores = []
        
        for policy in self.policies:
            _, score_info = self.find_best_policy({**claim, "policy_id": policy.get("policy_id")})
            policies_with_scores.append({
                "policy": policy,
                "score_info": score_info
            })
        
        sorted_policies = sorted(policies_with_scores, key=lambda x: x["score_info"]["match_score"], reverse=True)
        return sorted_policies[:count]


class PolicyComparator:
    """Compare policies for claim coverage and payouts"""
    
    @staticmethod
    def compare_coverage(policies: List[Dict], claim: Dict) -> Dict:
        """Compare how different policies would cover a claim"""
        comparisons = []
        
        bill_total = claim.get("bill_total", 0)
        
        for policy in policies:
            sum_insured = policy.get("sum_insured", 0)
            room_limit = policy.get("room_rent_sublimit", 0)
            copay = policy.get("copay_percent", 0)
            
            # Estimate coverage
            eligible = min(bill_total, sum_insured)
            estimated_copay = eligible * copay / 100
            estimated_payout = eligible - estimated_copay
            
            comparisons.append({
                "policy_id": policy.get("policy_id"),
                "sum_insured": sum_insured,
                "claim_amount": bill_total,
                "coverage_percent": (eligible / bill_total * 100) if bill_total > 0 else 0,
                "estimated_copay": round(estimated_copay, 2),
                "estimated_payout": round(estimated_payout, 2),
                "room_rent_limit": room_limit,
                "copay_percent": copay
            })
        
        return {
            "comparisons": comparisons,
            "best_policy_index": max(range(len(comparisons)), key=lambda i: comparisons[i]["estimated_payout"])
        }
    
    @staticmethod
    def analyze_coverage_gaps(policy: Dict, claim: Dict) -> Dict:
        """Identify coverage gaps in a policy"""
        gaps = []
        
        # Check waiting periods
        pre_existing = claim.get("pre_existing_conditions", [])
        waiting_periods = policy.get("waiting_periods", {})
        
        for condition in pre_existing:
            if condition.lower() in waiting_periods:
                gaps.append({
                    "gap_type": "Waiting Period",
                    "condition": condition,
                    "waiting_days": waiting_periods[condition.lower()],
                    "severity": "MEDIUM"
                })
        
        # Check room rent sublimit
        room_rent = claim.get("room_rent_per_day", {}).get("value", 0)
        room_limit = policy.get("room_rent_sublimit", 0)
        
        if room_rent > room_limit:
            gaps.append({
                "gap_type": "Room Rent Sublimit",
                "claimed": room_rent,
                "limit": room_limit,
                "excess": room_rent - room_limit,
                "severity": "MEDIUM"
            })
        
        # Check non-payable items
        non_payable_items = policy.get("non_payable_items", [])
        claim_items = claim.get("line_items", [])
        
        for item in claim_items:
            item_name = item.get("description", "").lower()
            for np_item in non_payable_items:
                if np_item.get("name", "").lower() in item_name:
                    gaps.append({
                        "gap_type": "Non-Payable Item",
                        "item": item.get("description"),
                        "amount": item.get("amount", 0),
                        "severity": "HIGH"
                    })
        
        return {
            "total_gaps": len(gaps),
            "gaps": gaps,
            "coverage_status": "FULL" if len(gaps) == 0 else ("PARTIAL" if len(gaps) < 3 else "LIMITED")
        }


class PolicConstraintValidator:
    """Validate claim against policy constraints"""
    
    def __init__(self, policy: Dict):
        self.policy = policy
    
    def validate_all_constraints(self, extraction: Dict) -> Dict:
        """Validate claim against all policy constraints"""
        violations = []
        warnings = []
        
        # 1. Check sum insured
        bill_total = extraction.get("bill_total", 0)
        sum_insured = self.policy.get("sum_insured", 0)
        
        if bill_total > sum_insured:
            violations.append({
                "constraint": "Sum Insured",
                "claimed": bill_total,
                "limit": sum_insured,
                "violation": f"Exceeds by ₹{bill_total - sum_insured:,.0f}",
                "severity": "CRITICAL"
            })
        
        # 2. Check room rent sublimit
        room_rent = extraction.get("room_rent_per_day", {}).get("value", 0)
        room_limit = self.policy.get("room_rent_sublimit", 0)
        
        if room_rent > room_limit:
            warnings.append({
                "constraint": "Room Rent Sublimit",
                "claimed": room_rent,
                "limit": room_limit,
                "excess": room_rent - room_limit,
                "severity": "HIGH"
            })
        
        # 3. Check waiting periods
        pre_existing = extraction.get("pre_existing_conditions", [])
        waiting_periods = self.policy.get("waiting_periods", {})
        admission_date = extraction.get("admission_date", "")
        
        for condition in pre_existing:
            if condition.lower() in waiting_periods:
                warnings.append({
                    "constraint": "Waiting Period",
                    "condition": condition,
                    "waiting_days": waiting_periods[condition.lower()],
                    "severity": "MEDIUM"
                })
        
        # 4. Check annual limit
        annual_limit = self.policy.get("annual_limit", 0)
        if annual_limit > 0 and bill_total > annual_limit:
            violations.append({
                "constraint": "Annual Limit",
                "claimed": bill_total,
                "limit": annual_limit,
                "severity": "CRITICAL"
            })
        
        # 5. Check copay
        copay_percent = self.policy.get("copay_percent", 0)
        if copay_percent > 0:
            warnings.append({
                "constraint": "Co-pay",
                "percentage": copay_percent,
                "estimated_copay": round(bill_total * copay_percent / 100, 2),
                "severity": "LOW"
            })
        
        return {
            "compliant": len(violations) == 0,
            "violations": violations,
            "warnings": warnings,
            "overall_status": "COMPLIANT" if len(violations) == 0 else "VIOLATES_CONSTRAINT"
        }
