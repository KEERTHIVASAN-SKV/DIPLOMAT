# 🛂 DIPLOMAT
## Fail-Closed Trust Layer for Insurance AI Agents

DIPLOMAT is a contract-enforcement gateway placed **between** AI agents in an insurance claim workflow.
It ensures that no agent can pass incomplete, ambiguous, contradictory, or unsupported financial information to another agent.

---

## Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Copy and configure environment
cp .env.example .env
# Add your GOOGLE_API_KEY for live LLM mode
# Set GEMINI_MODEL=gemini-3.5-flash-lite (confirmed working on free tier)
# Set MOCK_MODE=false to use real Gemini API

# 3. Run the medical claims demo (shows LLM extraction + validation + retry loops)
python demo.py

# 4. (Optional) Run the visual dashboard
streamlit run dashboard/app.py
```

---

## Demo Scenarios

The demo processes health insurance claims through a multi-agent pipeline with validation gates:

**Pipeline Flow:**
```
Medical Documents (bill + discharge summary + policy)
    ↓
IntakeAgent (LLM extracts structured data)
    ↓
🛂 Gate 1: VERITAS (validates extraction integrity)
    ↓ (retry loop with feedback if bounced)
PolicyEngine (determines applicable rules)
    ↓
AdjudicatorAgent (LLM calculates deductions)
    ↓
🛂 Gate 2: DIPLOMAT (validates calculations)
    ↓ (retry loop with feedback if bounced)
Final Settlement or Human Review
```

**Scenarios:**
1. **Clean Extraction** — LLM may make mistakes (citation errors, calculation errors) that trigger retry loops
2. **Room Rent Misread** — Simulated OCR error tests Gate 1 bounce + feedback correction
3. **Missing Citation** — Simulated calculation error tests Gate 2 bounce + feedback correction

**Expected Outcomes:**
- ✅ **APPROVED** — All gates pass, settlement calculated
- 🚨 **ESCALATED_TO_HUMAN** — LLM fails after max retries with feedback
- 🤚 **HUMAN REVIEW** — High-value or high-risk claims

---

## Architecture

```
Medical Documents (Bill, Discharge Summary, Policy)
    ↓
IntakeAgent (LLM) → 🛂 Gate 1: VERITAS → (retry with feedback if bounced)
    ↓
PolicyEngine (deterministic rule matching)
    ↓
AdjudicatorAgent (LLM) → 🛂 Gate 2: DIPLOMAT → (retry with feedback if bounced)
    ↓
Settlement / Human Review
```

**Key Innovation:** When an LLM agent produces invalid output, the gate doesn't just block it — it sends structured feedback explaining exactly what failed, and the agent retries with that feedback incorporated into the prompt. This creates a self-correcting loop.

---

## DIPLOMAT's Validation Checks

### Gate 1: VERITAS (Input Verification)
- **C1_BILL_INTEGRITY** — line items must sum to bill total
- **C2_CROSS_DOC_DATE** — dates must match across documents
- **C2_CROSS_DOC_NAME** — patient names must match across documents
- **C3_SOURCE_CITATION** — extracted values must appear verbatim in source citations
- **C6_POLICY_LINK** — policy IDs must match

### Gate 2: DIPLOMAT (Calculation Verification)
- **C4_CITATION_RULE** — every deduction must cite a valid policy clause
- **C5_RECOMPUTE_RULE** — independently recompute each deduction to verify LLM math
- **C6_IDENTITY** — payable = bill_total - total_deductions (arithmetic check)
- **C7_PED_LINKAGE** — pre-existing disease deductions must have evidence

---

## Project Structure

```
diplomat/
├── agents/               # AI agents (IntakeAgent, AdjudicatorAgent, PolicyEngine)
├── diplomat/             # Validation gates (Veritas, Diplomat) + validators
├── models/               # Pydantic data models
├── orchestrator/         # Pipeline with retry loops + feedback
├── demo_data/            # Medical claim documents (bill, discharge, policy)
├── demo.py               # Main demo runner (health insurance pipeline)
├── dashboard/            # Streamlit visual demo
├── diagnostics/          # Debugging scripts used during development (not part of core pipeline)
└── test_*.py             # Verification scripts

# Legacy/Prototypes (not used in main demo):
├── contracts/            # Earlier multi-agent handoff contracts
├── test_claims/          # Motor insurance scenarios (different pipeline)
└── main.py               # Earlier CLI runner (not compatible with current pipeline)
```

## Environment Variables

| Variable | Default | Description |
|---|---|---|
| `GOOGLE_API_KEY` | — | Gemini API key (required for LLM mode) |
| `GEMINI_MODEL` | `gemini-3.5-flash-lite` | Gemini model (confirmed working on free tier) |
| `MOCK_MODE` | `true` | Set `false` to use real Gemini API |

**Note:** Do NOT use deprecated models like `gemini-1.5-flash`, `gemini-2.5-flash`, or `gemini-3.6-flash` — these either 404 on new accounts or hit tiny free-tier quota caps (20 requests/day). Confirmed working: `gemini-3.5-flash-lite`.

---

*Built for Hackathon — Track 3: Old World, New Money + Track 2: Agentic Web*
