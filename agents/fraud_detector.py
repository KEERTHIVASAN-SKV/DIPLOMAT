"""
Fraud Detection and Risk Scoring Engine
Analyzes claims for suspicious patterns and anomalies
"""
from typing import Dict, List, Tuple
import math


class FraudDetector:
    """Advanced fraud detection with risk scoring"""
    
    # Risk thresholds
    RISK_THRESHOLDS = {
        "LOW": 0.3,
        "MEDIUM": 0.6,
        "HIGH": 0.8,
    }
    
    def __init__(self, historical_claims: List[Dict] = None):
        self.historical_claims = historical_claims or []
        self.risk_scores = {}
    
    def analyze_claim(self, extraction: Dict, settlement: Dict, policy: Dict) -> Dict:
        """
        Comprehensive fraud analysis with multiple risk factors
        
        Returns:
            {
                "risk_level": "LOW|MEDIUM|HIGH",
                "risk_score": 0.0-1.0,
                "risk_factors": [...],
                "anomalies": [...],
                "red_flags": [],
                "confidence": 0.0-1.0,
                "recommendation": "APPROVE|REVIEW|REJECT"
            }
        """
        risk_score = 0.0
        risk_factors = []
        anomalies = []
        red_flags = []
        
        # === FACTOR 1: Bill Amount Anomaly ===
        bill_total = extraction.get("bill_total", 0)
        avg_bill, std_bill = self._get_stats("bill_total")
        
        if avg_bill > 0:
            z_score = abs((bill_total - avg_bill) / (std_bill or 1))
            if z_score > 2.5:
                factor_score = min(0.25, z_score / 10)
                risk_score += factor_score
                risk_factors.append({
                    "factor": "Unusual Bill Amount",
                    "score": factor_score,
                    "details": f"Amount ₹{bill_total:,.0f} is {z_score:.1f}σ from average",
                    "severity": "HIGH" if z_score > 3 else "MEDIUM"
                })
                anomalies.append(f"Bill amount {z_score:.1f} standard deviations above average")
        
        # === FACTOR 2: Length of Stay Anomaly ===
        los = extraction.get("length_of_stay", {}).get("value", 0)
        avg_los, std_los = self._get_stats("length_of_stay")
        
        if los > 0 and avg_los > 0:
            los_z = abs((los - avg_los) / (std_los or 1))
            if los_z > 2.0:
                factor_score = min(0.15, los_z / 15)
                risk_score += factor_score
                risk_factors.append({
                    "factor": "Unusual Length of Stay",
                    "score": factor_score,
                    "details": f"LOS {los} days is {los_z:.1f}σ from average",
                    "severity": "MEDIUM"
                })
        
        # === FACTOR 3: High Non-Payable Ratio ===
        line_items = extraction.get("line_items", [])
        non_payable_sum = sum(
            item.get("amount", 0) for item in line_items 
            if item.get("category") == "non_payable"
        )
        
        if bill_total > 0:
            non_payable_ratio = non_payable_sum / bill_total
            if non_payable_ratio > 0.15:
                factor_score = min(0.2, non_payable_ratio / 0.3)
                risk_score += factor_score
                risk_factors.append({
                    "factor": "High Non-Payable Ratio",
                    "score": factor_score,
                    "details": f"Non-payable items are {non_payable_ratio*100:.1f}% of bill",
                    "severity": "MEDIUM"
                })
                if non_payable_ratio > 0.25:
                    red_flags.append("Non-payable items exceed 25% of bill")
        
        # === FACTOR 4: Multiple High-Cost Procedures ===
        surgery_items = [i for i in line_items if i.get("category") == "surgery"]
        high_cost_surgery = [i for i in surgery_items if i.get("amount", 0) > 150000]
        
        if len(high_cost_surgery) > 1:
            factor_score = min(0.2, len(high_cost_surgery) * 0.1)
            risk_score += factor_score
            risk_factors.append({
                "factor": "Multiple High-Cost Procedures",
                "score": factor_score,
                "details": f"{len(high_cost_surgery)} high-cost procedures in single stay",
                "severity": "HIGH"
            })
            red_flags.append(f"Multiple procedures exceeding ₹150K in single claim")
        
        # === FACTOR 5: Room Rent vs Procedure Mismatch ===
        room_rent_total = extraction.get("room_rent_total", {})
        if isinstance(room_rent_total, dict):
            room_rent = room_rent_total.get("value", 0)
        else:
            room_rent = room_rent_total if isinstance(room_rent_total, (int, float)) else 0
        
        total_procedures = sum(i.get("amount", 0) for i in surgery_items)
        
        if total_procedures > 0:
            room_ratio = room_rent / total_procedures
            if room_ratio > 0.5:
                factor_score = min(0.15, (room_ratio - 0.3) / 0.4)
                risk_score += factor_score
                risk_factors.append({
                    "factor": "Disproportionate Room Rent",
                    "score": factor_score,
                    "details": f"Room rent is {room_ratio*100:.1f}% of procedure costs",
                    "severity": "MEDIUM"
                })
        
        # === FACTOR 6: Duplicate/Suspicious Item Names ===
        item_descriptions = [i.get("description", "").lower() for i in line_items]
        item_counts = {}
        for desc in item_descriptions:
            item_counts[desc] = item_counts.get(desc, 0) + 1
        
        duplicates = [desc for desc, count in item_counts.items() if count > 2]
        if duplicates:
            factor_score = min(0.15, len(duplicates) * 0.08)
            risk_score += factor_score
            risk_factors.append({
                "factor": "Duplicate Line Items",
                "score": factor_score,
                "details": f"{len(duplicates)} items appear 3+ times",
                "severity": "HIGH"
            })
            red_flags.extend([f"Duplicate item: {d}" for d in duplicates[:3]])
        
        # === FACTOR 7: Deduction Rate Anomaly ===
        total_deductions = settlement.get("total_deductions", 0)
        if bill_total > 0:
            deduction_rate = total_deductions / bill_total
            avg_ded_rate, _ = self._get_stats("deduction_rate")
            
            if avg_ded_rate > 0:
                ded_z = abs((deduction_rate - avg_ded_rate) / (avg_ded_rate * 0.2 + 0.01))
                if ded_z > 2.0:
                    factor_score = min(0.15, ded_z / 15)
                    risk_score += factor_score
                    risk_factors.append({
                        "factor": "Unusual Deduction Rate",
                        "score": factor_score,
                        "details": f"Deduction rate {deduction_rate*100:.1f}% is {ded_z:.1f}σ from expected",
                        "severity": "MEDIUM"
                    })
        
        # === FACTOR 8: Policy Limit Exploitation ===
        policy_limits = policy.get("sum_insured", 0)
        if policy_limits > 0:
            utilization = bill_total / policy_limits
            if utilization > 0.9:
                factor_score = 0.1 * min(1.0, (utilization - 0.9) / 0.1)
                risk_score += factor_score
                risk_factors.append({
                    "factor": "High Policy Limit Utilization",
                    "score": factor_score,
                    "details": f"Claim uses {utilization*100:.1f}% of policy limit",
                    "severity": "MEDIUM"
                })
        
        # === Normalize Risk Score ===
        risk_score = min(1.0, risk_score)
        
        # === Determine Risk Level ===
        risk_level = "LOW"
        if risk_score >= self.RISK_THRESHOLDS["HIGH"]:
            risk_level = "HIGH"
        elif risk_score >= self.RISK_THRESHOLDS["MEDIUM"]:
            risk_level = "MEDIUM"
        
        # === Calculate Confidence ===
        confidence = 0.7 + (len(risk_factors) * 0.05)
        confidence = min(0.99, confidence)
        
        # === Recommendation ===
        if risk_level == "HIGH" or len(red_flags) > 3:
            recommendation = "REJECT" if risk_score > 0.9 else "REVIEW"
        elif risk_level == "MEDIUM":
            recommendation = "REVIEW" if risk_score > 0.65 else "APPROVE"
        else:
            recommendation = "APPROVE"
        
        return {
            "risk_level": risk_level,
            "risk_score": round(risk_score, 3),
            "risk_factors": risk_factors,
            "anomalies": anomalies,
            "red_flags": red_flags,
            "confidence": round(confidence, 3),
            "recommendation": recommendation,
            "details": {
                "bill_total": bill_total,
                "total_deductions": total_deductions,
                "policy_utilization": f"{(bill_total/policy_limits*100):.1f}%" if policy_limits else "N/A"
            }
        }
    
    def _get_stats(self, field: str) -> Tuple[float, float]:
        """Calculate mean and std dev for a field from historical claims"""
        if not self.historical_claims:
            return (0, 0)
        
        values = []
        for claim in self.historical_claims:
            if field == "bill_total":
                val = claim.get("bill_total", 0)
            elif field == "length_of_stay":
                val = claim.get("discharge_date", "") - claim.get("admission_date", "")
            elif field == "deduction_rate":
                total = claim.get("bill_total", 1)
                ded = claim.get("total_deductions", 0)
                val = ded / total if total > 0 else 0
            else:
                continue
            
            if isinstance(val, (int, float)) and val > 0:
                values.append(val)
        
        if not values:
            return (0, 0)
        
        mean = sum(values) / len(values)
        variance = sum((x - mean) ** 2 for x in values) / len(values)
        std_dev = math.sqrt(variance)
        
        return (mean, std_dev)
    
    def get_comparative_analysis(self, claim: Dict, comparison_claims: List[Dict]) -> Dict:
        """Compare current claim with similar historical claims"""
        bill_total = claim.get("bill_total", 0)
        diagnosis = claim.get("diagnosis", "").lower()
        
        similar = [
            c for c in comparison_claims
            if diagnosis in c.get("diagnosis", "").lower() or
               0.8 < c.get("bill_total", 0) / (bill_total or 1) < 1.2
        ]
        
        if not similar:
            return {"similar_claims": 0, "analysis": "No similar claims found"}
        
        bills = [c.get("bill_total", 0) for c in similar]
        avg_bill = sum(bills) / len(bills) if bills else 0
        
        return {
            "similar_claims": len(similar),
            "average_bill": round(avg_bill, 2),
            "percentile": f"{(len([b for b in bills if b < bill_total])/len(bills)*100):.0f}th",
            "range": f"₹{min(bills):,.0f} - ₹{max(bills):,.0f}",
            "current_bill": bill_total
        }
