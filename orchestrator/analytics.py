"""
Analytics and Performance Tracking for DIPLOMAT Pipeline
Tracks metrics, performance, and generates insights
"""
from typing import Dict, List, Any
from datetime import datetime, timedelta
from collections import defaultdict
import json


class PipelineAnalytics:
    """Real-time analytics for claim processing pipeline"""
    
    def __init__(self):
        self.claims_processed = 0
        self.claims_approved = 0
        self.claims_escalated = 0
        self.claims_rejected = 0
        
        self.total_bill_amount = 0.0
        self.total_approved_amount = 0.0
        self.total_deductions_applied = 0.0
        
        self.gate_pass_rate = {"G1": 0, "G2": 0}
        self.gate_bounce_count = {"G1": 0, "G2": 0}
        self.bounce_reasons = defaultdict(int)
        
        self.processing_times = []
        self.retry_distribution = defaultdict(int)
        
        self.claim_history = []
        self.started_at = datetime.now()
    
    def record_claim(self, claim_data: Dict, result: Dict, processing_time: float):
        """Record a processed claim"""
        self.claims_processed += 1
        self.processing_times.append(processing_time)
        
        # Track outcome
        status = result.get("status", "UNKNOWN")
        if status == "APPROVED":
            self.claims_approved += 1
        elif status == "ESCALATED_TO_HUMAN":
            self.claims_escalated += 1
        else:
            self.claims_rejected += 1
        
        # Track financials
        bill_total = claim_data.get("bill_total", 0)
        self.total_bill_amount += bill_total
        
        settlement = result.get("settlement", {})
        payable = settlement.get("payable", 0)
        self.total_approved_amount += payable
        
        deductions = settlement.get("total_deductions", 0)
        self.total_deductions_applied += deductions
        
        # Track bounces
        trace = result.get("trace", [])
        for step in trace:
            if "BOUNCE" in step.get("status", ""):
                if "G1_VERITAS" in step.get("step", ""):
                    self.gate_bounce_count["G1"] += 1
                elif "G2_DIPLOMAT" in step.get("step", ""):
                    self.gate_bounce_count["G2"] += 1
                
                # Track bounce reasons
                for bounce in step.get("bounces", []):
                    check = bounce.get("check", "UNKNOWN")
                    self.bounce_reasons[check] += 1
        
        # Track retry attempts
        attempt_count = max([int(s.get("status", "ATTEMPT_1").split("_")[-1]) 
                           for s in trace if "ATTEMPT" in s.get("status", "")] + [1])
        self.retry_distribution[attempt_count] += 1
        
        # Store claim record
        self.claim_history.append({
            "timestamp": datetime.now().isoformat(),
            "status": status,
            "bill_total": bill_total,
            "payable": payable,
            "deductions": deductions,
            "processing_time": processing_time,
            "retries": attempt_count
        })
    
    def get_summary(self) -> Dict:
        """Get comprehensive analytics summary"""
        runtime = (datetime.now() - self.started_at).total_seconds()
        
        approval_rate = (self.claims_approved / self.claims_processed * 100) if self.claims_processed > 0 else 0
        escalation_rate = (self.claims_escalated / self.claims_processed * 100) if self.claims_processed > 0 else 0
        rejection_rate = (self.claims_rejected / self.claims_processed * 100) if self.claims_processed > 0 else 0
        
        avg_processing_time = (sum(self.processing_times) / len(self.processing_times)) if self.processing_times else 0
        
        deduction_rate = (self.total_deductions_applied / self.total_bill_amount * 100) if self.total_bill_amount > 0 else 0
        
        # Calculate gate pass rates
        total_gates = sum(self.gate_bounce_count.values()) + self.claims_approved * 2
        g1_pass_rate = ((self.claims_approved + self.claims_escalated) / (self.claims_processed or 1) * 100)
        g2_pass_rate = ((self.claims_approved) / (self.claims_processed or 1) * 100)
        
        return {
            "summary": {
                "total_claims_processed": self.claims_processed,
                "runtime_seconds": round(runtime, 2),
                "claims_per_minute": round(self.claims_processed / (runtime / 60), 2) if runtime > 0 else 0
            },
            "outcomes": {
                "approved": self.claims_approved,
                "escalated_to_human": self.claims_escalated,
                "rejected": self.claims_rejected,
                "approval_rate_percent": round(approval_rate, 2),
                "escalation_rate_percent": round(escalation_rate, 2),
                "rejection_rate_percent": round(rejection_rate, 2)
            },
            "financials": {
                "total_bill_amount": round(self.total_bill_amount, 2),
                "total_approved_payout": round(self.total_approved_amount, 2),
                "total_deductions": round(self.total_deductions_applied, 2),
                "deduction_rate_percent": round(deduction_rate, 2),
                "average_claim_value": round(self.total_bill_amount / (self.claims_processed or 1), 2)
            },
            "gates": {
                "G1_VERITAS": {
                    "total_bounces": self.gate_bounce_count["G1"],
                    "pass_rate_percent": round(g1_pass_rate, 2)
                },
                "G2_DIPLOMAT": {
                    "total_bounces": self.gate_bounce_count["G2"],
                    "pass_rate_percent": round(g2_pass_rate, 2)
                }
            },
            "bounce_analysis": {
                "top_issues": sorted(
                    [(k, v) for k, v in self.bounce_reasons.items()],
                    key=lambda x: x[1],
                    reverse=True
                )[:5],
                "total_bounces": sum(self.bounce_reasons.values())
            },
            "performance": {
                "avg_processing_time_ms": round(avg_processing_time * 1000, 2),
                "min_processing_time_ms": round(min(self.processing_times) * 1000, 2) if self.processing_times else 0,
                "max_processing_time_ms": round(max(self.processing_times) * 1000, 2) if self.processing_times else 0,
                "retry_distribution": dict(sorted(self.retry_distribution.items()))
            }
        }
    
    def get_fraud_insights(self) -> Dict:
        """Generate fraud detection insights from processed claims"""
        if not self.claim_history:
            return {"message": "No claims processed yet"}
        
        high_value = [c for c in self.claim_history if c["bill_total"] > 500000]
        high_deduction = [c for c in self.claim_history if c["deductions"] > c["bill_total"] * 0.4]
        quick_claims = [c for c in self.claim_history if c["processing_time"] < 0.5]
        
        return {
            "high_value_claims": len(high_value),
            "high_value_total": round(sum(c["bill_total"] for c in high_value), 2),
            "high_deduction_claims": len(high_deduction),
            "fast_processed_claims": len(quick_claims),
            "average_deduction_rate": round(
                (self.total_deductions_applied / self.total_bill_amount * 100) if self.total_bill_amount > 0 else 0,
                2
            )
        }
    
    def export_metrics(self) -> str:
        """Export all metrics as JSON"""
        return json.dumps({
            "timestamp": datetime.now().isoformat(),
            "summary": self.get_summary(),
            "fraud_insights": self.get_fraud_insights(),
            "claim_history": self.claim_history[-100:]  # Last 100 claims
        }, indent=2)


