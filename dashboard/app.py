"""
DIPLOMAT Dashboard
==================
Streamlit-based visual demo of the DIPLOMAT insurance pipeline.
Real, working pipeline using InsurancePipeline.process(bill, discharge, inject_fault=...).

Run with:
    streamlit run dashboard/app.py
"""
import json
import sys
from pathlib import Path

import streamlit as st

# Add project root to path
ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

from orchestrator.pipeline import InsurancePipeline


def load_json(path: str) -> dict:
    with open(path, encoding='utf-8') as f:
        return json.load(f)


# ── Page Config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="DIPLOMAT — Insurance AI Gateway",
    page_icon="🛂",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── CSS ───────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
.diplomat-header {
    background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
    padding: 2rem; border-radius: 12px; text-align: center; margin-bottom: 2rem;
}
.diplomat-header h1 { color: #e94560; font-size: 2.5rem; margin: 0; }
.diplomat-header p { color: #a8dadc; margin: 0.5rem 0 0 0; font-size: 1.1rem; }

.agent-box {
    background: #1e2a3a; border: 1px solid #2d4059; border-radius: 8px;
    padding: 1.2rem 0.8rem; margin: 0.2rem; text-align: center; 
    display: inline-block; min-width: 140px;
}
.agent-box .agent-name { color: #a8dadc; font-weight: bold; font-size: 0.9rem; }
.agent-box .agent-method { color: #7a9fbb; font-size: 0.7rem; margin-top: 0.3rem; }

.gate-box {
    background: #1e2a3a; border: 2px solid #555; border-radius: 6px;
    padding: 0.6rem 0.4rem; margin: 0.2rem; text-align: center;
    display: inline-block; min-width: 100px;
}

.gate-pass {
    border-color: #27ae60; background: #0d2b0d;
    color: #27ae60; font-weight: bold; font-size: 0.85rem;
}
.gate-bounce {
    border-color: #e94560; background: #2b0d0d;
    color: #e94560; font-weight: bold; font-size: 0.85rem;
}
.gate-attempt {
    color: #f39c12; font-size: 0.75rem;
}

.bounce-panel {
    background: #2b0d0d; border-left: 4px solid #e94560; padding: 0.8rem;
    margin: 0.5rem 0; border-radius: 4px; font-size: 0.9rem;
}
.bounce-check {
    color: #e94560; font-weight: bold;
    margin-bottom: 0.3rem;
}
.bounce-detail {
    color: #ccc; margin-left: 1rem; font-size: 0.85rem;
    font-family: monospace;
}

.success-card {
    background: #0d2b0d; border: 2px solid #27ae60; border-radius: 8px; 
    padding: 1.5rem; margin: 1rem 0;
}
.success-card h3 { color: #27ae60; margin: 0 0 0.5rem 0; }
.success-card .deduction { 
    display: flex; justify-content: space-between; margin: 0.3rem 0;
    color: #ccc; font-size: 0.95rem;
}
.success-card .total-row {
    border-top: 1px solid #27ae60; margin-top: 0.5rem; padding-top: 0.5rem;
    font-weight: bold;
}

.escalate-card {
    background: #2b0d0d; border: 2px solid #e94560; border-radius: 8px; 
    padding: 1.5rem; margin: 1rem 0;
}
.escalate-card h3 { color: #e94560; margin: 0 0 0.5rem 0; }

.trace-flow {
    background: #1a1a2e; border: 1px solid #2d4059; border-radius: 8px;
    padding: 1.2rem; margin: 1rem 0; text-align: center;
    overflow-x: auto;
}
</style>
""", unsafe_allow_html=True)


# ── Scenario definitions ──────────────────────────────────────────────────────
SCENARIOS = [
    {
        "name": "SCENARIO 1: Gate 1 — Intake misreads room rent",
        "description": "Tests Veritas (Gate 1) bounce + retry loop",
        "inject_fault": "room_rent_misread",
    },
    {
        "name": "SCENARIO 2: Gate 2 — Adjudicator missing citation",
        "description": "Tests Diplomat (Gate 2) bounce + retry loop",
        "inject_fault": "missing_citation",
    },
    {
        "name": "SCENARIO 3: Clean claim — no fault injection",
        "description": "Tests clean path through all gates",
        "inject_fault": None,
    },
    {
        "name": "CLEAN RUN (manual override)",
        "description": "No fault injection, fresh run",
        "inject_fault": None,
    },
]


# ── Load demo data ────────────────────────────────────────────────────────────
DEMO_DATA_DIR = ROOT / "demo_data"
policy = load_json(str(DEMO_DATA_DIR / "policy.json"))
bill = load_json(str(DEMO_DATA_DIR / "bill.json"))
discharge = load_json(str(DEMO_DATA_DIR / "discharge_summary.json"))


# ── Header ────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="diplomat-header">
  <h1>🛂 DIPLOMAT</h1>
  <p>Fail-Closed Trust Layer for Insurance AI Agents</p>
</div>
""", unsafe_allow_html=True)


# ── Main controls ─────────────────────────────────────────────────────────────
col_scenario, col_button = st.columns([3, 1])

with col_scenario:
    scenario_idx = st.selectbox(
        "Select Scenario",
        range(len(SCENARIOS)),
        format_func=lambda i: SCENARIOS[i]["name"],
        label_visibility="collapsed"
    )
    selected_scenario = SCENARIOS[scenario_idx]

with col_button:
    run_button = st.button("▶ Run Claim", type="primary", use_container_width=True)


# ── Initialize pipeline ───────────────────────────────────────────────────────
@st.cache_resource
def get_pipeline():
    return InsurancePipeline(policy, use_gates=True, max_retries=2)


pipeline = get_pipeline()


# ── Helper: Render agent in flow ──────────────────────────────────────────────
def render_agent(name: str, method: str = None) -> str:
    method_html = f'<div class="agent-method">[{method}]</div>' if method else ""
    return f'''
<div class="agent-box">
  <div class="agent-name">{name}</div>
  {method_html}
</div>
'''


def render_gate(status: str, attempt: int = None) -> str:
    if "PASS" in status:
        css_class = "gate-box gate-pass"
        text = f"✅ PASS"
    elif "BOUNCE" in status:
        css_class = "gate-box gate-bounce"
        text = f"🔄 BOUNCE"
    else:
        css_class = "gate-box"
        text = "—"
    
    attempt_text = f'<div class="gate-attempt">(attempt {attempt})</div>' if attempt else ""
    return f'<div class="{css_class}">{text}{attempt_text}</div>'


# ── Process claim ─────────────────────────────────────────────────────────────
if run_button:
    with st.spinner("Running DIPLOMAT pipeline..."):
        result = pipeline.process(
            bill, 
            discharge, 
            inject_fault=selected_scenario["inject_fault"]
        )
    
    # ── Agent flow visualization ──────────────────────────────────────────────
    st.markdown("### 🔄 Pipeline Trace")
    
    flow_html = '<div class="trace-flow">'
    
    # Build flow from trace
    trace_by_step = {}
    for step_entry in result.get("trace", []):
        step_name = step_entry.get("step")
        if step_name not in trace_by_step:
            trace_by_step[step_name] = []
        trace_by_step[step_name].append(step_entry)
    
    # Render timeline: A1_INTAKE → G1_VERITAS → A2_POLICY → A3_ADJUDICATOR → G2_DIPLOMAT → SETTLEMENT
    agent_flow = [
        ("A1_INTAKE", "IntakeAgent", "llm"),
        ("G1_VERITAS", "Veritas Gate", None),
        ("A2_POLICY", "PolicyEngine", "deterministic"),
        ("A3_ADJUDICATOR", "AdjudicatorAgent", "llm"),
        ("G2_DIPLOMAT", "Diplomat Gate", None),
    ]
    
    for step_name, display_name, method in agent_flow:
        if step_name.startswith("A"):
            # It's an agent
            entries = trace_by_step.get(step_name, [])
            if entries:
                last_entry = entries[-1]
                method_tag = None
                if method:
                    output = last_entry.get("output") or last_entry.get("settlement")
                    if isinstance(output, dict):
                        em = output.get("_extraction_method")
                        am = output.get("_adjudication_method")
                        if em:
                            method_tag = em
                        elif am:
                            method_tag = am
                        else:
                            method_tag = method
                    else:
                        method_tag = method
                flow_html += render_agent(display_name, method_tag)
        else:
            # It's a gate
            entries = trace_by_step.get(step_name, [])
            if entries:
                last_entry = entries[-1]
                status = last_entry.get("status", "PENDING")
                attempt = last_entry.get("attempt", None)
                flow_html += render_gate(status, attempt)
    
    flow_html += '</div>'
    st.markdown(flow_html, unsafe_allow_html=True)
    
    # ── Bounce feedback panels ────────────────────────────────────────────────
    bounce_steps = [s for s in result.get("trace", []) if "BOUNCE" in s.get("status", "")]
    if bounce_steps:
        st.markdown("### 🔴 Gate Bounces (Feedback Sent to Agent)")
        for bounce_step in bounce_steps:
            gate_name = bounce_step.get("step")
            bounces = bounce_step.get("bounces", [])
            
            for bounce in bounces:
                st.markdown(f"""
<div class="bounce-panel">
<div class="bounce-check">🚫 {bounce.get('check', 'UNKNOWN')}</div>
<div class="bounce-detail">{bounce.get('message', '')}</div>
""", unsafe_allow_html=True)
                
                if "expected" in bounce and "got" in bounce:
                    st.markdown(f"""
<div class="bounce-detail">
  Expected: <b>{bounce['expected']}</b><br>
  Got: <b>{bounce['got']}</b>
</div>
""", unsafe_allow_html=True)
                
                if "hint" in bounce:
                    st.markdown(f"""
<div class="bounce-detail">💡 {bounce['hint']}</div>
</div>
""", unsafe_allow_html=True)
                else:
                    st.markdown("</div>", unsafe_allow_html=True)
    
    # ── Result card ───────────────────────────────────────────────────────────
    st.markdown("### 📄 Final Result")
    
    if result.get("status") == "APPROVED":
        settlement = result.get("settlement", {})
        bill_total = settlement.get("bill_total", 0)
        total_deductions = settlement.get("total_deductions", 0)
        payable = settlement.get("payable", 0)
        
        st.markdown(f"""
<div class="success-card">
  <h3>✅ APPROVED</h3>
  <div class="deduction">
    <span>Bill Total:</span>
    <span style="font-weight: bold;">₹{bill_total:,.2f}</span>
  </div>
""", unsafe_allow_html=True)
        
        deductions = settlement.get("deductions", [])
        if deductions:
            st.markdown('  <div style="border-top: 1px solid #27ae60; margin: 0.5rem 0; padding: 0.5rem 0;">', unsafe_allow_html=True)
            for deduction in deductions:
                desc = deduction.get("description", "Unknown")
                amount = deduction.get("amount", 0)
                clause_id = deduction.get("clause_id", "?")
                st.markdown(f"""
  <div class="deduction">
    <span>{desc:<40} [{clause_id}]</span>
    <span>₹{amount:,.2f}</span>
  </div>
""", unsafe_allow_html=True)
            st.markdown('  </div>', unsafe_allow_html=True)
        
        st.markdown(f"""
  <div class="deduction total-row">
    <span>Total Deductions:</span>
    <span>₹{total_deductions:,.2f}</span>
  </div>
  <div class="deduction total-row" style="color: #27ae60; font-size: 1.1rem;">
    <span>PAYABLE:</span>
    <span>₹{payable:,.2f}</span>
  </div>
</div>
""", unsafe_allow_html=True)
    
    else:
        bounces = result.get("bounces", [])
        reason = result.get("reason", "Unknown reason")
        
        st.markdown(f"""
<div class="escalate-card">
  <h3>🚨 ESCALATED TO HUMAN REVIEW</h3>
  <p><strong>Reason:</strong> {reason}</p>
""", unsafe_allow_html=True)
        
        if bounces:
            st.markdown("  <p><strong>Final Unresolved Issues:</strong></p>", unsafe_allow_html=True)
            for bounce in bounces:
                check_name = bounce.get("check", bounce.get("validator", "UNKNOWN"))
                msg = bounce.get("message", "")
                st.markdown(f"""
  <div class="bounce-detail">
    • {check_name}: {msg}
  </div>
""", unsafe_allow_html=True)
        
        st.markdown("</div>", unsafe_allow_html=True)
    
    # ── Detailed trace ────────────────────────────────────────────────────────
    with st.expander("📋 Full Trace (for debugging)"):
        st.json(result.get("trace", []))
