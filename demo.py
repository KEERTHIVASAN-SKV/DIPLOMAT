import json
import sys
import os

sys.stdout.reconfigure(encoding='utf-8')

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from orchestrator.pipeline import InsurancePipeline


def load_json(path):
    with open(path, encoding='utf-8') as f:
        return json.load(f)


def print_bounces(bounces):
    for bounce in bounces:
        check_name = bounce.get('check', bounce.get('validator', 'UNKNOWN'))
        severity = bounce.get('severity', 'ERROR')
        message = bounce.get('message', 'No message')
        print(f"  🔴 [{severity}] {check_name}: {message}")
        if 'expected' in bounce and 'got' in bounce:
            print(f"     Expected: {bounce['expected']}")
            print(f"     Got:      {bounce['got']}")
        if 'hint' in bounce:
            print(f"     💡 {bounce['hint']}")
        print()


def print_settlement(settlement):
    if not settlement:
        print("  (No settlement generated)")
        return
    print(f"  Bill Total:     ₹{settlement['bill_total']:,.2f}")
    print(f"  Deductions:")
    for d in settlement['deductions']:
        clause = d.get('clause_id', 'MISSING')
        print(f"    • {d['description']:<45} ₹{d['amount']:>10,.2f}  (Clause: {clause})")
    print(f"  Total Deducted: ₹{settlement['total_deductions']:,.2f}")
    print(f"  Payable:        ₹{settlement['payable']:,.2f}")


def _method_tag(payload):
    if not isinstance(payload, dict):
        return None
    em = payload.get("_extraction_method")
    am = payload.get("_adjudication_method")
    parts = []
    if em:
        parts.append(f"extraction={em}")
    if am:
        parts.append(f"adjudication={am}")
    return f"  [{' | '.join(parts)}]" if parts else None


def print_trace_step(step):
    step_name = step.get("step", "UNKNOWN")
    status = step.get("status", "UNKNOWN")

    if step_name == "PIPELINE" and status == "FEEDBACK_LOOP":
        detail = step.get("detail", "")
        print(f"  🔄 {detail}")
    elif "BOUNCED" in status:
        print(f"  🚫 {step_name}: {status}")
        if "bounces" in step:
            print_bounces(step["bounces"])
    elif status == "PASSED":
        attempt = step.get("attempt", "?")
        print(f"  ✅ {step_name} PASSED (attempt {attempt})")
    elif "ATTEMPT" in status:
        tag = _method_tag(step.get("output")) or _method_tag(step.get("settlement")) or ""
        print(f"  🔄 {step_name} — {status}{tag}")
    else:
        print(f"  ▶️  {step_name}: {status}")


def run_scenario(name, inject_fault):
    policy = load_json("demo_data/policy.json")
    bill = load_json("demo_data/bill.json")
    discharge = load_json("demo_data/discharge_summary.json")
    
    print(f"\n{'='*70}")
    print(f"  {name}")
    print(f"{'='*70}")
    
    pipeline = InsurancePipeline(policy, use_gates=True, max_retries=2)
    result = pipeline.process(bill, discharge, inject_fault=inject_fault)
    
    print(f"\nFinal Status: {result['status']}")
    
    if result.get("trace"):
        print("\nPipeline Trace:")
        for step in result["trace"]:
            print_trace_step(step)
    
    if result.get("settlement"):
        print("\nSettlement:")
        print_settlement(result["settlement"])
    
    if result.get("bounces"):
        print("\nFinal Bounces (escalated):")
        print_bounces(result["bounces"])


def main():
    print("=" * 70)
    print("DIPLOMAT DEMO: Self-Correcting Pipeline with Feedback Loops")
    print("=" * 70)

    run_scenario("SCENARIO 1: Gate 1 — Intake misreads room rent (room_rent_misread)", "room_rent_misread")
    run_scenario("SCENARIO 2: Gate 2 — Adjudicator missing citation (missing_citation)", "missing_citation")
    run_scenario("SCENARIO 3: Clean claim — no fault injection", None)

    print("\n" + "=" * 70)
    print("Demo Complete")
    print("=" * 70)


if __name__ == "__main__":
    main()
