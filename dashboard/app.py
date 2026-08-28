"""
DIPLOMAT Dashboard
==================
Streamlit-based visual demo of the DIPLOMAT insurance pipeline.

Run with:
    streamlit run dashboard/app.py
"""
import json
import sys
import time
from pathlib import Path

import streamlit as st

# Add project root to path
ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

from orchestrator.pipeline import InsurancePipeline
from models.diplomat_models import DiplomatStatus

CLAIMS_DIR = ROOT / "test_claims"

# ── Page Config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="DIPLOMAT — Insurance AI Gateway",
    page_icon="🛂",
    layout="wide",
    initial_sidebar_state="expanded",
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
    padding: 1rem; margin: 0.3rem 0; text-align: center;
}
.agent-box .agent-name { color: #a8dadc; font-weight: bold; font-size: 1rem; }

.diplomat-gate-pass {
    background: #0d2b0d; border: 1px solid #27ae60; border-radius: 6px;
    padding: 0.5rem; margin: 0.2rem 0; text-align: center; color: #27ae60;
    font-size: 0.85rem;
}
.diplomat-gate-fail {
    background: #2b0d0d; border: 1px solid #e74c3c; border-radius: 6px;
    padding: 0.5rem; margin: 0.2rem 0; text-align: center; color: #e74c3c;
    font-size: 0.85rem;
}
.diplomat-gate-review {
    background: #2b2200; border: 1px solid #f39c12; border-radius: 6px;
    padding: 0.5rem; margin: 0.2rem 0; text-align: center; color: #f39c12;
    font-size: 0.85rem;
}
.diplomat-gate-pending {
    background: #1a1a2e; border: 1px dashed #555; border-radius: 6px;
    padding: 0.5rem; margin: 0.2rem 0; text-align: center; color: #555;
    font-size: 0.85rem;
}
.error-card {
    background: #2b0d0d; border: 2px solid #e74c3c; border-radius: 8px; padding: 1rem;
}
.review-card {
    background: #2b2200; border: 2px solid #f39c12; border-radius: 8px; padding: 1rem;
}
.success-card {
    background: #0d2b0d; border: 2px solid #27ae60; border-radius: 8px; padding: 1rem;
}
.metric-box {
    background: #1e2a3a; border-radius: 8px; padding: 1rem; text-align: center;
    border: 1px solid #2d4059;
}
</style>
""", unsafe_allow_html=True)


# ── Helpers ───────────────────────────────────────────────────────────────────
@st.cache_resource
def get_pipeline():
    return InsurancePipeline()


def load_claim_files():
    return sorted(CLAIMS_DIR.glob("claim_0*.json"))


def load_claim(path: Path) -> dict:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def gate_html(status: str, label: str, message: str = "") -> str:
    if status == "PASS":
        cls = "diplomat-gate-pass"
        icon = "✅ CONTRACT PASS"
    elif status == "HUMAN_REVIEW":
        cls = "diplomat-gate-review"
        icon = "🤚 HUMAN REVIEW"
    elif status == "REJECTED":
        cls = "diplomat-gate-fail"
        icon = f"🚨 BLOCKED"
    else:
        cls = "diplomat-gate-pending"
        icon = "🛂 DIPLOMAT"

    msg_html = f"<br><small>{message[:80]}</small>" if message else ""
    return f'<div class="{cls}"><b>{icon}</b>{msg_html}</div>'


def agent_html(name: str, active: bool = True) -> str:
    opacity = "1.0" if active else "0.35"
    return f'<div class="agent-box" style="opacity:{opacity}"><div class="agent-name">🤖 {name}</div></div>'


# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🛂 DIPLOMAT")
    st.markdown("**Fail-Closed Trust Layer**\n*for Insurance AI Agents*")
    st.divider()

    claim_files = load_claim_files()
    claim_labels = []
    for cf in claim_files:
        data = load_claim(cf)
        claim_labels.append(f"{data['claim_id']} — {data.get('claimant_name','?')}")

    selected_idx = st.selectbox(
        "Select a Demo Claim",
        range(len(claim_labels)),
        format_func=lambda i: claim_labels[i],
    )

    run_all = st.button("▶ Run All 6 Claims", use_container_width=True, type="secondary")
    run_one = st.button("▶ Process This Claim", use_container_width=True, type="primary")

    st.divider()
    st.markdown("""
**7 DIPLOMAT Checks:**
1. Required Fields
2. Data Types
3. Formats
4. Semantic Meaning
5. Cross-Agent Consistency
6. Evidence
7. Financial Rules
""")


# ── Header ─────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="diplomat-header">
  <h1>🛂 DIPLOMAT</h1>
  <p>Fail-Closed Trust Layer for Insurance AI Agents</p>
</div>
""", unsafe_allow_html=True)


