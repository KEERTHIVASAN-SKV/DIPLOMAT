# 🚀 How to Start — DIPLOMAT

A step-by-step guide to run DIPLOMAT locally and deploy it to Vercel.

---

## Prerequisites

| Tool | Version | Notes |
|---|---|---|
| Python | ≥ 3.10 | [python.org](https://www.python.org/downloads/) |
| Node.js | ≥ 18 | [nodejs.org](https://nodejs.org/) |
| npm | ≥ 9 | Bundled with Node.js |
| Git | Any | [git-scm.com](https://git-scm.com/) |
| Google API Key | — | [aistudio.google.com](https://aistudio.google.com/) *(optional for mock mode)* |

---

## 1. Clone the Repository

```bash
git clone https://github.com/KEERTHIVASAN-SKV/DIPLOMAT.git
cd DIPLOMAT
```

---

## 2. Set Up the Python Backend

### 2a. Create a virtual environment

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS / Linux
python3 -m venv venv
source venv/bin/activate
```

### 2b. Install Python dependencies

```bash
pip install -r requirements.txt
```

### 2c. Configure environment variables

```bash
# Windows
copy .env.example .env

# macOS / Linux
cp .env.example .env
```

Then open `.env` and fill in your values:

```env
# Required only for live LLM mode
GOOGLE_API_KEY=your-api-key-here

# Confirmed working on free tier (do NOT use deprecated models)
GEMINI_MODEL=gemini-3.5-flash-lite

# true = no API key needed (deterministic mock responses)
# false = real Gemini API calls
MOCK_MODE=true
```

> **Tip:** Keep `MOCK_MODE=true` to run locally without any API key.

### 2d. Run the Python demo (CLI)

```bash
python demo.py
```

This processes a health insurance claim through the full pipeline and prints the validation trace.

### 2e. (Optional) Start the Streamlit visual dashboard

```bash
streamlit run dashboard/app.py
```

Open [http://localhost:8501](http://localhost:8501) in your browser.

### 2f. Start the FastAPI backend (for the Next.js web UI)

```bash
# Install FastAPI & uvicorn first
pip install fastapi uvicorn

# Start the server
uvicorn web.api.server:app --reload --port 8000
```

The API will be available at [http://localhost:8000](http://localhost:8000).
Health check: [http://localhost:8000/api/health](http://localhost:8000/api/health)

---

## 3. Set Up the Next.js Frontend

Open a **new terminal** (keep the Python server running):

```bash
cd web
npm install
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) — the animated dashboard is live!

> The frontend talks to the Python backend at `http://localhost:8000` by default.
> To change this, set `NEXT_PUBLIC_API_URL` in `web/.env.local`.

---

## 4. Running Demo Scenarios

From the web dashboard, you can trigger three scenarios:

| Scenario | What it tests |
|---|---|
| **Clean Run** | Normal happy-path claim (LLM may still make recoverable mistakes) |
| **Room Rent Misread** | OCR-style error → Gate 1 bounce + feedback correction |
| **Missing Citation** | Calculation error → Gate 2 bounce + feedback correction |

From the CLI:
```bash
python demo.py                    # clean run
python demo.py room_rent_misread  # inject fault 1
python demo.py missing_citation   # inject fault 2
```

---

## 5. Deploy to Vercel (Frontend Only)

> **Note:** Vercel deploys the Next.js frontend only. The Python backend must be hosted separately (e.g., [Railway](https://railway.app), [Render](https://render.com), or kept local).

### Option A — Vercel CLI

```bash
# Install Vercel CLI
npm install -g vercel

# From the repo root
vercel

# Follow the prompts:
# - Link to your Vercel account
# - Set root directory to: web
# - Framework: Next.js (auto-detected)
```

### Option B — Vercel Dashboard (Recommended)

1. Go to [vercel.com/new](https://vercel.com/new)
2. Import the GitHub repo `KEERTHIVASAN-SKV/DIPLOMAT`
3. Vercel will auto-detect `vercel.json` and set `web/` as the root
4. Add environment variable:
   - **Name:** `NEXT_PUBLIC_API_URL`
   - **Value:** your deployed Python backend URL (e.g., `https://diplomat-api.railway.app`)
5. Click **Deploy**

### Setting up the Python backend on Railway

1. Go to [railway.app](https://railway.app) → New Project → Deploy from GitHub Repo
2. Select `KEERTHIVASAN-SKV/DIPLOMAT`
3. Add a service with start command:
   ```
   pip install fastapi uvicorn google-generativeai pydantic python-dotenv && uvicorn web.api.server:app --host 0.0.0.0 --port $PORT
   ```
4. Add environment variables: `GOOGLE_API_KEY`, `GEMINI_MODEL`, `MOCK_MODE`
5. Copy the Railway URL → paste as `NEXT_PUBLIC_API_URL` in Vercel

---

## 6. Environment Variables Reference

### Python Backend (`.env`)

| Variable | Default | Required | Description |
|---|---|---|---|
| `GOOGLE_API_KEY` | — | Only if `MOCK_MODE=false` | Gemini API key |
| `GEMINI_MODEL` | `gemini-3.5-flash-lite` | No | Which Gemini model to use |
| `MOCK_MODE` | `true` | No | `true` = mock, `false` = live LLM |

### Next.js Frontend (`web/.env.local`)

| Variable | Default | Description |
|---|---|---|
| `NEXT_PUBLIC_API_URL` | `http://localhost:8000` | URL of the Python FastAPI backend |

---

## 7. Troubleshooting

### `ModuleNotFoundError: No module named 'fastapi'`
```bash
pip install fastapi uvicorn
```

### `CORS error` in browser console
Make sure the FastAPI server is running and `NEXT_PUBLIC_API_URL` matches exactly (no trailing slash).

### `404 on Gemini model`
Deprecated models (`gemini-1.5-flash`, `gemini-2.5-flash`, `gemini-3.6-flash`) don't work on new accounts. Use `gemini-3.5-flash-lite`.

### `Port 3000 already in use`
```bash
# Windows
netstat -ano | findstr :3000
taskkill /PID <PID> /F
```

### `Build fails on Vercel`
- Make sure `vercel.json` is at the repo root
- Confirm `web/package.json` exists and is valid
- Check Vercel build logs for missing env variables

---

## 8. Project Layout

```
DIPLOMAT/
├── .env.example          # Environment variable template
├── .gitignore            # Comprehensive ignore patterns
├── vercel.json           # Vercel deployment config (root → web/)
├── HOW_TO_START.md       # This file
├── README.md             # Project overview
├── requirements.txt      # Python dependencies
├── demo.py               # CLI demo runner
├── main.py               # Earlier CLI (legacy)
│
├── agents/               # IntakeAgent, AdjudicatorAgent, PolicyEngine
├── diplomat/             # Validation gates (Veritas, Diplomat) + validators
├── models/               # Pydantic data models
├── orchestrator/         # Pipeline with retry loops + feedback
├── demo_data/            # Medical claim documents (bill, discharge, policy)
├── dashboard/            # Streamlit visual demo
├── diagnostics/          # Debug scripts (dev only)
│
└── web/                  # Next.js frontend dashboard
    ├── app/              # Next.js App Router pages
    ├── components/       # React UI components
    ├── api/              # FastAPI backend wrapper (Python)
    ├── next.config.js    # Next.js config (API URL via env)
    └── package.json      # Node dependencies
```
