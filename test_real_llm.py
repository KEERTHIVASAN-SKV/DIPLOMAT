"""
Test Script: Verify Real LLM Calls vs Mock Fallback
====================================================
Tests the medical claims pipeline (IntakeAgent + AdjudicatorAgent)
with MOCK_MODE=false to verify real Gemini API calls.
"""
import json
import sys
from pathlib import Path

# Configuration check
import config
print("="*80)
print(" LLM VERIFICATION TEST")
print("="*80)
print(f"\nMOCK_MODE: {config.MOCK_MODE}")
print(f"API KEY: {'SET (' + config.GOOGLE_API_KEY[:15] + '...)' if config.GOOGLE_API_KEY else 'NOT SET'}")
print(f"MODEL: {config.GEMINI_MODEL}\n")

if config.MOCK_MODE:
    print("❌ ERROR: MOCK_MODE is TRUE - real LLM calls will NOT be made!")
    print("Set MOCK_MODE=false in .env file")
    sys.exit(1)

if not config.GOOGLE_API_KEY:
    print("❌ ERROR: GOOGLE_API_KEY is not set!")
    print("Set GOOGLE_API_KEY in .env file")
    sys.exit(1)

print("✓ Configuration looks good. Running tests...")
print("="*80)
print()

from orchestrator.pipeline import InsurancePipeline


def load_json(path):
    with open(path, encoding='utf-8') as f:
        return json.load(f)


def test_scenario(name, inject_fault=None, expected_outcome=None):
    """Test a scenario and verify LLM usage."""
    print(f"\n{'='*80}")
    print(f" SCENARIO: {name}")
    print(f"{'='*80}\n")
    
    # Load documents
    policy = load_json("demo_data/policy.json")
    bill = load_json("demo_data/bill.json")
    discharge = load_json("demo_data/discharge_summary.json")
    
    # Run pipeline
    pipeline = InsurancePipeline(policy, use_gates=True, max_retries=2)
    result = pipeline.process(bill, discharge, inject_fault=inject_fault)
    
    # Analyze trace for LLM usage
    intake_attempts = []
    adjudicator_attempts = []
    intake_method = "unknown"
    adjudicator_method = "unknown"
    bounces_detected = []
    
    for step in result.get("trace", []):
        step_name = step.get("step", "")
        status = step.get("status", "")
        
        # Track intake agent attempts
        if step_name == "A1_INTAKE" and "ATTEMPT" in status:
            output = step.get("output", {})
            method = output.get("_extraction_method", "unknown")
            intake_attempts.append({
                "attempt": status,
                "method": method
            })
            intake_method = method
        
        # Track adjudicator attempts
        if step_name == "A3_ADJUDICATOR" and "ATTEMPT" in status:
            settlement = step.get("settlement", {})
            method = settlement.get("_adjudication_method", "unknown")
            adjudicator_attempts.append({
                "attempt": status,
                "method": method
            })
            adjudicator_method = method
        
        # Track bounces
        if "BOUNCED" in status:
            bounces_detected.append({
                "gate": step_name,
                "attempt": status,
                "bounces": step.get("bounces", [])
            })
        
        # Track feedback loops
        if step_name == "PIPELINE" and status == "FEEDBACK_LOOP":
            print(f"  🔄 FEEDBACK LOOP: {step.get('detail', '')}")
            feedback = step.get('feedback', [])
            for fb in feedback:
                check = fb.get('check', 'UNKNOWN')
                msg = fb.get('message', '')
                print(f"     └─ {check}: {msg}")
    
    # Display results
    print(f"\n📊 RESULT SUMMARY:")
    print(f"  Final Status: {result['status']}")
    print(f"  Intake Agent: {intake_method.upper()} ({len(intake_attempts)} attempts)")
    print(f"  Adjudicator: {adjudicator_method.upper()} ({len(adjudicator_attempts)} attempts)")
    print(f"  Bounces Detected: {len(bounces_detected)}")
    
    # Verify LLM usage
    print(f"\n🔍 LLM USAGE VERIFICATION:")
    if intake_method == "llm":
        print(f"  ✅ IntakeAgent used REAL LLM (Gemini)")
    elif intake_method == "mock":
        print(f"  ❌ IntakeAgent fell back to MOCK mode")
    else:
        print(f"  ⚠️  IntakeAgent method: {intake_method}")
    
    if adjudicator_method == "llm":
        print(f"  ✅ AdjudicatorAgent used REAL LLM (Gemini)")
    elif adjudicator_method == "mock":
        print(f"  ❌ AdjudicatorAgent fell back to MOCK mode")
    else:
        print(f"  ⚠️  AdjudicatorAgent method: {adjudicator_method}")
    
    # Show bounces if any
    if bounces_detected:
        print(f"\n🚫 BOUNCES:")
        for bounce_event in bounces_detected:
            print(f"  {bounce_event['gate']} — {bounce_event['attempt']}:")
            for b in bounce_event['bounces']:
                check = b.get('check', 'UNKNOWN')
                msg = b.get('message', '')
                print(f"    • {check}: {msg}")
    
    # Show settlement if approved
    if result['status'] == "APPROVED" and result.get('settlement'):
        settlement = result['settlement']
        print(f"\n💰 SETTLEMENT:")
        print(f"  Bill Total: ₹{settlement['bill_total']:,.2f}")
        print(f"  Deductions: ₹{settlement['total_deductions']:,.2f}")
        print(f"  Payable: ₹{settlement['payable']:,.2f}")
    
    # Flag issues
    issues = []
    if intake_method == "mock":
        issues.append("⚠️  IntakeAgent fell back to MOCK")
    if adjudicator_method == "mock":
        issues.append("⚠️  AdjudicatorAgent fell back to MOCK")
    
    if issues:
        print(f"\n⚠️  ISSUES DETECTED:")
        for issue in issues:
            print(f"  {issue}")
        print(f"\nCheck console output above for error messages from agents.")
    
    print()
    
    return {
        "name": name,
        "status": result['status'],
        "intake_method": intake_method,
        "adjudicator_method": adjudicator_method,
        "intake_attempts": len(intake_attempts),
        "adjudicator_attempts": len(adjudicator_attempts),
        "bounces": len(bounces_detected),
        "has_issues": len(issues) > 0
    }


