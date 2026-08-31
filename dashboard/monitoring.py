"""
Real-time Monitoring and Alerting System
Tracks system health, performance anomalies, and suspicious patterns
"""
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from collections import deque


class RealTimeMonitor:
    """Real-time system monitoring and alerting"""
    
    def __init__(self, window_size: int = 100):
        self.window_size = window_size
        self.claims_window = deque(maxlen=window_size)
        self.alerts = []
        self.thresholds = {
            "high_error_rate": 0.1,  # 10%
            "high_fraud_risk_rate": 0.2,  # 20%
            "low_throughput": 10,  # claims per minute
            "high_processing_time": 5000,  # ms
            "unusual_payout_rate": 0.9  # 90%
        }
    
    def record_claim(self, claim_result: Dict):
        """Record a processed claim and check for anomalies"""
        self.claims_window.append(claim_result)
        self._check_anomalies()
    
    def _check_anomalies(self):
        """Check for anomalies in recent claims"""
        if len(self.claims_window) < 5:
            return
        
        recent = list(self.claims_window)[-10:]
        
        # Check error rate
        errors = len([c for c in recent if c.get("status") == "FAILED"])
        error_rate = errors / len(recent)
        if error_rate > self.thresholds["high_error_rate"]:
            self._create_alert("HIGH_ERROR_RATE", f"Error rate {error_rate*100:.1f}%", "HIGH")
        
        # Check fraud risk
        high_risk = len([c for c in recent if c.get("fraud_analysis", {}).get("risk_level") == "HIGH"])
        high_risk_rate = high_risk / len(recent)
        if high_risk_rate > self.thresholds["high_fraud_risk_rate"]:
            self._create_alert("FRAUD_SPIKE", f"{high_risk} high-risk claims in last 10", "MEDIUM")
        
        # Check processing time
        processing_times = [c.get("processing_time", 0) for c in recent]
        avg_time = sum(processing_times) / len(processing_times) if processing_times else 0
        if avg_time * 1000 > self.thresholds["high_processing_time"]:
            self._create_alert("SLOW_PROCESSING", f"Avg time {avg_time*1000:.0f}ms", "MEDIUM")
        
        # Check payout rate
        approved = len([c for c in recent if c.get("status") == "APPROVED"])
        payout_rate = approved / len(recent) if recent else 0
        if payout_rate > self.thresholds["unusual_payout_rate"]:
            self._create_alert("UNUSUAL_PAYOUT", f"Payout rate {payout_rate*100:.1f}%", "LOW")
    
    def _create_alert(self, alert_type: str, message: str, severity: str):
        """Create an alert"""
        alert = {
            "timestamp": datetime.now().isoformat(),
            "type": alert_type,
            "message": message,
            "severity": severity
        }
        self.alerts.append(alert)
        
        # Keep only last 50 alerts
        if len(self.alerts) > 50:
            self.alerts = self.alerts[-50:]
    
    def get_active_alerts(self, severity: str = None) -> List[Dict]:
        """Get active alerts"""
        if severity:
            return [a for a in self.alerts if a["severity"] == severity]
        return self.alerts
    
    def get_system_health(self) -> Dict:
        """Get overall system health status"""
        if not self.claims_window:
            return {"status": "IDLE", "health_percent": 100}
        
        recent = list(self.claims_window)[-20:]
        
        # Calculate health score
        health = 100.0
        
        # Deduct for errors
        error_rate = len([c for c in recent if c.get("status") == "FAILED"]) / len(recent)
        health -= error_rate * 20
        
        # Deduct for high fraud
        high_fraud_rate = len([c for c in recent if c.get("fraud_analysis", {}).get("risk_level") in ["HIGH", "MEDIUM"]]) / len(recent)
        health -= high_fraud_rate * 15
        
        # Deduct for slow processing
        avg_time = sum([c.get("processing_time", 0) for c in recent]) / len(recent)
        if avg_time > 2:
            health -= (avg_time - 2) * 5
        
        health = max(0, min(100, health))
        
        status = "HEALTHY" if health > 80 else ("DEGRADED" if health > 50 else "CRITICAL")
        
        return {
            "status": status,
            "health_percent": round(health, 1),
            "active_alerts": len(self.alerts)
        }