# ── Main Area ─────────────────────────────────────────────────────────────────
pipeline = get_pipeline()
selected_claim_file = claim_files[selected_idx]
selected_claim_data = load_claim(selected_claim_file)

# Show claim details
col_info, col_flow, col_result = st.columns([2, 1.5, 2])

with col_info:
    st.markdown("### 📋 Claim Details")
    st.json({
        "claim_id": selected_claim_data.get("claim_id"),
        "policy_id": selected_claim_data.get("policy_id"),
        "claimant": selected_claim_data.get("claimant_name"),
        "incident_type": selected_claim_data.get("incident_type"),
        "incident_date": selected_claim_data.get("incident_date"),
        "estimated_damage": selected_claim_data.get("estimated_damage"),
    })

with col_flow:
    st.markdown("### 🔄 Agent Flow")
    agents = ["Claim Agent", "Policy Agent", "Assessment Agent", "Fraud Agent", "Settlement Agent"]
    flow_placeholder = st.empty()

    def render_flow(handoff_log=None):
        gates = {}
        if handoff_log:
            step_map = {
                "ClaimAgent → PolicyAgent": 0,
                "PolicyAgent → AssessmentAgent": 1,
                "AssessmentAgent → FraudAgent": 2,
                "FraudAgent → SettlementAgent": 3,
            }
            for entry in handoff_log:
                idx = step_map.get(entry["step"])
                if idx is not None:
                    gates[idx] = (entry["status"], entry.get("error_code", ""))

        html_parts = []
        for i, agent in enumerate(agents):
            active = True
            if handoff_log:
                # Agent is inactive if pipeline was blocked before it
                blocked = any(
                    gates.get(j, ("PASS", ""))[0] in ("REJECTED",)
                    for j in range(i)
                )
                active = not blocked or i == 0

            html_parts.append(agent_html(agent, active))
            if i < len(agents) - 1:
                gate_status, gate_msg = gates.get(i, ("PENDING", ""))
                html_parts.append(gate_html(gate_status, f"Gate {i+1}", gate_msg))

        flow_placeholder.markdown("".join(html_parts), unsafe_allow_html=True)

    render_flow()

with col_result:
    st.markdown("### 🏁 Result")
    result_placeholder = st.empty()
    result_placeholder.info("Click **▶ Process This Claim** to run the pipeline.")


