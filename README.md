# 🛂 DIPLOMAT

## **Fail-Closed Trust & Verification Layer for Insurance AI Agents**

> **DIPLOMAT** — *Data Integrity, Policy Logic, Output Validation & Agent Trust*

DIPLOMAT is a trust and verification layer designed for **AI-driven insurance claim processing**.

Instead of allowing one AI component to blindly trust the output of another, DIPLOMAT places deterministic validation gates between critical stages of the claim workflow.

It verifies:

* extracted claim information
* source evidence
* policy rules
* cross-document consistency
* agent outputs
* deduction calculations
* financial identities
* policy citations
* high-risk decisions

If a handoff violates a rule, the system **fails closed**: the output is rejected, the error is returned to the responsible component for correction, and after repeated failures the workflow is escalated to human review.

---

# 🎯 Problem

AI agents are increasingly being used to automate complex financial workflows.

Insurance claims are particularly sensitive because a single incorrect extraction or calculation can result in:

* incorrect claim amounts
* invalid deductions
* unsupported policy decisions
* incorrect patient information
* hallucinated evidence
* inconsistent policy interpretation
* financial loss
* unfair claim rejection

A conventional AI pipeline may look like:

```text
Document
   ↓
AI Agent
   ↓
AI Agent
   ↓
AI Agent
   ↓
Settlement
```

The problem is that **each downstream component may trust the previous component's output**.

If the first agent makes a mistake:

```text
Incorrect extraction
       ↓
Incorrect policy interpretation
       ↓
Incorrect deduction
       ↓
Incorrect settlement
       ↓
Financial loss
```

DIPLOMAT introduces a verification layer between these stages.

---

# 💡 Solution

DIPLOMAT uses a **fail-closed architecture**.

```text
                  INSURANCE CLAIM
                        │
                        ▼
                 ┌─────────────┐
                 │ Intake Agent│
                 └──────┬──────┘
                        │
                        ▼
                 ┌─────────────┐
                 │   VERITAS   │
                 │ Input Gate  │
                 └──────┬──────┘
                        │
                     PASS
                        │
                        ▼
                 ┌─────────────┐
                 │ PolicyEngine│
                 └──────┬──────┘
                        │
                        ▼
                 ┌─────────────┐
                 │ Adjudicator │
                 │    Agent    │
                 └──────┬──────┘
                        │
                        ▼
                 ┌─────────────┐
                 │   DIPLOMAT  │
                 │ Output Gate │
                 └──────┬──────┘
                        │
                  ┌─────┴─────┐
                  │           │
                PASS        FAIL
                  │           │
                  ▼           ▼
             Settlement    Retry
                              │
                              ▼
                           Retry limit
                              │
                              ▼
                         Human Review
```

The current repository implements this workflow using an intake component, deterministic policy engine, adjudication component, Veritas input validation, DIPLOMAT output validation, retry loops, and human escalation.

---

# 🧠 Core Principle

## **Never trust an agent output blindly.**

Every critical handoff should answer:

> **Is this information complete, consistent, supported by evidence, and financially valid?**

If the answer is no:

```text
❌ BLOCK
```

If the answer is yes:

```text
✅ CONTINUE
```

---

# 🏗️ Current Architecture

```text
                         CUSTOMER / CLAIM
                                │
                                ▼
                    ┌─────────────────────┐
                    │    INTAKE AGENT     │
                    │                     │
                    │ Document extraction │
                    │ + source citations  │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │   VERITAS GATE      │
                    │                     │
                    │ Input verification  │
                    └──────────┬──────────┘
                               │
                         ┌─────┴─────┐
                         │           │
                       FAIL         PASS
                         │           │
                         ▼           ▼
                      RETRY     POLICY ENGINE
                                     │
                                     ▼
                              Applicable Rules
                                     │
                                     ▼
                           ┌─────────────────┐
                           │ ADJUDICATOR     │
                           │     AGENT       │
                           │                 │
                           │ Calculate       │
                           │ deductions      │
                           │ + payable       │
                           └────────┬────────┘
                                    │
                                    ▼
                           ┌─────────────────┐
                           │ DIPLOMAT GATE   │
                           │                 │
                           │ Output / trust  │
                           │ verification    │
                           └────────┬────────┘
                                    │
                              ┌─────┴─────┐
                              │           │
                            FAIL         PASS
                              │           │
                              ▼           ▼
                           RETRY      APPROVED
                              │
                         retry limit
                              │
                              ▼
                       HUMAN REVIEW
```

The repository's current orchestrator explicitly implements retry loops around the Veritas and DIPLOMAT gates.