class PerformanceProfiler:
    """Profile and analyze performance metrics"""
    
    def __init__(self):
        self.gate_timings = {"G1": [], "G2": []}
        self.agent_timings = {"A1": [], "A2": [], "A3": []}
        self.total_timings = []
    
    def record_timings(self, trace: List[Dict], total_time: float):
        """Record timing information from trace"""
        self.total_timings.append(total_time)
        
        for step in trace:
            step_name = step.get("step", "")
            if "timing_ms" in step:
                timing = step["timing_ms"]
                if step_name.startswith("G"):
                    gate = step_name.split("_")[0]
                    self.gate_timings[gate].append(timing)
                elif step_name.startswith("A"):
                    agent = step_name.split("_")[0]
                    self.agent_timings[agent].append(timing)
    
    def get_performance_report(self) -> Dict:
        """Generate performance report"""
        def calc_stats(timings):
            if not timings:
                return {}
            return {
                "count": len(timings),
                "avg_ms": round(sum(timings) / len(timings), 2),
                "min_ms": round(min(timings), 2),
                "max_ms": round(max(timings), 2),
                "total_ms": round(sum(timings), 2)
            }
        
        return {
            "gates": {
                "G1_VERITAS": calc_stats(self.gate_timings["G1"]),
                "G2_DIPLOMAT": calc_stats(self.gate_timings["G2"])
            },
            "agents": {
                "A1_INTAKE": calc_stats(self.agent_timings["A1"]),
                "A2_POLICY": calc_stats(self.agent_timings["A2"]),
                "A3_ADJUDICATOR": calc_stats(self.agent_timings["A3"])
            },
            "overall": calc_stats(self.total_timings)
        }


class AnomalyDetector:
    """Detect anomalous patterns in claims"""
    
    def __init__(self, historical_baseline: List[Dict] = None):
        self.baseline = historical_baseline or []
        self.anomalies = []
    
    def detect_anomalies(self, claim: Dict) -> Dict:
        """Detect various anomalies in a claim"""
        anomalies = []
        scores = {}
        
        # 1. Statistical outlier detection
        bill_total = claim.get("bill_total", 0)
        if self.baseline:
            baseline_bills = [c.get("bill_total", 0) for c in self.baseline if c.get("bill_total", 0) > 0]
            if baseline_bills:
                mean_bill = sum(baseline_bills) / len(baseline_bills)
                std_bill = (sum((x - mean_bill)**2 for x in baseline_bills) / len(baseline_bills))**0.5
                
                if std_bill > 0:
                    z_score = abs((bill_total - mean_bill) / std_bill)
                    scores["bill_outlier_z"] = z_score
                    if z_score > 3:
                        anomalies.append({
                            "type": "Statistical Outlier",
                            "description": f"Bill amount is {z_score:.1f}σ from baseline",
                            "severity": "HIGH"
                        })
        
        # 2. Pattern detection
        line_items = claim.get("line_items", [])
        item_names = [i.get("description", "") for i in line_items]
        
        # Check for suspicious patterns
        if len(item_names) > 15:
            anomalies.append({
                "type": "Unusual Item Count",
                "description": f"{len(item_names)} line items (unusual)",
                "severity": "LOW"
            })
        
        # 3. Duplicate detection
        duplicates = len(item_names) - len(set(item_names))
        if duplicates > 3:
            anomalies.append({
                "type": "Duplicate Items",
                "description": f"{duplicates} duplicate line items detected",
                "severity": "MEDIUM"
            })
        
        # 4. Procedure complexity
        surgeries = [i for i in line_items if i.get("category") == "surgery"]
        if len(surgeries) > 3:
            anomalies.append({
                "type": "Complex Procedure",
                "description": f"{len(surgeries)} surgical procedures in single claim",
                "severity": "MEDIUM"
            })
        
        return {
            "anomaly_count": len(anomalies),
            "anomalies": anomalies,
            "anomaly_scores": scores,
            "risk_level": "HIGH" if len(anomalies) > 3 else ("MEDIUM" if len(anomalies) > 1 else "LOW")
        }