# Run test scenarios
print("\nRunning test scenarios with MOCK_MODE=false...")
print("This will make REAL API calls to Gemini.")
print()

results = []

# Test 1: Clean run (no fault injection)
results.append(test_scenario(
    "Clean Extraction (No Faults)",
    inject_fault=None
))

# Test 2: Room rent misread (should trigger Gate 1 bounce + retry)
results.append(test_scenario(
    "Room Rent Misread (Gate 1 Bounce)",
    inject_fault="room_rent_misread"
))

# Test 3: Missing citation (should trigger Gate 2 bounce + retry)
results.append(test_scenario(
    "Missing Citation (Gate 2 Bounce)",
    inject_fault="missing_citation"
))

# Final summary
print("\n" + "="*80)
print(" FINAL SUMMARY")
print("="*80 + "\n")

print(f"{'Scenario':<40} {'Status':<15} {'Intake':<10} {'Adjudicator':<12} {'Attempts':<10} {'Bounces'}")
print("-"*100)

for r in results:
    intake_icon = "✅" if r['intake_method'] == "llm" else "❌"
    adj_icon = "✅" if r['adjudicator_method'] == "llm" else "❌"
    attempts_str = f"{r['intake_attempts']}/{r['adjudicator_attempts']}"
    
    print(f"{r['name']:<40} {r['status']:<15} {intake_icon} {r['intake_method']:<8} {adj_icon} {r['adjudicator_method']:<10} {attempts_str:<10} {r['bounces']}")

print()

# Final verdict
all_llm = all(r['intake_method'] == 'llm' and r['adjudicator_method'] == 'llm' for r in results)
any_issues = any(r['has_issues'] for r in results)

if all_llm and not any_issues:
    print("✅ VERIFICATION PASSED")
    print("   All agents successfully used REAL LLM calls")
    print("   No silent fallbacks to mock mode detected")
else:
    print("❌ VERIFICATION FAILED")
    if not all_llm:
        print("   Some agents fell back to MOCK mode")
    if any_issues:
        print("   Issues detected - check output above")
    print("\n   Possible reasons:")
    print("   • API key invalid or quota exceeded")
    print("   • Network connectivity issues")
    print("   • LLM returned invalid JSON (check warnings above)")

print()
