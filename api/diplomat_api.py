"""
DIPLOMAT REST API
Enterprise API for claim processing, fraud detection, and analytics
"""
from typing import Dict, List, Optional
from datetime import datetime
import json


class DiplomatAPI:
    """RESTful API interface for DIPLOMAT"""
    
    def __init__(self, pipeline, fraud_detector, analytics):
        self.pipeline = pipeline
        self.fraud_detector = fraud_detector
        self.analytics = analytics
        self.request_log = []
    
    # ========== Claims Processing ==========
    
    def process_claim(self, claim_data: Dict, metadata: Dict = None) -> Dict:
        """
        Process a single claim
        
        Request:
        {
            "bill": {...},
            "discharge": {...},
            "policy": {...},
            "metadata": {"request_id": "...", "user": "..."}
        }
        """
        request_id = metadata.get("request_id") if metadata else None
        
        try:
            bill = claim_data.get("bill")
            discharge = claim_data.get("discharge")
            policy = claim_data.get("policy", self.pipeline.policy)
            
            # Process through pipeline
            result = self.pipeline.process(bill, discharge)
            
            # Add fraud analysis
            fraud_analysis = self.fraud_detector.analyze_claim(bill, result.get("settlement", {}), policy)
            
            # Add analytics
            self.analytics.record_claim(bill, result, 0)
            
            response = {
                "request_id": request_id,
                "status": "SUCCESS",
                "timestamp": datetime.now().isoformat(),
                "result": result,
                "fraud_analysis": fraud_analysis
            }
            
            self._log_request("process_claim", "SUCCESS", request_id)
            return response
            
        except Exception as e:
            self._log_request("process_claim", "FAILED", request_id, str(e))
            return {
                "request_id": request_id,
                "status": "ERROR",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def process_claims_batch(self, claims: List[Dict], parallel: bool = False) -> Dict:
        """Process multiple claims"""
        from orchestrator.batch_processor import BatchProcessor
        
        processor = BatchProcessor()
        
        def process_fn(claim):
            return self.pipeline.process(claim.get("bill"), claim.get("discharge"))
        
        batch_result = processor.process_batch(claims, process_fn, parallel=parallel)
        
        return {
            "status": "SUCCESS",
            "timestamp": datetime.now().isoformat(),
            "batch_result": batch_result
        }
    
    # ========== Fraud Analysis ==========
    
    def analyze_fraud_risk(self, claim_data: Dict, policy: Dict = None) -> Dict:
        """
        Analyze fraud risk for a claim
        
        Request:
        {
            "bill": {...},
            "discharge": {...}
        }
        """
        try:
            bill = claim_data.get("bill")
            policy = policy or self.pipeline.policy
            
            fraud_analysis = self.fraud_detector.analyze_claim(bill, {}, policy)
            
            return {
                "status": "SUCCESS",
                "fraud_analysis": fraud_analysis,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            return {
                "status": "ERROR",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    # ========== Policy Operations ==========
    
    def validate_policy_compliance(self, extraction: Dict, policy: Dict) -> Dict:
        """Check if claim complies with policy"""
        from agents.policy_selector import PolicConstraintValidator
        
        try:
            validator = PolicConstraintValidator(policy)
            compliance = validator.validate_all_constraints(extraction)
            
            return {
                "status": "SUCCESS",
                "compliance": compliance,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            return {
                "status": "ERROR",
                "error": str(e)
            }
    
    def compare_policies(self, claim: Dict, policies: List[Dict]) -> Dict:
        """Compare multiple policies for a claim"""
        from agents.policy_selector import PolicyComparator
        
        try:
            comparison = PolicyComparator.compare_coverage(policies, claim)
            
            return {
                "status": "SUCCESS",
                "comparison": comparison,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            return {
                "status": "ERROR",
                "error": str(e)
            }
    
    # ========== Analytics ==========
    
    def get_analytics_summary(self) -> Dict:
        """Get current analytics summary"""
        try:
            summary = self.analytics.get_summary()
            fraud_insights = self.analytics.get_fraud_insights()
            
            return {
                "status": "SUCCESS",
                "analytics": summary,
                "fraud_insights": fraud_insights,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            return {
                "status": "ERROR",
                "error": str(e)
            }
    
    def get_performance_metrics(self) -> Dict:
        """Get performance metrics"""
        return {
            "status": "SUCCESS",
            "metrics": self.analytics.get_summary()["performance"],
            "timestamp": datetime.now().isoformat()
        }
    
    # ========== System ==========
    
    def get_health_status(self) -> Dict:
        """Get system health status"""
        return {
            "status": "HEALTHY",
            "service": "DIPLOMAT v2",
            "claims_processed": self.analytics.claims_processed,
            "approval_rate": f"{(self.analytics.claims_approved/self.analytics.claims_processed*100):.1f}%" if self.analytics.claims_processed > 0 else "N/A",
            "timestamp": datetime.now().isoformat()
        }
    
    def _log_request(self, endpoint: str, status: str, request_id: str = None, error: str = None):
        """Log API request"""
        self.request_log.append({
            "timestamp": datetime.now().isoformat(),
            "endpoint": endpoint,
            "status": status,
            "request_id": request_id,
            "error": error
        })
        
        # Keep only last 1000 requests
        if len(self.request_log) > 1000:
            self.request_log = self.request_log[-1000:]


class GraphQLInterface:
    """GraphQL interface for DIPLOMAT"""
    
    def __init__(self, api: DiplomatAPI):
        self.api = api
    
    def execute_query(self, query: str, variables: Dict = None) -> Dict:
        """Execute GraphQL query"""
        # Simple query parser
        variables = variables or {}
        
        if "processClaim" in query:
            return self._process_claim_query(variables)
        elif "getAnalytics" in query:
            return self._get_analytics_query(variables)
        elif "analyzeFraud" in query:
            return self._analyze_fraud_query(variables)
        else:
            return {"error": "Unknown query"}
    
    def _process_claim_query(self, variables: Dict) -> Dict:
        """Process claim query"""
        return self.api.process_claim(variables)
    
    def _get_analytics_query(self, variables: Dict) -> Dict:
        """Get analytics query"""
        return self.api.get_analytics_summary()
    
    def _analyze_fraud_query(self, variables: Dict) -> Dict:
        """Analyze fraud query"""
        return self.api.analyze_fraud_risk(variables)


class WebhookManager:
    """Manage webhooks for event notifications"""
    
    def __init__(self):
        self.webhooks = {}
        self.events = []
    
    def register_webhook(self, event_type: str, url: str, auth_token: str = None) -> Dict:
        """Register a webhook"""
        webhook_id = f"webhook_{len(self.webhooks)+1}"
        self.webhooks[webhook_id] = {
            "event_type": event_type,
            "url": url,
            "auth_token": auth_token,
            "created_at": datetime.now().isoformat(),
            "active": True
        }
        return {"webhook_id": webhook_id, "status": "REGISTERED"}
    
    def trigger_webhook(self, event_type: str, data: Dict):
        """Trigger webhook events"""
        event = {
            "timestamp": datetime.now().isoformat(),
            "event_type": event_type,
            "data": data
        }
        self.events.append(event)
        
        # In production, would call registered webhooks here
        for webhook_id, webhook in self.webhooks.items():
            if webhook["event_type"] == event_type and webhook["active"]:
                # Would POST to webhook["url"] with event data
                pass
    
    def get_webhook_history(self, event_type: str = None) -> List[Dict]:
        """Get webhook event history"""
        if event_type:
            return [e for e in self.events if e["event_type"] == event_type]
        return self.events
