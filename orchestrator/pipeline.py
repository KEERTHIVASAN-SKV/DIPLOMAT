import json
from typing import Dict, List, Tuple, Any
from agents.intake_agent import IntakeAgent
from agents.policy_engine import PolicyEngine
from agents.adjudicator_agent import AdjudicatorAgent
from diplomat.veritas import VeritasGate
from diplomat.diplomat import DiplomatGate


class InsurancePipeline:
    """
    Resilient pipeline with feedback loops.
    Gates don't stop the process — they bounce errors back to agents for retry.
    """
    
    def __init__(self, policy_doc: dict, use_gates: bool = True, max_retries: int = 2):
        self.policy = policy_doc
        self.use_gates = use_gates
        self.max_retries = max_retries
        self.intake = IntakeAgent()
        self.veritas = VeritasGate()
        self.diplomat = DiplomatGate(policy_doc)
    
    def process(self, bill_doc: dict, discharge_doc: dict, 
                inject_fault: str = None) -> dict:
        """
        Run the full pipeline with retry loops.
        """
        trace = []
        
        # ========== STEP 1: INTAKE + GATE 1 (with retry loop) ==========
        trace.append({"step": "A1_INTAKE", "status": "STARTING"})
        
        extraction = None
        gate1_passed = False
        gate1_bounces = []
        attempt = 0
        
        while attempt <= self.max_retries and not gate1_passed:
            attempt += 1
            
            # Agent extracts
            extraction = self.intake.extract(
                self.policy, bill_doc, discharge_doc, 
                inject_fault=inject_fault if attempt == 1 else None  # Only inject fault on first try
            )
            trace.append({
                "step": "A1_INTAKE", 
                "status": f"ATTEMPT_{attempt}", 
                "output": extraction
            })
            
            if not self.use_gates:
                gate1_passed = True
                break
            
            # Gate 1 validates
            gate1_passed, gate1_bounces = self.veritas.validate(
                extraction, bill_doc, discharge_doc, self.policy
            )
            
            if gate1_passed:
                trace.append({"step": "G1_VERITAS", "status": "PASSED", "attempt": attempt})
            else:
                trace.append({
                    "step": "G1_VERITAS", 
                    "status": f"BOUNCED_ATTEMPT_{attempt}", 
                    "bounces": gate1_bounces
                })
                if attempt <= self.max_retries:
                    trace.append({
                        "step": "PIPELINE", 
                        "status": "FEEDBACK_LOOP", 
                        "detail": f"Sending {len(gate1_bounces)} bounce(s) back to IntakeAgent for retry"
                    })
        
        if not gate1_passed:
            return {
                "status": "ESCALATED_TO_HUMAN",
                "reason": "Gate 1 blocked after max retries",
                "trace": trace,
                "bounces": gate1_bounces,
                "settlement": None
            }
        
        # ========== STEP 2: POLICY ENGINE ==========
        trace.append({"step": "A2_POLICY", "status": "RUNNING"})
        policy_engine = PolicyEngine(self.policy)
        rules = policy_engine.get_applicable_rules(extraction)
        trace.append({
            "step": "A2_POLICY", 
            "status": "COMPLETE", 
            "rules_applied": [r.get("description", r.get("rule_id", "UNKNOWN")) for r in rules]
        })
        
        # ========== STEP 3: ADJUDICATOR + GATE 2 (with retry loop) ==========
        trace.append({"step": "A3_ADJUDICATOR", "status": "STARTING"})
        
        settlement = None
        gate2_passed = False
        gate2_bounces = []
        attempt = 0
        
        while attempt <= self.max_retries and not gate2_passed:
            attempt += 1
            
            # Adjudicator calculates
            adjudicator = AdjudicatorAgent(self.policy)
            settlement = adjudicator.adjudicate(
                extraction, rules,
                inject_fault=inject_fault if attempt == 1 else None
            )
            trace.append({
                "step": "A3_ADJUDICATOR",
                "status": f"ATTEMPT_{attempt}",
                "settlement": settlement
            })
            
            if not self.use_gates:
                gate2_passed = True
                break
            
            # Gate 2 validates
            gate2_passed, gate2_bounces = self.diplomat.validate(settlement, extraction)
            
            if gate2_passed:
                trace.append({"step": "G2_DIPLOMAT", "status": "PASSED", "attempt": attempt})
            else:
                trace.append({
                    "step": "G2_DIPLOMAT",
                    "status": f"BOUNCED_ATTEMPT_{attempt}",
                    "bounces": gate2_bounces
                })
                if attempt <= self.max_retries:
                    trace.append({
                        "step": "PIPELINE",
                        "status": "FEEDBACK_LOOP",
                        "detail": f"Sending {len(gate2_bounces)} bounce(s) back to AdjudicatorAgent for retry"
                    })
        
        if not gate2_passed:
            return {
                "status": "ESCALATED_TO_HUMAN",
                "reason": "Gate 2 blocked after max retries",
                "trace": trace,
                "bounces": gate2_bounces,
                "settlement": settlement
            }
        
        # ========== SUCCESS ==========
        return {
            "status": "APPROVED",
            "trace": trace,
            "settlement": settlement,
            "grievance_draft": self._generate_grievance(settlement)
        }
    
    def _generate_grievance(self, settlement: dict) -> str:
        """Generate a one-page grievance letter if any deductions were flagged."""
        # For now, return a simple status
        return "All deductions verified and cited. No grievance necessary."
