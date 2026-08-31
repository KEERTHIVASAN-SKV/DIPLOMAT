# 🛂 DIPLOMAT
### Fail-Closed Trust Layer for Insurance AI Agents

[![Deploy with Vercel](https://vercel.com/button)](https://vercel.com/new/clone?repository-url=https://github.com/KEERTHIVASAN-SKV/DIPLOMAT)
[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?logo=python&logoColor=white)](https://python.org)
[![Next.js](https://img.shields.io/badge/Next.js-14-black?logo=next.js)](https://nextjs.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-009688?logo=fastapi)](https://fastapi.tiangolo.com)

DIPLOMAT is a **contract-enforcement gateway** placed **between** AI agents in an insurance claim workflow. It ensures no agent can pass incomplete, ambiguous, contradictory, or unsupported financial information to another agent.

> 🏆 Built for Hackathon — Track 3: Old World, New Money + Track 2: Agentic Web

---

## 🎬 Quick Start

```bash
# 1. Clone
git clone https://github.com/KEERTHIVASAN-SKV/DIPLOMAT.git
cd DIPLOMAT

# 2. Python setup
python -m venv venv && venv\Scripts\activate   # Windows
pip install -r requirements.txt

# 3. Configure env
cp .env.example .env   # set MOCK_MODE=true to skip API key

# 4. Run the CLI demo
python demo.py

# 5. Start the web dashboard (two terminals)
uvicorn web.api.server:app --reload --port 8000   # terminal 1
cd web && npm install && npm run dev              # terminal 2
```

👉 **See [HOW_TO_START.md](./HOW_TO_START.md) for the full step-by-step guide, Vercel deployment, and troubleshooting.**

---

## 🏗️ Architecture

```
Medical Documents (Bill, Discharge Summary, Policy)
    ↓
IntakeAgent (LLM)
    ↓
🛂 Gate 1: VERITAS  ──── bounces with structured feedback ──→ retry
    ↓ (pass)
PolicyEngine (deterministic rule matching)
    ↓
AdjudicatorAgent (LLM)
    ↓
🛂 Gate 2: DIPLOMAT ──── bounces with structured feedback ──→ retry
    ↓ (pass)
Settlement / Human Review
```

**Key Innovation:** When an LLM produces invalid output, the gate doesn't just block it — it sends structured feedback explaining exactly what failed, enabling a **self-correcting retry loop**.

---

## ✅ Validation Gates

### Gate 1 — VERITAS (Input Verification)
| Check | Description |
|---|---|
| `C1_BILL_INTEGRITY` | Line items must sum to bill total |
| `C2_CROSS_DOC_DATE` | Dates must match across all documents |
| `C2_CROSS_DOC_NAME` | Patient names must match across documents |
| `C3_SOURCE_CITATION` | Extracted values must appear verbatim in source |
| `C6_POLICY_LINK` | Policy IDs must match |

### Gate 2 — DIPLOMAT (Calculation Verification)
| Check | Description |
|---|---|
| `C4_CITATION_RULE` | Every deduction must cite a valid policy clause |
| `C5_RECOMPUTE_RULE` | Independently recompute each deduction (verify LLM math) |
| `C6_IDENTITY` | `payable = bill_total − total_deductions` |
| `C7_PED_LINKAGE` | Pre-existing disease deductions must have supporting evidence |

---

## 🖥️ Web Dashboard

A premium animated Next.js dashboard that runs the full pipeline visually.

![Dashboard Preview](./web/.next/static/media/screenshot.png)

**Features:**
- Real-time pipeline execution with live agent trace log
- Three demo scenarios: Clean Run / Room Rent Misread / Missing Citation
- Gate bounce animation with structured feedback display
- Settlement breakdown with chart visualization
- Fraud risk gauge panel

**Stack:** Next.js 14 · TypeScript · Tailwind CSS · Framer Motion · Recharts · FastAPI

---

## 🚀 Deploy to Vercel

The Next.js frontend deploys directly to Vercel. The Python backend must run separately.

```bash
npm install -g vercel
vercel   # from repo root — vercel.json handles the web/ subdirectory
```

Or click: [![Deploy with Vercel](https://vercel.com/button)](https://vercel.com/new/clone?repository-url=https://github.com/KEERTHIVASAN-SKV/DIPLOMAT)

Set the environment variable in Vercel:
- `NEXT_PUBLIC_API_URL` → your deployed Python backend URL

See [HOW_TO_START.md §5](./HOW_TO_START.md#5-deploy-to-vercel-frontend-only) for full Vercel + Railway setup instructions.

---

## 📁 Project Structure

```
DIPLOMAT/
├── .env.example          # Environment variable template
├── vercel.json           # Vercel config (root → web/)
├── HOW_TO_START.md       # Full setup + deployment guide
├── requirements.txt      # Python dependencies
├── demo.py               # CLI pipeline demo
│
├── agents/               # IntakeAgent, AdjudicatorAgent, PolicyEngine
├── diplomat/             # Validation gates (Veritas, Diplomat) + validators
├── models/               # Pydantic data models
├── orchestrator/         # Pipeline with retry loops + feedback
├── demo_data/            # Medical claim JSON docs (bill, discharge, policy)
├── dashboard/            # Streamlit visual demo (alternative to web/)
│
└── web/                  # Next.js frontend
    ├── app/              # App Router pages
    ├── components/       # React UI components (10 components)
    ├── api/              # FastAPI backend wrapper (Python)
    └── next.config.js    # API URL configurable via NEXT_PUBLIC_API_URL
```

> **Legacy/Prototypes** (not used in main demo): `contracts/`, `test_claims/`, `main.py`

---

## ⚙️ Environment Variables

### Python Backend

| Variable | Default | Description |
|---|---|---|
| `GOOGLE_API_KEY` | — | Gemini API key (required for live LLM mode) |
| `GEMINI_MODEL` | `gemini-3.5-flash-lite` | Model to use (confirmed working on free tier) |
| `MOCK_MODE` | `true` | `true` = no API key needed; `false` = live Gemini calls |

> ⚠️ Do **NOT** use deprecated models: `gemini-1.5-flash`, `gemini-2.5-flash`, `gemini-3.6-flash` — these either 404 or hit tiny quota caps.

### Next.js Frontend

| Variable | Default | Description |
|---|---|---|
| `NEXT_PUBLIC_API_URL` | `http://localhost:8000` | URL of the Python FastAPI backend |

---

## 🎭 Demo Scenarios

| Scenario | Fault Injected | Expected Outcome |
|---|---|---|
| Clean Run | None | ✅ APPROVED — all gates pass |
| Room Rent Misread | Gate 1 OCR error | 🔄 Retry with feedback → corrected |
| Missing Citation | Gate 2 calc error | 🔄 Retry with feedback → corrected or 🚨 ESCALATED_TO_HUMAN |