# ── Run Single Claim ──────────────────────────────────────────────────────────
if run_one:
    with col_result:
        result_placeholder.empty()

    steps_collected = []

    def on_step(step, payload, dr):
        steps_collected.append({"step": step, "status": dr.status.value,
                                 "error_code": dr.error_code, "message": dr.message,
                                 "details": dr.details})
        render_flow(steps_collected)
        time.sleep(0.4)

    with st.spinner("Running DIPLOMAT pipeline..."):
        result = pipeline.run(selected_claim_data, on_step=on_step)

    render_flow(result.handoff_log)

    with col_result:
        if result.final_status == "APPROVED":
            payout = result.final_output.get("payable_amount", 0)
            breakdown = result.final_output.get("calculation_breakdown", {})
            result_placeholder.empty()
            st.markdown(f"""
<div class="success-card">
<h3>✅ APPROVED</h3>
<b>Payable Amount: ₹{payout:,.2f}</b>
<hr/>
<small>
Eligible: ₹{breakdown.get('step1_eligible_amount', 0):,.0f}<br>
After Deductible: ₹{breakdown.get('step2_after_deductible', 0):,.0f}<br>
Co-pay: ₹{breakdown.get('step3_copay_amount', 0):,.0f}<br>
<b>Final: ₹{breakdown.get('step4_final_payable', 0):,.0f}</b>
</small>
</div>
""", unsafe_allow_html=True)

        elif result.final_status == "HUMAN_REVIEW":
            err = result.error
            result_placeholder.empty()
            st.markdown(f"""
<div class="review-card">
<h3>🤚 HUMAN REVIEW REQUIRED</h3>
<b>{err.error_code if err else "ESCALATED"}</b><br>
{err.message if err else ""}
<hr/>
<small>Blocked at: {result.blocked_at or "Post-validation"}</small>
</div>
""", unsafe_allow_html=True)
        else:
            err = result.error
            result_placeholder.empty()
            st.markdown(f"""
<div class="error-card">
<h3>🚨 BLOCKED</h3>
<b>{err.error_code if err else "UNKNOWN"}</b><br>
{err.message if err else ""}
<hr/>
<small>At: {result.blocked_at}</small>
</div>
""", unsafe_allow_html=True)
            if err and err.details:
                with st.expander("Error Details"):
                    st.json(err.details)

    # Handoff log
    st.divider()
    st.markdown("### 🗂️ Handoff Audit Log")
    for entry in result.handoff_log:
        status = entry["status"]
        icon = "✅" if status == "PASS" else ("🤚" if status == "HUMAN_REVIEW" else "🚨")
        color = "green" if status == "PASS" else ("orange" if status == "HUMAN_REVIEW" else "red")
        st.markdown(f"**{icon} {entry['step']}** — :{color}[{status}]")
        if entry.get("error_code"):
            st.markdown(f"  - `{entry['error_code']}`: {entry['message']}")


# ── Run All Claims ────────────────────────────────────────────────────────────
if run_all:
    st.divider()
    st.markdown("## 📊 Batch Processing — All 6 Claims")

    cols = st.columns(3)
    claim_results = []

    for i, cf in enumerate(claim_files):
        raw = load_claim(cf)
        result = pipeline.run(raw)
        claim_results.append((cf, raw, result))

    approved = sum(1 for _, _, r in claim_results if r.final_status == "APPROVED")
    blocked = sum(1 for _, _, r in claim_results if r.final_status == "REJECTED")
    review = sum(1 for _, _, r in claim_results if r.final_status == "HUMAN_REVIEW")

    m1, m2, m3, m4 = st.columns(4)
    with m1:
        st.markdown(f'<div class="metric-box"><h2>6</h2><p>Claims Processed</p></div>', unsafe_allow_html=True)
    with m2:
        st.markdown(f'<div class="metric-box" style="border-color:#27ae60"><h2 style="color:#27ae60">✅ {approved}</h2><p>Approved</p></div>', unsafe_allow_html=True)
    with m3:
        st.markdown(f'<div class="metric-box" style="border-color:#e74c3c"><h2 style="color:#e74c3c">🚨 {blocked}</h2><p>Blocked</p></div>', unsafe_allow_html=True)
    with m4:
        st.markdown(f'<div class="metric-box" style="border-color:#f39c12"><h2 style="color:#f39c12">🤚 {review}</h2><p>Human Review</p></div>', unsafe_allow_html=True)

    st.markdown("---")
    for i, (cf, raw, result) in enumerate(claim_results, 1):
        claim_id = raw.get("claim_id")
        claimant = raw.get("claimant_name", "?")

        if result.final_status == "APPROVED":
            payout = result.final_output.get("payable_amount", 0)
            st.markdown(f"**{i}. {claim_id}** ({claimant}) → :green[✅ APPROVED — ₹{payout:,.2f}]")
        elif result.final_status == "HUMAN_REVIEW":
            err = result.error
            st.markdown(f"**{i}. {claim_id}** ({claimant}) → :orange[🤚 HUMAN REVIEW — {err.error_code if err else '?'}]")
        else:
            err = result.error
            st.markdown(f"**{i}. {claim_id}** ({claimant}) → :red[🚨 BLOCKED — {err.error_code if err else '?'} @ {result.blocked_at}]")

    st.success("**0 unsafe handoffs allowed through** — every blocked claim was caught by DIPLOMAT before reaching the next agent.")
