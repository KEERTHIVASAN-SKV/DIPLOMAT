"""
DIPLOMAT FastAPI Backend
========================
Wraps the existing InsurancePipeline for the Next.js frontend.

Run with:
    uvicorn web.api.server:app --reload --port 8000
or from project root:
    python -m uvicorn web.api.server:app --reload --port 8000
"""

import json
import sys
import os
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional

# ── path bootstrap ──────────────────────────────────────────────────────────
ROOT = Path(__file__).parent.parent.parent  # diplomat/
sys.path.insert(0, str(ROOT))

from orchestrator.pipeline import InsurancePipeline

DATA_DIR = ROOT / "demo_data"

app = FastAPI(title="DIPLOMAT API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── helpers ─────────────────────────────────────────────────────────────────
def load_demo_data():
    with open(DATA_DIR / "policy.json", encoding="utf-8") as f:
        policy = json.load(f)
    with open(DATA_DIR / "bill.json", encoding="utf-8") as f:
        bill = json.load(f)
    with open(DATA_DIR / "discharge_summary.json", encoding="utf-8") as f:
        discharge = json.load(f)
    return policy, bill, discharge


# ── request / response models ────────────────────────────────────────────────
class RunRequest(BaseModel):
    inject_fault: Optional[str] = None


# ── routes ───────────────────────────────────────────────────────────────────
@app.get("/api/claim-data")
def get_claim_data():
    """Return the demo bill, discharge summary, and policy for display."""
    policy, bill, discharge = load_demo_data()
    return {
        "bill": bill,
        "discharge": discharge,
        "policy": policy,
    }


@app.post("/api/run")
def run_pipeline(req: RunRequest):
    """
    Run the InsurancePipeline and return the full result with trace.
    inject_fault: None | "room_rent_misread" | "missing_citation"
    """
    policy, bill, discharge = load_demo_data()
    pipeline = InsurancePipeline(policy, use_gates=True, max_retries=2)
    result = pipeline.process(bill, discharge, inject_fault=req.inject_fault)
    return result


@app.get("/api/health")
def health():
    return {"status": "ok", "service": "DIPLOMAT API"}
