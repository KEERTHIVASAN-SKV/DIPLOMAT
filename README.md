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
# (Optional) Add your GOOGLE_API_KEY for live LLM mode.
# Default is MOCK_MODE=true — works without any API key.

# 3. Run all 6 demo claims (CLI)
python main.py

# 4. Run the visual dashboard
streamlit run dashboard/app.py
```

---

## Demo Scenarios

| # | Claim | Expected | Blocked By |
|---|-------|----------|------------|
| 1 | Valid motor claim | ✅ APPROVED | — |
| 2 | Amount mismatch (₹1,00,000 sum reported as ₹1,50,000) | 🚨 BLOCKED | Check 7 — Financial Rules |
| 3 | Expired policy (incident after expiry) | 🚨 BLOCKED | Check 7 — Financial Rules |
| 4 | Missing field (currency omitted) | 🚨 BLOCKED | Check 1 — Required Fields |
| 5 | Currency conflict (Assessment=USD, Policy=INR) | 🚨 BLOCKED | Check 5 — Consistency |
| 6 | High-risk claim (fraud score 0.85) | 🤚 HUMAN REVIEW | Escalation Rule |

---

## Architecture

```
Customer
    ↓
Claim Agent  →  🛂 DIPLOMAT  →  Policy Agent  →  🛂 DIPLOMAT  →
Assessment Agent  →  🛂 DIPLOMAT  →  Fraud Agent  →  🛂 DIPLOMAT  →
Settlement Agent  →  Human Review  →  PAYOUT
```

## DIPLOMAT's 7 Checks

1. **Required Fields** — all mandatory fields must be present
2. **Data Types** — types must match the contract specification
3. **Formats** — dates (YYYY-MM-DD), enums, ISO-4217 currency codes
4. **Semantic Meaning** — amounts must carry currency and source context
5. **Cross-Agent Consistency** — currency/claim_id/policy_id must not conflict across agents
6. **Evidence** — HIGH/MEDIUM risk decisions must have evidence_ids and reasons
7. **Financial Rules** — payout ≤ limit, dates valid, amounts match breakdowns

---

## Project Structure

```
diplomat/
├── agents/            # 5 insurance AI agents
├── contracts/         # Machine-readable handoff contracts (JSON)
├── diplomat/          # DIPLOMAT gateway + 7 validators
├── models/            # Pydantic data models
├── orchestrator/      # Pipeline wiring all agents + DIPLOMAT
├── test_claims/       # 6 demo scenarios
├── dashboard/         # Streamlit visual demo
└── main.py            # CLI runner
```

## Environment Variables

| Variable | Default | Description |
|---|---|---|
| `GOOGLE_API_KEY` | — | Gemini API key (optional) |
| `GEMINI_MODEL` | `gemini-1.5-flash` | Gemini model to use |
| `MOCK_MODE` | `true` | Set `false` to use live Gemini API |

---

*Built for Hackathon — Track 3: Old World, New Money + Track 2: Agentic Web*