---

# 🔐 DIPLOMAT's Trust Model

DIPLOMAT currently performs seven major validation categories.

| # | Validation              | Purpose                                       |
| - | ----------------------- | --------------------------------------------- |
| 1 | Required Fields         | Ensure mandatory information exists           |
| 2 | Data Types              | Ensure values have correct types              |
| 3 | Formats                 | Validate dates, enums and currency            |
| 4 | Semantic Meaning        | Ensure values have meaningful context         |
| 5 | Cross-Agent Consistency | Detect contradictory information              |
| 6 | Evidence                | Require evidence for risk-sensitive decisions |
| 7 | Financial Rules         | Verify calculations and financial constraints |

The gateway constructs these seven validators and fails on the first violation.

---

# 🔎 1. Required Field Validation

A claim should not continue if required information is missing.

Example:

```json
{
  "policy_id": "POL-001",
  "patient_name": "Kumar"
}
```

If the contract requires an admission date:

```text
❌ REQUIRED FIELD MISSING

field:
admission_date

action:
BLOCK / RETRY
```

---

# 🔢 2. Data Type Validation

The system verifies that values match their expected data types.

Example:

```json
{
  "bill_total": "150000"
}
```

when the expected type is numeric.

Result:

```text
❌ TYPE MISMATCH
```

This prevents malformed data from propagating downstream.

---

# 📅 3. Format Validation

DIPLOMAT validates standardized representations such as:

```text
Dates:
YYYY-MM-DD

Currency:
INR

Enums:
ACTIVE
EXPIRED
CANCELLED
...
```

The current configuration defines INR as the required currency and maintains allowed incident types, policy statuses and risk levels.

---

# 🧠 4. Semantic Validation

Syntactically valid data can still be meaningless.

For example:

```text
amount = 60000
```

is not enough.

The system needs to understand:

```text
amount
+ currency
+ source
+ purpose
```

DIPLOMAT therefore treats semantic context as a separate validation layer.

---

# 🔄 5. Cross-Source / Cross-Agent Consistency

Information extracted from different sources must agree.

Example:

```text
Bill:
Patient = Kumar

Discharge Summary:
Patient = Kumar

Extraction:
Patient = Raj
```

The system detects:

```text
❌ PATIENT NAME MISMATCH
```

The current Veritas gate performs cross-document checks for patient names and admission dates.

---

# 📑 6. Evidence Validation

Important decisions should have supporting evidence.

For example, a deduction should not simply say:

```text
Deduction = ₹10,000
```

It should be traceable to a policy rule and calculation.

DIPLOMAT's financial validation also requires policy clause identifiers for deductions.

Example:

```json
{
  "deduction_id": "D1",
  "amount": 10000,
  "clause_id": "R1",
  "calculation": "(actual rate - allowed rate) × days"
}
```

The gateway verifies that the referenced clause actually exists in the policy rule registry.

---

# 💰 7. Financial Validation

Financial calculations are not delegated entirely to an LLM.

DIPLOMAT independently checks important identities.

For example:

```text
Payable =
Bill Total - Total Deductions
```

If:

```text
Bill Total       = ₹100,000
Deductions       = ₹20,000
Payable reported = ₹95,000
```

DIPLOMAT calculates:

```text
Expected payable = ₹80,000

Reported payable = ₹95,000

Difference       = ₹15,000

❌ BLOCK
```

The current `DiplomatGate` independently recomputes deductions and the final payable amount.

---

# 🛡️ VERITAS — Input Verification Gate

DIPLOMAT currently has a separate **Veritas Gate** for validating extracted information before it reaches the policy/adjudication stages.

Veritas is specifically designed to catch document/extraction errors before they propagate into financial calculations.

It currently checks:

### Bill integrity

```text
sum(line_items) == bill_total
```

### Cross-document admission date

```text
bill_date
     ==
discharge_date
     ==
extracted_date
```

### Cross-document patient identity

```text
bill_patient
     ==
discharge_patient
     ==
extracted_patient
```

### Source citation

Extracted values must be traceable to their source.

### Policy linkage

The extracted policy ID must correspond to the supplied policy.

---

# 🤖 Current Agent / Processing Components

The current codebase contains three primary processing components under `agents/`:

```text
agents/
├── intake_agent.py
├── policy_engine.py
└── adjudicator_agent.py
```

The repository's current implementation therefore differs from an architecture containing five fully independent LLM agents.

---

## 1. Intake Agent

The `IntakeAgent` converts policy, bill and discharge information into structured claim data.

Each extracted field includes:

```text
value
source
page
```

