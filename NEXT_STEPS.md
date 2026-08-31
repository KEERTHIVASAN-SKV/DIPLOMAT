# DIPLOMAT — Remaining Work to Finish

Status snapshot: the core trust-layer logic works with real LLM calls. What's left is mostly UI, cleanup, and polish. No architecture changes needed below.

---

## 1. Rebuild the dashboard (biggest remaining task)

`dashboard/app.py` does not work. It was built against an abandoned pipeline API (`pipeline.run()`, `result.handoff_log`, `DiplomatStatus`, reading from `test_claims/*.json`) that has nothing to do with the real, working code. It has never run successfully.

The real, working pipeline is `orchestrator/pipeline.py`'s `InsurancePipeline`, constructed as `InsurancePipeline(policy_doc)` and called via `.process(bill_doc, discharge_doc, inject_fault=...)` — exactly how `demo.py` already uses it. `demo.py` is the reference implementation to copy from.

**Paste this into Kiro/Sonnet (needs judgment, not mechanical — spend real credits here):**

```
Rewrite dashboard/app.py from scratch. The current file is built against an 
abandoned pipeline API (pipeline.run(), result.handoff_log, DiplomatStatus, 
test_claims/*.json for motor insurance) that doesn't match the real, working 
code. Ignore it as reference except for the CSS block, which is fine to reuse.

The real, working pipeline is orchestrator/pipeline.py's InsurancePipeline, 
constructed as InsurancePipeline(policy_doc), called via .process(bill_doc, 
discharge_doc, inject_fault=...), matching exactly how demo.py already uses it 
(demo.py is the reference implementation — read it first).

Build a Streamlit dashboard with:
1. A dropdown to pick one of the three demo.py scenarios (or a "no fault injection" 
   clean run)
2. A "Run claim" button that calls pipeline.process() with the selected inject_fault
3. A horizontal agent-flow row showing: Intake → Veritas Gate → Policy Engine → 
   Adjudicator → Diplomat Gate → Settlement, with each agent box showing its 
   _extraction_method / _adjudication_method tag (llm vs mock) and each gate 
   showing PASS/BOUNCE with attempt number
4. When a gate bounces, show the actual bounce dict content (check name, expected 
   vs got) in a small feedback panel, so the audience can see what was sent back 
   to the agent on retry
5. A final settlement card showing bill_total, each deduction with its clause_id, 
   total_deductions, payable

Reuse the existing dark theme CSS classes (diplomat-header, agent-box, 
diplomat-gate-pass/fail/review, success-card) from the current file — keep that 
visual style, just rewire the data flow to match the real pipeline.

Read demo_data/*.json to confirm what shape bill_doc/discharge_doc/policy_doc take.

Show me the complete new file before I run it.
```

Then run `streamlit run dashboard/app.py` and confirm it actually renders and processes a claim before trusting it.

**If there's no time for this:** fall back to presenting `demo.py`'s CLI trace output directly, narrated live. It's a completely legitimate demo format — don't panic-build a broken UI under time pressure.

---

## 2. Fix the dishonest scenario label (5 min, mechanical — use MiniMax)

`demo.py`'s Scenario 3 is currently labeled `"Clean claim — no fault injection, first-try APPROVED"`. With real Gemini calls, it took 3 attempts in the last confirmed run, not one — the label is currently false and a grader could catch it instantly.

```
In demo.py, rename Scenario 3's label from "Clean claim — no fault injection, 
first-try APPROVED" to "Clean claim — no fault injection" (remove the "first-try 
APPROVED" claim since with real LLM variance, it isn't guaranteed to pass on 
attempt 1 every run). Use MiniMax, mechanical text change only.
```

---

## 3. Clean up scratch/diagnostic files (5 min, mechanical)

`test_real_llm.py`, `test_api_key.py`, and `VERIFICATION_REPORT.md` were created mid-session purely for debugging whether real LLM calls were happening. They're not part of the core deliverable.

Either delete them, or move them into a clearly-labeled folder:
```
Move test_real_llm.py, test_api_key.py, and VERIFICATION_REPORT.md into a new 
diagnostics/ folder, and add a one-line note in README.md that this folder holds 
debugging scripts used during development, not part of the core pipeline.
```

---

## 4. Update README's model instructions (2 min, mechanical)

The README/`.env.example` may still reference deprecated model names (`gemini-1.5-flash`, `gemini-2.5-flash`, etc.) from earlier in development. Confirmed working model: `gemini-3.5-flash-lite`.

```
Update README.md and .env.example so GEMINI_MODEL is documented as 
gemini-3.5-flash-lite (confirmed working on the free tier). Remove any 
references to gemini-1.5-flash, gemini-2.5-flash, or gemini-3.6-flash as the 
recommended model — those either 404 on new accounts or hit tiny free-tier 
quota caps (20 requests/day).
```

---

## 5. Known gap — low priority, don't fix unless time remains

Neither `IntakeAgent` nor `AdjudicatorAgent` ever populates the `ped_evidence` field for pre-existing-disease deductions, so `DiplomatGate`'s C7_PED_LINKAGE check has never actually been exercised by a real claim. This was true before any of this session's changes too — not something introduced.

Not worth fixing under time pressure. If asked about it, the honest answer is: "this is a known limitation, the R5/PED path exists in the gate but isn't currently reachable by either agent's output — noted as a next-phase item."

---

## 6. Be ready for one likely Q&A question

**Likely question:** "DiplomatGate already independently recomputes the correct deduction — why does the AdjudicatorAgent need to be an LLM at all? Isn't the gate doing all the real work?"

**Honest answer to have ready:** In this specific claim type, the deduction math is fully deterministic, so yes — the gate could just supply the correct value directly, and in a narrower system it might. The point being demonstrated here is the general pattern: untrusted agent output → independent verification → bounce with a specific reason → retry with that reason as feedback → escalate to a human if it still doesn't converge. That pattern is valuable specifically in domains where the verifier can check consistency but can't independently derive the full right answer — e.g. contested medical necessity, ambiguous document interpretation. This project picked a fully-checkable financial domain because it's demoable and provable end-to-end, not because it's the hardest possible case for the pattern.

---

## What NOT to touch — already correct, don't second-guess it

- `diplomat/veritas.py`, `diplomat/diplomat.py` — gate logic is solid, don't modify
- `agents/intake_agent.py`, `agents/adjudicator_agent.py` — LLM integration, mock fallback, retry-with-feedback, and method tagging (`_extraction_method`/`_adjudication_method`) are all correct
- `orchestrator/pipeline.py` — retry loop with bounce-feedback threading is correct
- `models/*.py`, `contracts/*.json`, `demo_data/*.json` — fine as-is
- `main.py`, `test_claims/` — confirmed leftovers from an earlier, incompatible motor-insurance prototype; already marked deprecated in README, safe to ignore entirely

---

## Presentation framing to remember

- Claim documents are synthetic/mock — completely normal for a hackathon prototype, already disclosed in the README, don't be defensive about it
- The LLM reasoning is 100% real — confirmed via actual API calls, real quota exhaustion errors, real 404s on wrong model names, and unscripted arithmetic mistakes (a consistent ₹30,000 vs ₹45,000 pattern suggesting the model miscounts a days-multiplier — a good, specific detail to mention rather than vague "sometimes it's wrong")
- The narrative arc for a live demo: one claim that sails through, one that gets caught and self-corrects via bounce feedback, one that exhausts retries and correctly escalates to human review — that three-beat structure is the whole pitch
