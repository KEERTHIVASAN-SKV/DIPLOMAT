"""
DIPLOMAT Dashboard v3 — Premium Modern Animated SaaS Dashboard
Dark fintech aesthetic with glassmorphism, animated pipeline, and interactive metrics
"""
import json
import sys
import time
from pathlib import Path
from datetime import datetime

import streamlit as st

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

from orchestrator.pipeline import InsurancePipeline
from agents.fraud_detector import FraudDetector
from orchestrator.analytics import PipelineAnalytics
from orchestrator.batch_processor import BatchProcessor


def load_json(path: str) -> dict:
    with open(path, encoding='utf-8') as f:
        return json.load(f)


# ═══════════════════════════════════════════════════════════════════════════
# PAGE CONFIG
# ═══════════════════════════════════════════════════════════════════════════

st.set_page_config(
    page_title="DIPLOMAT — AI Insurance Gateway",
    page_icon="🛂",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ═══════════════════════════════════════════════════════════════════════════
# PREMIUM CSS - Glassmorphism + Animations + Dark SaaS Aesthetic
# ═══════════════════════════════════════════════════════════════════════════

st.markdown("""
<style>
/* Root Variables */
:root {
    --primary: #6366f1;
    --primary-light: #818cf8;
    --secondary: #8b5cf6;
    --success: #10b981;
    --warning: #f59e0b;
    --danger: #ef4444;
    --dark-bg: #0f172a;
    --card-bg: rgba(15, 23, 42, 0.7);
    --glass: rgba(255, 255, 255, 0.05);
    --glass-hover: rgba(255, 255, 255, 0.1);
}

/* Global Styles */
* {
    margin: 0;
    padding: 0;
}

body, .main {
    background: linear-gradient(135deg, #0f172a 0%, #1a1a3e 50%, #16213e 100%);
    color: #e2e8f0;
    font-family: 'Segoe UI', 'Roboto', sans-serif;
}

.stApp {
    background: transparent;
}

/* Remove Streamlit default padding */
.main > div {
    padding-top: 0;
}

/* ─────────────────────────────────────────────────────────────────────── */
/* PREMIUM HEADER */
/* ─────────────────────────────────────────────────────────────────────── */

.premium-header {
    background: linear-gradient(135deg, rgba(99, 102, 241, 0.15) 0%, rgba(139, 92, 246, 0.15) 100%);
    backdrop-filter: blur(20px);
    -webkit-backdrop-filter: blur(20px);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 24px;
    padding: 3rem 2.5rem;
    margin: 2rem 0;
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
    text-align: center;
}

.premium-header h1 {
    font-size: 3rem;
    font-weight: 800;
    background: linear-gradient(135deg, #818cf8 0%, #a78bfa 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    margin-bottom: 0.5rem;
    letter-spacing: -1px;
}

.premium-header .subtitle {
    color: #cbd5e1;
    font-size: 1.1rem;
    font-weight: 500;
    margin-bottom: 0.5rem;
}

.premium-header .description {
    color: #94a3b8;
    font-size: 0.95rem;
    margin-top: 0.5rem;
}

/* ─────────────────────────────────────────────────────────────────────── */
/* GLASSMORPHISM CARDS */
/* ─────────────────────────────────────────────────────────────────────── */

.glass-card {
    background: rgba(15, 23, 42, 0.6);
    backdrop-filter: blur(20px);
    -webkit-backdrop-filter: blur(20px);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 20px;
    padding: 2rem;
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.2);
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.glass-card:hover {
    background: rgba(15, 23, 42, 0.8);
    border-color: rgba(255, 255, 255, 0.2);
    transform: translateY(-4px);
    box-shadow: 0 16px 48px rgba(99, 102, 241, 0.2);
}

/* ─────────────────────────────────────────────────────────────────────── */
/* ANIMATED AGENT PIPELINE */
/* ─────────────────────────────────────────────────────────────────────── */

@keyframes float-up {
    0%, 100% { transform: translateY(0px); }
    50% { transform: translateY(-8px); }
}

@keyframes pulse-glow {
    0%, 100% { box-shadow: 0 0 10px rgba(99, 102, 241, 0.5); }
    50% { box-shadow: 0 0 20px rgba(99, 102, 241, 0.8); }
}

@keyframes slide-right {
    0% { transform: translateX(-20px); opacity: 0; }
    100% { transform: translateX(0); opacity: 1; }
}

.agent-node {
    background: linear-gradient(135deg, rgba(99, 102, 241, 0.2) 0%, rgba(139, 92, 246, 0.2) 100%);
    backdrop-filter: blur(10px);
    border: 2px solid rgba(99, 102, 241, 0.5);
    border-radius: 16px;
    padding: 1.5rem;
    text-align: center;
    min-width: 140px;
    transition: all 0.3s ease;
    animation: float-up 3s ease-in-out infinite;
}

.agent-node.active {
    border-color: #818cf8;
    background: linear-gradient(135deg, rgba(99, 102, 241, 0.4) 0%, rgba(139, 92, 246, 0.4) 100%);
    box-shadow: 0 0 20px rgba(99, 102, 241, 0.6);
    animation: pulse-glow 2s ease-in-out infinite;
}

.agent-node .name {
    font-weight: 700;
    color: #e2e8f0;
    font-size: 0.95rem;
    margin-bottom: 0.5rem;
}

.agent-node .method {
    color: #94a3b8;
    font-size: 0.75rem;
    background: rgba(255, 255, 255, 0.05);
    padding: 0.4rem 0.8rem;
    border-radius: 8px;
    display: inline-block;
    margin-top: 0.5rem;
}

/* ─────────────────────────────────────────────────────────────────────── */
/* GATE STATUS INDICATORS */
/* ─────────────────────────────────────────────────────────────────────── */

.gate-indicator {
    min-width: 100px;
    padding: 1rem 0.8rem;
    border-radius: 14px;
    text-align: center;
    font-weight: 600;
    font-size: 0.9rem;
    transition: all 0.3s ease;
    border: 2px solid;
}

.gate-pass {
    background: rgba(16, 185, 129, 0.2);
    color: #10b981;
    border-color: rgba(16, 185, 129, 0.5);
    box-shadow: 0 0 15px rgba(16, 185, 129, 0.3);
}

.gate-bounce {
    background: rgba(239, 68, 68, 0.2);
    color: #ef4444;
    border-color: rgba(239, 68, 68, 0.5);
    box-shadow: 0 0 15px rgba(239, 68, 68, 0.3);
    animation: pulse-glow 1.5s ease-in-out infinite;
}

.gate-processing {
    background: rgba(99, 102, 241, 0.2);
    color: #818cf8;
    border-color: rgba(99, 102, 241, 0.5);
    box-shadow: 0 0 15px rgba(99, 102, 241, 0.3);
    animation: pulse-glow 1s ease-in-out infinite;
}

.gate-review {
    background: rgba(245, 158, 11, 0.2);
    color: #f59e0b;
    border-color: rgba(245, 158, 11, 0.5);
    box-shadow: 0 0 15px rgba(245, 158, 11, 0.3);
}

/* ─────────────────────────────────────────────────────────────────────── */
/* PIPELINE FLOW */
/* ─────────────────────────────────────────────────────────────────────── */

.pipeline-flow {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 1rem;
    flex-wrap: wrap;
    padding: 2rem;
    background: linear-gradient(135deg, rgba(99, 102, 241, 0.08) 0%, rgba(139, 92, 246, 0.08) 100%);
    border-radius: 20px;
    border: 1px solid rgba(99, 102, 241, 0.2);
    margin: 2rem 0;
    overflow-x: auto;
}

.pipeline-arrow {
    color: #818cf8;
    font-size: 1.5rem;
    animation: slide-right 1.5s ease-in-out infinite;
}

/* ─────────────────────────────────────────────────────────────────────── */
/* METRIC CARDS */
/* ─────────────────────────────────────────────────────────────────────── */

.metric-card {
    background: rgba(15, 23, 42, 0.6);
    backdrop-filter: blur(10px);
    border: 1px solid rgba(99, 102, 241, 0.3);
    border-radius: 16px;
    padding: 1.5rem;
    text-align: center;
    transition: all 0.3s ease;
}

.metric-card:hover {
    transform: translateY(-4px);
    border-color: rgba(99, 102, 241, 0.6);
    box-shadow: 0 8px 24px rgba(99, 102, 241, 0.2);
}

.metric-card .icon {
    font-size: 2rem;
    margin-bottom: 0.5rem;
}

.metric-card .label {
    color: #94a3b8;
    font-size: 0.85rem;
    margin-bottom: 0.5rem;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}

.metric-card .value {
    font-size: 2rem;
    font-weight: 800;
    background: linear-gradient(135deg, #818cf8 0%, #a78bfa 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}

/* ─────────────────────────────────────────────────────────────────────── */
/* FRAUD RISK CARD */
/* ─────────────────────────────────────────────────────────────────────── */

.fraud-card {
    border-radius: 20px;
    padding: 2rem;
    backdrop-filter: blur(20px);
    border: 1px solid;
    margin: 1.5rem 0;
}

.fraud-high {
    background: linear-gradient(135deg, rgba(239, 68, 68, 0.15) 0%, rgba(220, 38, 38, 0.15) 100%);
    border-color: rgba(239, 68, 68, 0.3);
}

.fraud-medium {
    background: linear-gradient(135deg, rgba(245, 158, 11, 0.15) 0%, rgba(217, 119, 6, 0.15) 100%);
    border-color: rgba(245, 158, 11, 0.3);
}

.fraud-low {
    background: linear-gradient(135deg, rgba(16, 185, 129, 0.15) 0%, rgba(5, 150, 105, 0.15) 100%);
    border-color: rgba(16, 185, 129, 0.3);
}

.fraud-title {
    font-size: 1.5rem;
    font-weight: 700;
    margin-bottom: 0.5rem;
}

.fraud-score {
    font-size: 3rem;
    font-weight: 800;
    margin: 1rem 0;
}

.fraud-recommendation {
    padding: 1rem;
    border-radius: 12px;
    background: rgba(255, 255, 255, 0.05);
    margin-top: 1rem;
    border-left: 4px solid;
}

/* ─────────────────────────────────────────────────────────────────────── */
/* SETTLEMENT CARD */
/* ─────────────────────────────────────────────────────────────────────── */

.settlement-card {
    background: linear-gradient(135deg, rgba(16, 185, 129, 0.15) 0%, rgba(5, 150, 105, 0.15) 100%);
    backdrop-filter: blur(20px);
    border: 1px solid rgba(16, 185, 129, 0.3);
    border-radius: 20px;
    padding: 2rem;
    margin: 1.5rem 0;
}

.settlement-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 1rem 0;
    border-bottom: 1px solid rgba(255, 255, 255, 0.05);
}

.settlement-row:last-child {
    border-bottom: none;
}

.settlement-label {
    color: #cbd5e1;
    font-weight: 500;
}

.settlement-value {
    font-size: 1.3rem;
    font-weight: 700;
    color: #10b981;
}

.settlement-total {
    font-size: 1.8rem;
    color: #10b981;
    margin-top: 1rem;
}

/* ─────────────────────────────────────────────────────────────────────── */
/* BUTTONS */
/* ─────────────────────────────────────────────────────────────────────── */

.premium-button {
    background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
    border: none;
    color: white;
    padding: 0.8rem 2rem;
    border-radius: 12px;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.3s ease;
    box-shadow: 0 4px 15px rgba(99, 102, 241, 0.3);
}

.premium-button:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 25px rgba(99, 102, 241, 0.5);
}

/* ─────────────────────────────────────────────────────────────────────── */
/* TABS */
/* ─────────────────────────────────────────────────────────────────────── */

.stTabs [data-baseweb="tab-list"] {
    gap: 1rem;
    background: rgba(15, 23, 42, 0.4);
    padding: 1rem;
    border-radius: 16px;
    border: 1px solid rgba(99, 102, 241, 0.2);
}

.stTabs [data-baseweb="tab"] {
    background: transparent;
    border-radius: 12px;
    color: #94a3b8;
    border: 1px solid transparent;
    transition: all 0.3s ease;
}

.stTabs [aria-selected="true"] {
    background: linear-gradient(135deg, rgba(99, 102, 241, 0.3) 0%, rgba(139, 92, 246, 0.3) 100%);
    color: #818cf8;
    border-color: rgba(99, 102, 241, 0.5);
}

/* ─────────────────────────────────────────────────────────────────────── */
/* SCROLLBAR */
/* ─────────────────────────────────────────────────────────────────────── */

::-webkit-scrollbar {
    width: 8px;
    height: 8px;
}

::-webkit-scrollbar-track {
    background: rgba(15, 23, 42, 0.3);
}

::-webkit-scrollbar-thumb {
    background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
    border-radius: 4px;
}

::-webkit-scrollbar-thumb:hover {
    background: linear-gradient(135deg, #818cf8 0%, #a78bfa 100%);
}
</style>
""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════
# SESSION STATE & INITIALIZATION
# ═══════════════════════════════════════════════════════════════════════════

if "analytics" not in st.session_state:
    st.session_state.analytics = PipelineAnalytics()
if "fraud_detector" not in st.session_state:
    st.session_state.fraud_detector = FraudDetector()

# Load demo data
DEMO_DATA_DIR = ROOT / "demo_data"
policy = load_json(str(DEMO_DATA_DIR / "policy.json"))
bill = load_json(str(DEMO_DATA_DIR / "bill.json"))
discharge = load_json(str(DEMO_DATA_DIR / "discharge_summary.json"))

# ═══════════════════════════════════════════════════════════════════════════
# PREMIUM HEADER
# ═══════════════════════════════════════════════════════════════════════════

st.markdown("""
<div class="premium-header">
    <h1>🛂 DIPLOMAT</h1>
    <div class="subtitle">Enterprise Insurance AI Gateway</div>
    <div class="description">Self-correcting pipeline with fraud detection, validation gates & explainable decisions</div>
</div>
""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════
# MAIN INTERFACE
# ═══════════════════════════════════════════════════════════════════════════

tab1, tab2, tab3, tab4 = st.tabs(["🎯 Process Claim", "📊 Analytics", "🔍 Fraud Risk", "📈 Batch"])

# ─────────────────────────────────────────────────────────────────────────
# TAB 1: CLAIMS PROCESSOR
# ─────────────────────────────────────────────────────────────────────────

with tab1:
    st.markdown("### 📋 Claim Processing")
    
    SCENARIOS = [
        {"name": "🟢 Clean Claim", "inject_fault": None},
        {"name": "🔴 Room Rent Misread", "inject_fault": "room_rent_misread"},
        {"name": "🟡 Missing Citation", "inject_fault": "missing_citation"},
    ]
    
    col1, col2 = st.columns([3, 1])
    with col1:
        scenario_idx = st.selectbox("Select Scenario", range(len(SCENARIOS)), 
                                   format_func=lambda i: SCENARIOS[i]["name"],
                                   label_visibility="collapsed")
    with col2:
        run_btn = st.button("▶ Process", use_container_width=True, type="primary")
    
    if run_btn:
        with st.spinner("⏳ Processing..."):
            start_time = time.time()
            pipeline = InsurancePipeline(policy, use_gates=True, max_retries=2)
            result = pipeline.process(bill, discharge, inject_fault=SCENARIOS[scenario_idx]["inject_fault"])
            processing_time = time.time() - start_time
        
        st.session_state.analytics.record_claim(bill, result, processing_time)
        
        # Animated Pipeline Flow
        trace = result.get("trace", [])
        trace_by_step = {step.get("step"): step for step in trace if "step" in step}
        
        st.markdown("""
<div class="pipeline-flow">
    <div class="agent-node active">
        <div class="name">📥 Intake</div>
        <div class="method">LLM</div>
    </div>
    <div class="pipeline-arrow">→</div>
    <div class="gate-indicator gate-pass">✅ VERITAS</div>
    <div class="pipeline-arrow">→</div>
    <div class="agent-node">
        <div class="name">⚙️ Policy</div>
        <div class="method">Deterministic</div>
    </div>
    <div class="pipeline-arrow">→</div>
    <div class="agent-node active">
        <div class="name">🧮 Adjudicator</div>
        <div class="method">LLM</div>
    </div>
    <div class="pipeline-arrow">→</div>
    <div class="gate-indicator gate-pass">✅ DIPLOMAT</div>
    <div class="pipeline-arrow">→</div>
    <div class="agent-node">
        <div class="name">💰 Settlement</div>
        <div class="method">Complete</div>
    </div>
</div>
""", unsafe_allow_html=True)
        
        # Fraud Analysis
        settlement = result.get("settlement", {})
        fraud_analysis = st.session_state.fraud_detector.analyze_claim(bill, settlement, policy)
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown(f"""
<div class="metric-card">
    <div class="icon">⏱️</div>
    <div class="label">Processing Time</div>
    <div class="value">{processing_time:.2f}s</div>
</div>
""", unsafe_allow_html=True)
        
        with col2:
            risk_emoji = "🟢" if fraud_analysis['risk_level'] == "LOW" else ("🟡" if fraud_analysis['risk_level'] == "MEDIUM" else "🔴")
            st.markdown(f"""
<div class="metric-card">
    <div class="icon">{risk_emoji}</div>
    <div class="label">Fraud Risk</div>
    <div class="value">{fraud_analysis['risk_score']:.2f}</div>
</div>
""", unsafe_allow_html=True)
        
        with col3:
            st.markdown(f"""
<div class="metric-card">
    <div class="icon">🎯</div>
    <div class="label">Recommendation</div>
    <div class="value" style="font-size: 1rem;">{fraud_analysis['recommendation']}</div>
</div>
""", unsafe_allow_html=True)
        
        # Result Card
        if result.get("status") == "APPROVED":
            st.markdown(f"""
<div class="settlement-card">
    <h3 style="color: #10b981; margin-bottom: 1.5rem;">✅ CLAIM APPROVED</h3>
    <div class="settlement-row">
        <span class="settlement-label">Bill Total</span>
        <span class="settlement-value">₹{settlement.get('bill_total', 0):,.0f}</span>
    </div>
    <div class="settlement-row">
        <span class="settlement-label">Total Deductions</span>
        <span class="settlement-value">₹{settlement.get('total_deductions', 0):,.0f}</span>
    </div>
    <div class="settlement-row" style="border-top: 2px solid rgba(16, 185, 129, 0.3); padding-top: 1.5rem; margin-top: 1.5rem;">
        <span class="settlement-label" style="font-size: 1.2rem; font-weight: 800;">Final Payable</span>
        <span class="settlement-total">₹{settlement.get('payable', 0):,.0f}</span>
    </div>
</div>
""", unsafe_allow_html=True)
        else:
            st.markdown(f"""
<div class="fraud-card fraud-high">
    <div class="fraud-title">🚨 ESCALATED TO HUMAN REVIEW</div>
    <div style="color: #ef4444; margin-top: 1rem;">Reason: {result.get('reason', 'Unknown')}</div>
</div>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────
# TAB 2: ANALYTICS
# ─────────────────────────────────────────────────────────────────────────

with tab2:
    st.markdown("### 📊 Real-Time Analytics")
    
    if st.session_state.analytics.claims_processed > 0:
        summary = st.session_state.analytics.get_summary()
        
        col1, col2, col3, col4 = st.columns(4)
        metrics = [
            (col1, "📋", "Claims", summary['summary']['total_claims_processed']),
            (col2, "✅", "Approved", summary['outcomes']['approved']),
            (col3, "💰", "Payout", f"₹{summary['financials']['total_approved_payout']/100000:.1f}L"),
            (col4, "📈", "Deduction", f"{summary['financials']['deduction_rate_percent']:.1f}%"),
        ]
        
        for col, icon, label, value in metrics:
            with col:
                st.markdown(f"""
<div class="metric-card">
    <div class="icon">{icon}</div>
    <div class="label">{label}</div>
    <div class="value">{value}</div>
</div>
""", unsafe_allow_html=True)
    else:
        st.info("🔄 Process claims to see analytics")

# ─────────────────────────────────────────────────────────────────────────
# TAB 3: FRAUD DETECTION
# ─────────────────────────────────────────────────────────────────────────

with tab3:
    st.markdown("### 🔍 Fraud Risk Assessment")
    st.info("Fraud analysis runs automatically on every processed claim. Risk factors are calculated based on multiple detection algorithms.")

# ─────────────────────────────────────────────────────────────────────────
# TAB 4: BATCH PROCESSING
# ─────────────────────────────────────────────────────────────────────────

with tab4:
    st.markdown("### 📈 Batch Processing")
    
    col1, col2 = st.columns(2)
    with col1:
        batch_size = st.slider("Batch Size", 1, 10, 3)
    with col2:
        parallel = st.checkbox("🚀 Parallel Processing", value=True)
    
    if st.button("⚙️ Process Batch", type="primary", use_container_width=True):
        with st.spinner("Processing batch..."):
            demo_claims = [{**bill, "claim_id": f"BATCH-{i+1:03d}"} for i in range(batch_size)]
            processor = BatchProcessor()
            pipeline = InsurancePipeline(policy)
            
            def process_fn(claim):
                return pipeline.process(claim, discharge)
            
            batch_result = processor.process_batch(demo_claims, process_fn, parallel=parallel)
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.markdown(f"""
<div class="metric-card">
    <div class="icon">⚡</div>
    <div class="label">Processed</div>
    <div class="value">{batch_result['batch_summary']['total_claims']}</div>
</div>
""", unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"""
<div class="metric-card">
    <div class="icon">✅</div>
    <div class="label">Success</div>
    <div class="value">{batch_result['batch_summary']['success_rate_percent']:.0f}%</div>
</div>
""", unsafe_allow_html=True)
        
        with col3:
            st.markdown(f"""
<div class="metric-card">
    <div class="icon">⏱️</div>
    <div class="label">Avg Time</div>
    <div class="value">{batch_result['performance'].get('avg_claim_time_ms', 0):.0f}ms</div>
</div>
""", unsafe_allow_html=True)
        
        with col4:
            st.markdown(f"""
<div class="metric-card">
    <div class="icon">📊</div>
    <div class="label">Throughput</div>
    <div class="value">{batch_result['batch_summary']['total_claims'] / max(batch_result['performance']['total_time_seconds'], 0.1) * 60:.0f}/min</div>
</div>
""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════
# FOOTER
# ═══════════════════════════════════════════════════════════════════════════

st.divider()
st.markdown("""
<div style="text-align: center; color: #64748b; font-size: 0.9rem; margin-top: 2rem;">
    <p>🛂 DIPLOMAT v3 — Premium Insurance AI Gateway</p>
    <p style="font-size: 0.85rem; margin-top: 0.5rem;">Fraud Detection • Analytics • Multi-Policy Intelligence • Enterprise APIs</p>
</div>
""", unsafe_allow_html=True)