For example:

```json
{
  "room_rent_per_day": {
    "value": 5000,
    "source": "Bill: room_rent_per_day=5000",
    "page": 1
  }
}
```

This source-aware representation is particularly important because later verification can determine whether an extracted value is supported by the original source.

---

# 2. Policy Engine

The Policy Engine is intentionally deterministic.

The code explicitly describes it as:

> **Pure lookup table for policy rules — NO LLM**

It converts policy configuration into a rule registry.

Current rule examples include:

```text
R1 → Room rent sublimit
R2 → Proportionate deduction
R3 → Non-payable items
R4 → Copay
R5 → Pre-existing disease waiting period
```

The engine then determines which rules apply to the current claim.

---

# 3. Adjudicator Agent

The Adjudicator calculates:

```text
Bill total
+
Applicable deductions
+
Total deductions
+
Payable amount
+
Remaining sum insured
```

It independently performs calculations rather than relying on an LLM to produce the financial result.

Example:

```text
Bill Total
₹100,000

Room Rent Deduction
₹10,000

Non-payable Items
₹5,000

Copay
₹8,500

──────────────────

Total Deductions
₹23,500

Payable
₹76,500
```

---

# 🔁 Feedback & Retry System

DIPLOMAT does not simply stop when a validation error occurs.

The current pipeline implements a feedback loop.

```text
             Agent
               │
               ▼
            Validator
               │
        ┌──────┴──────┐
        │             │
       PASS          FAIL
        │             │
        ▼             ▼
      NEXT          BOUNCE
                      │
                      ▼
                 Same Agent
                      │
                      ▼
                    RETRY
```

The pipeline supports configurable retries and records every attempt in a trace.

Default:

```text
max_retries = 2
```

If the system still cannot produce a valid output:

```text
❌ ESCALATED_TO_HUMAN
```

---

# 🧑‍⚖️ Human Escalation

DIPLOMAT is not designed to blindly automate every financial decision.

The gateway can escalate situations such as:

### High fraud risk

```text
risk_score >= configured threshold
```

### Agent-requested human review

```text
recommendation = HUMAN_REVIEW
```

### High-value claims

```text
claim amount >= configured threshold
```

The current configuration sets:

```text
HIGH_VALUE_THRESHOLD = ₹500,000
HIGH_RISK_SCORE_THRESHOLD = 0.75
```

and the gateway converts these cases to `HUMAN_REVIEW`.

---

# 🧪 Fault Injection & Testing

One of the strongest aspects of the current prototype is that it deliberately creates bad data to demonstrate that the verification system catches it.

The Intake Agent supports injected faults such as:

```text
room_rent_misread
missing_date
ped_hallucination
```

The Adjudicator supports faults such as:

```text
missing_citation
wrong_proportion
wrong_ped_link
```

This makes the system suitable for demonstrating:

> **"What happens when an AI makes a mistake?"**

rather than only demonstrating successful claims.

---

# 🧪 Demo Scenarios

The current repository documents six demonstration cases:

| Scenario          | Expected Result | Failure               |
| ----------------- | --------------- | --------------------- |
| Valid motor claim | ✅ Approved      | —                     |
| Amount mismatch   | 🚨 Blocked      | Financial validation  |
| Expired policy    | 🚨 Blocked      | Financial/policy rule |
| Missing currency  | 🚨 Blocked      | Required field        |
| Currency conflict | 🚨 Blocked      | Consistency           |
| High-risk claim   | 🤚 Human review | Escalation            |

These scenarios are included specifically to demonstrate the fail-closed behavior.

---

# 📊 Complete Execution Flow

A claim currently travels through the following process:

```text
                CLAIM DOCUMENTS
                      │
                      ▼
                INTAKE AGENT
                      │
                      │ structured extraction
                      ▼
                 VERITAS GATE
                      │
          ┌───────────┴───────────┐
          │                       │
       INVALID                  VALID
          │                       │
          ▼                       ▼
        RETRY               POLICY ENGINE
                                  │
                                  │ applicable rules
                                  ▼
                            ADJUDICATOR
                                  │
                                  │ settlement
                                  ▼
                           DIPLOMAT GATE
                                  │
                    ┌─────────────┼─────────────┐
                    │             │             │
                 REJECT        HUMAN          PASS
                    │           REVIEW          │
                    ▼             │              ▼
                  RETRY           │          APPROVED
                    │             │
                    └─────────────┘
```

This flow is implemented in `orchestrator/pipeline.py`.

---

# 🧾 Example Claim

Consider:

```text
Policy:
POL-1001

Patient:
Kumar

Room Rent:
₹7,000/day

Allowed Room Rent:
₹5,000/day

Duration:
3 days

Hospital Bill:
₹100,000
```

The system calculates:

```text
Room rent excess:

(₹7,000 - ₹5,000) × 3

= ₹6,000 deduction
```

The Adjudicator creates a deduction with:

```text
deduction_id
clause_id
amount
category
base_amount
calculation
```

DIPLOMAT independently verifies that:

```text
clause_id exists
        +
calculation is correct
        +
deduction amount is correct
        +
payable = bill - deductions
```

The corresponding implementation exists in the adjudicator and DIPLOMAT calculation gate.

---

# 🗂️ Project Structure

```text
DIPLOMAT/
│
├── agents/
│   ├── __init__.py
│   ├── intake_agent.py
│   ├── policy_engine.py
│   └── adjudicator_agent.py
│
├── contracts/
│   └── *.json
│
├── diplomat/
│   ├── __init__.py
│   ├── diplomat.py
│   ├── gateway.py
│   ├── veritas.py
│   └── validators/
│       ├── field_validator.py
│       ├── type_validator.py
│       ├── format_validator.py
│       ├── semantic_validator.py
│       ├── consistency_validator.py
│       ├── evidence_validator.py
│       └── financial_validator.py
│
├── models/
│   └── diplomat_models.py
│
├── orchestrator/
│   └── pipeline.py
│
├── test_claims/
│   └── demo scenarios
│
├── dashboard/
│   └── app.py
│
├── demo_data/
│   └── sample documents
│
├── config.py
├── demo.py
├── main.py
├── requirements.txt
└── .env.example
```

The repository currently exposes these top-level components and describes the dashboard, demo data, contracts, models and orchestration structure.

---

# 🔌 Configuration

Create a `.env` file:

```env
GOOGLE_API_KEY=
GEMINI_MODEL=gemini-1.5-flash
MOCK_MODE=true
```

Current configuration includes:

```text
GOOGLE_API_KEY
GEMINI_MODEL
MOCK_MODE
HIGH_VALUE_THRESHOLD
HIGH_RISK_SCORE_THRESHOLD
REQUIRED_CURRENCY
VALID_INCIDENT_TYPES
VALID_POLICY_STATUSES
VALID_RISK_LEVELS
```

---

# 🚀 Installation

## 1. Clone

```bash
git clone https://github.com/KEERTHIVASAN-SKV/DIPLOMAT.git
cd DIPLOMAT
```

## 2. Create virtual environment

### Windows

```bash
python -m venv .venv
.venv\Scripts\activate
```

### Linux / macOS

```bash
python -m venv .venv
source .venv/bin/activate
```

## 3. Install dependencies

```bash
pip install -r requirements.txt
```

## 4. Configure environment

```bash
copy .env.example .env
```

or on Linux/macOS:

```bash
cp .env.example .env
```

The repository currently defaults to mock mode, so the demo can run without an external API key.

---

# ▶️ Running the Project

## CLI Demo

```bash
python main.py
```

The documented demo runs the available claim scenarios.

## Dashboard

```bash
streamlit run dashboard/app.py
```

The repository includes a Streamlit dashboard for visualizing the workflow.

---

# 🧠 Design Philosophy

DIPLOMAT follows five core principles.

### 1. Fail Closed

Invalid information should not continue downstream.

```text
Invalid
   ↓
BLOCK
```

### 2. Deterministic Verification

Critical financial calculations should be independently verified rather than blindly trusted from an LLM.

### 3. Evidence First

Important decisions should be traceable to supporting information.

### 4. Explicit Policy Rules

Policy logic should be represented as machine-readable rules.

### 5. Human Escalation

The system should know when autonomous processing is inappropriate.

---

# 🆚 What Makes DIPLOMAT Different?

A conventional AI insurance workflow:

```text
Document
   ↓
LLM
   ↓
Decision
```

DIPLOMAT:

```text
Document
   ↓
Extraction
   ↓
Verification
   ↓
Policy Rules
   ↓
Calculation
   ↓
Independent Validation
   ↓
Risk Check
   ↓
Human Escalation when necessary
```

The key idea is:

> **AI can make decisions, but AI-generated decisions should not automatically become trusted financial facts.**

---

# ⚠️ Current Limitations

DIPLOMAT is currently a **prototype/hackathon implementation**.

The current repository should not be represented as a production insurance claims platform.

Current limitations include:

* The workflow is primarily sequential.
* Agent discovery is not yet implemented.
* There is no independent agent identity system.
* There is no agent reputation mechanism.
* Agent-to-agent communication is currently orchestrated rather than a decentralized messaging protocol.
* There is no autonomous agent negotiation layer.
* Persistent long-term agent memory is not yet implemented.
* The current policy model is focused on a limited claim scenario.
* External insurer/TPA/hospital integrations are not implemented.
* Document ingestion is currently represented using structured document data.
* The current implementation focuses heavily on deterministic validation rather than a fully autonomous agent swarm.

These limitations are also the natural areas for the next stage of the project.

---

# 🚀 Future Roadmap

## Phase 1 — Multi-Insurance Support

Extend the rule system to:

```text
Motor
Health
Life
Travel
Property
Business
```

Instead of building separate systems, maintain a common DIPLOMAT protocol with domain-specific policy rules.

---

## Phase 2 — Agent Communication Protocol

Introduce structured agent messages:

```json
{
  "message_id": "MSG-001",
  "sender": "intake_agent",
  "receiver": "policy_agent",
  "intent": "VERIFY_COVERAGE",
  "claim_id": "CLM-001",
  "payload": {},
  "evidence": [],
  "confidence": 0.94,
  "constraints": {}
}
```

DIPLOMAT would validate the message before delivery.

---

## Phase 3 — Agent Discovery

Allow agents to discover other agents based on capabilities.

Example:

```text
Need:
MEDICAL_DOCUMENT_VERIFICATION

DIPLOMAT Registry:

MedicalAgent-A
Capability: MEDICAL_DOCUMENT_VERIFICATION
Reliability: 96%

MedicalAgent-B
Capability: MEDICAL_DOCUMENT_VERIFICATION
Reliability: 89%
```

The requesting agent selects the most appropriate agent.

---

## Phase 4 — Agent Reputation

Track:

```text
successful tasks
failed tasks
validation failures
response time
evidence quality
historical accuracy
```

This creates an agent reputation layer.

---

## Phase 5 — Negotiating Agents

Allow agents to disagree and propose alternatives.

```text
Assessment Agent
       │
       │ ₹80,000
       ▼
Fraud Agent
       │
       │ questions evidence
       ▼
Evidence Agent
       │
       │ provides additional evidence
       ▼
Coordinator
       │
       ▼
Final decision
```

---

## Phase 6 — Autonomous Recovery

Instead of a fixed pipeline:

```text
A → B → C → D
```

allow the system to dynamically recover:

```text
A
↓
B
↓
B fails
↓
Discover alternative agent
↓
C
↓
Verify
↓
Continue
```

This would move DIPLOMAT toward a true **Agentic Web infrastructure layer**.

---

# 🎯 Hackathon Vision

The current project establishes the foundation:

> **Trusted handoffs between insurance AI components.**

The long-term vision is:

```text
                 DIPLOMAT
        TRUST LAYER FOR AGENTS
                    │
       ┌────────────┼────────────┐
       ▼            ▼            ▼
     MOTOR        HEALTH         LIFE
     AGENTS       AGENTS        AGENTS
       │            │            │
       └────────────┼────────────┘
                    │
             AGENT REGISTRY
                    │
             TRUST / REPUTATION
                    │
             MESSAGE PROTOCOL
                    │
             EVIDENCE + MEMORY
                    │
             VERIFICATION LAYER
                    │
             HUMAN OVERSIGHT
```

The goal is not simply to create **more AI agents**.

The goal is to make autonomous agents **trustworthy enough to cooperate on high-stakes financial workflows**.

---

# 🏆 The Core Idea

> ### **"Don't just make agents autonomous. Make their handoffs trustworthy."**

DIPLOMAT provides a mechanism for ensuring that information moving between AI components is:

```text
Complete
   +
Correct
   +
Consistent
   +
Evidence-backed
   +
Policy-compliant
   +
Financially valid
```

before it is allowed to influence a downstream insurance decision.

---

# 📜 Status

**Current status:** Hackathon prototype

**Primary domain:** Insurance claims

**Current focus:** Health-claim-style document extraction, policy rules, adjudication and financial verification

**Target tracks:**

* Track 02 — Agentic Web, Swarms & Harnesses
* Track 03 — Old World, New Money

---

# 🔗 Repository

[GitHub Repository](https://github.com/KEERTHIVASAN-SKV/DIPLOMAT)

---

## ⚖️ Disclaimer

DIPLOMAT is a research and hackathon prototype. It is not an insurance provider, claims administrator, financial advisor, medical decision system, or substitute for legally authorized insurance review. Production deployment would require appropriate security, privacy, regulatory, actuarial, legal and operational controls.