class ClaimComparator:
    """Compare current claim with policy benchmarks and historical data"""
    
    def __init__(self, policy: Dict, historical_claims: List[Dict] = None):
        self.policy = policy
        self.historical_claims = historical_claims or []
    
    def compare_to_similar(self, current_claim: Dict, field: str = "bill_total") -> Dict:
        """Compare current claim to similar claims"""
        diagnosis = current_claim.get("diagnosis", "")
        procedure = current_claim.get("procedure", "")
        
        similar = [
            c for c in self.historical_claims
            if (diagnosis and diagnosis.lower() in c.get("diagnosis", "").lower()) or
               (procedure and procedure.lower() in c.get("procedure", "").lower())
        ]
        
        if not similar:
            return {"similar_count": 0, "comparison": "No similar claims"}
        
        current_value = current_claim.get(field, 0)
        similar_values = [c.get(field, 0) for c in similar if c.get(field, 0) > 0]
        
        if not similar_values:
            return {"similar_count": len(similar), "comparison": f"No {field} data"}
        
        avg_similar = sum(similar_values) / len(similar_values)
        percentile = (len([v for v in similar_values if v < current_value]) / len(similar_values)) * 100
        
        return {
            "similar_count": len(similar),
            "current_value": current_value,
            "average_similar": round(avg_similar, 2),
            "min": min(similar_values),
            "max": max(similar_values),
            "percentile": round(percentile, 1),
            "deviation_percent": round(((current_value - avg_similar) / avg_similar * 100) if avg_similar else 0, 2)
        }
    
    def policy_compliance_check(self, extraction: Dict) -> Dict:
        """Check if claim complies with policy terms"""
        issues = []
        warnings = []
        
        # Check room rent sublimit
        room_rent = extraction.get("room_rent_per_day", {}).get("value", 0)
        room_limit = self.policy.get("room_rent_sublimit", 0)
        
        if room_rent > room_limit:
            issues.append({
                "issue": "Room rent exceeds policy sublimit",
                "policy_limit": room_limit,
                "actual": room_rent,
                "excess": room_rent - room_limit,
                "severity": "HIGH"
            })
        
        # Check waiting periods
        pre_existing = extraction.get("pre_existing_conditions", [])
        waiting_periods = self.policy.get("waiting_periods", {})
        
        for condition in pre_existing:
            if condition.lower() in waiting_periods:
                warnings.append({
                    "warning": f"Pre-existing condition '{condition}' subject to waiting period",
                    "waiting_days": waiting_periods[condition.lower()],
                    "severity": "MEDIUM"
                })
        
        # Check policy coverage limits
        sum_insured = self.policy.get("sum_insured", 0)
        bill_total = extraction.get("bill_total", 0)
        
        if bill_total > sum_insured:
            issues.append({
                "issue": "Claim exceeds policy sum insured",
                "sum_insured": sum_insured,
                "claim_amount": bill_total,
                "excess": bill_total - sum_insured,
                "severity": "CRITICAL"
            })
        
        return {
            "compliant": len(issues) == 0,
            "issues": issues,
            "warnings": warnings
        }
