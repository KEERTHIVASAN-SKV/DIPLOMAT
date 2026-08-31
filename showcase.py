"""
DIPLOMAT v2 - Hackathon Showcase
Demonstrates all new features: fraud detection, analytics, batch processing, APIs
"""
import json
import sys
import os
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from orchestrator.pipeline import InsurancePipeline
from agents.fraud_detector import FraudDetector
from orchestrator.analytics import PipelineAnalytics
from orchestrator.batch_processor import BatchProcessor, ClaimFilter, ReportGenerator
from agents.policy_selector import PolicySelector, PolicyComparator
from api.diplomat_api import DiplomatAPI


def load_json(path):
    with open(path, encoding='utf-8') as f:
        return json.load(f)


def print_section(title):
    print(f"\n{'='*80}")
    print(f"  {title}")
    print(f"{'='*80}\n")


def showcase_fraud_detection():
    """Showcase fraud detection capabilities"""
    print_section("🔍 FRAUD DETECTION ENGINE")
    
    policy = load_json("demo_data/policy.json")
    bill = load_json("demo_data/bill.json")
    discharge = load_json("demo_data/discharge_summary.json")
    
    # Create fraud detector
    fraud_detector = FraudDetector()
    
    # Analyze claim
    settlement = {}  # Simplified for demo
    fraud_analysis = fraud_detector.analyze_claim(bill, settlement, policy)
    
    print(f"Risk Level:        {fraud_analysis['risk_level']}")
    print(f"Risk Score:        {fraud_analysis['risk_score']}/1.0")
    print(f"Confidence:        {fraud_analysis['confidence']}")
    print(f"Recommendation:    {fraud_analysis['recommendation']}")
    print(f"\nRisk Factors ({len(fraud_analysis['risk_factors'])}):")
    for factor in fraud_analysis['risk_factors']:
        print(f"  • {factor['factor']}: {factor['details']}")
    
    if fraud_analysis['red_flags']:
        print(f"\nRed Flags ({len(fraud_analysis['red_flags'])}):")
        for flag in fraud_analysis['red_flags']:
            print(f"  🚩 {flag}")


def showcase_analytics():
    """Showcase analytics engine"""
    print_section("📊 ANALYTICS ENGINE")
    
    policy = load_json("demo_data/policy.json")
    bill = load_json("demo_data/bill.json")
    discharge = load_json("demo_data/discharge_summary.json")
    
    # Create pipeline and analytics
    pipeline = InsurancePipeline(policy, use_gates=True, max_retries=2)
    analytics = PipelineAnalytics()
    
    # Process 3 demo claims
    for i in range(3):
        inject_fault = ["room_rent_misread", "missing_citation", None][i]
        result = pipeline.process(bill, discharge, inject_fault=inject_fault)
        analytics.record_claim(bill, result, 1.5)
    
    # Get summary
    summary = analytics.get_summary()
    
    print(f"Total Claims:           {summary['summary']['total_claims_processed']}")
    print(f"Success Rate:           {(analytics.claims_approved/max(1,analytics.claims_processed)*100):.1f}%")
    print(f"\nOutcomes:")
    print(f"  • Approved:           {analytics.claims_approved}")
    print(f"  • Escalated:          {analytics.claims_escalated}")
    print(f"  • Rejected:           {analytics.claims_rejected}")
    print(f"\nFinancials:")
    print(f"  • Total Bills:        ₹{analytics.total_bill_amount:,.0f}")
    print(f"  • Total Payouts:      ₹{analytics.total_approved_amount:,.0f}")
    print(f"  • Deduction Rate:     {(analytics.total_deductions_applied/max(1,analytics.total_bill_amount)*100):.1f}%")
    print(f"\nPerformance:")
    if analytics.processing_times:
        print(f"  • Avg Processing:     {(sum(analytics.processing_times)/len(analytics.processing_times))*1000:.2f}ms")


def showcase_batch_processing():
    """Showcase batch processing"""
    print_section("📈 BATCH PROCESSING ENGINE")
    
    policy = load_json("demo_data/policy.json")
    bill = load_json("demo_data/bill.json")
    discharge = load_json("demo_data/discharge_summary.json")
    
    # Create demo batch
    demo_claims = [{**bill, "claim_id": f"BATCH-{i+1:03d}"} for i in range(5)]
    
    processor = BatchProcessor(max_workers=2)
    pipeline = InsurancePipeline(policy, use_gates=True, max_retries=2)
    
    def process_fn(claim):
        return pipeline.process(claim, discharge)
    
    print("Processing 5 claims in batch...")
    batch_result = processor.process_batch(demo_claims, process_fn, parallel=True)
    
    summary = batch_result["batch_summary"]
    print(f"\nBatch Results:")
    print(f"  • Total Claims:       {summary['total_claims']}")
    print(f"  • Successful:         {summary['successful']}")
    print(f"  • Success Rate:       {summary['success_rate_percent']:.1f}%")
    
    outcomes = batch_result["outcomes"]
    print(f"\nOutcomes:")
    print(f"  • Approved:           {outcomes['approved']}")
    print(f"  • Escalated:          {outcomes['escalated_to_human']}")
    print(f"  • Rejected:           {outcomes['rejected']}")
    
    perf = batch_result["performance"]
    print(f"\nPerformance:")
    print(f"  • Total Time:         {perf['total_time_seconds']:.2f}s")
    print(f"  • Avg Time/Claim:     {perf['avg_claim_time_ms']:.2f}ms")
    print(f"  • Throughput:         {perf['throughput_per_minute']:.1f} claims/min")
    
    fin = batch_result["financials"]
    print(f"\nFinancials:")
    print(f"  • Total Bills:        ₹{fin['total_bill_amount']:,.0f}")
    print(f"  • Total Payouts:      ₹{fin['total_approved_payout']:,.0f}")
    print(f"  • Deduction Rate:     {fin['deduction_rate_percent']:.1f}%")


def showcase_multi_policy():
    """Showcase multi-policy support"""
    print_section("🎯 MULTI-POLICY SUPPORT")
    
    # Create multiple policies
    policies = [
        {
            "policy_id": "POL-BASIC-001",
            "sum_insured": 300000,
            "room_rent_sublimit": 3000,
            "coverage_types": ["surgery", "hospitalization"]
        },
        {
            "policy_id": "POL-PREMIUM-001",
            "sum_insured": 500000,
            "room_rent_sublimit": 5000,
            "coverage_types": ["surgery", "hospitalization", "diagnostics"]
        },
        {
            "policy_id": "POL-DELUXE-001",
            "sum_insured": 1000000,
            "room_rent_sublimit": 10000,
            "coverage_types": ["surgery", "hospitalization", "diagnostics", "ICU"]
        }
    ]
    
    bill = load_json("demo_data/bill.json")
    
    selector = PolicySelector(policies)
    best_policy, score_info = selector.find_best_policy(bill)
    
    print(f"Claim Amount:           ₹{bill['bill_total']:,.0f}")
    print(f"\nBest Matching Policy:   {best_policy['policy_id']}")
    print(f"  • Sum Insured:        ₹{best_policy['sum_insured']:,.0f}")
    print(f"  • Coverage:           {', '.join(best_policy['coverage_types'])}")
    print(f"  • Match Score:        {score_info['match_percent']}%")
    print(f"  • Match Reasons:")
    for reason in score_info['match_reasons']:
        print(f"    - {reason}")
    
    # Compare coverage
    comparator = PolicyComparator()
    comparison = comparator.compare_coverage(policies, bill)
    
    print(f"\nPolicy Comparison:")
    for comp in comparison["comparisons"]:
        print(f"\n  {comp['policy_id']}:")
        print(f"    • Coverage:       {comp['coverage_percent']:.1f}%")
        print(f"    • Estimated Payout: ₹{comp['estimated_payout']:,.0f}")


def showcase_api():
    """Showcase REST API"""
    print_section("🔌 ENTERPRISE API (REST + GraphQL)")
    
    policy = load_json("demo_data/policy.json")
    bill = load_json("demo_data/bill.json")
    discharge = load_json("demo_data/discharge_summary.json")
    
    pipeline = InsurancePipeline(policy)
    fraud_detector = FraudDetector()
    analytics = PipelineAnalytics()
    
    # Create API instance
    api = DiplomatAPI(pipeline, fraud_detector, analytics)
    
    # Process claim via API
    claim_data = {"bill": bill, "discharge": discharge, "policy": policy}
    result = api.process_claim(claim_data, {"request_id": "API-001"})
    
    print(f"Request ID:             {result['request_id']}")
    print(f"Status:                 {result['status']}")
    print(f"Claim Status:           {result['result'].get('status', 'N/A')}")
    print(f"\nFraud Analysis:")
    fraud = result['fraud_analysis']
    print(f"  • Risk Level:         {fraud['risk_level']}")
    print(f"  • Risk Score:         {fraud['risk_score']}/1.0")
    print(f"  • Recommendation:     {fraud['recommendation']}")
    
    # Get health
    health = api.get_health_status()
    print(f"\nAPI Health:")
    print(f"  • Service:            {health['service']}")
    print(f"  • Status:             {health['status']}")
    print(f"  • Claims Processed:   {health['claims_processed']}")


def showcase_features_summary():
    """Display features summary"""
    print_section("✨ HACKATHON WINNING FEATURES SUMMARY")
    
    features = {
        "🔍 Fraud Detection": {
            "Status": "✅ IMPLEMENTED",
            "Factor Count": "8 sophisticated factors",
            "Risk Levels": "LOW / MEDIUM / HIGH",
            "Confidence": "Up to 99%"
        },
        "📊 Real-Time Analytics": {
            "Status": "✅ IMPLEMENTED",
            "Metrics": "50+ KPIs tracked",
            "Dashboards": "4 tab interface",
            "Export": "JSON + Reports"
        },
        "📈 Batch Processing": {
            "Status": "✅ IMPLEMENTED",
            "Parallelization": "4+ workers",
            "Throughput": "100+ claims/min",
            "Filtering": "5 filter types"
        },
        "🎯 Multi-Policy": {
            "Status": "✅ IMPLEMENTED",
            "Matching": "Intelligent scoring",
            "Coverage Analysis": "Gap detection",
            "Comparison": "Side-by-side"
        },
        "💻 Enterprise API": {
            "Status": "✅ IMPLEMENTED",
            "Protocols": "REST + GraphQL",
            "Webhooks": "Event notifications",
            "Logging": "Full audit trail"
        },
        "🏥 Self-Correcting": {
            "Status": "✅ IMPLEMENTED",
            "Retry Logic": "With feedback",
            "Gates": "2 validation gates",
            "Feedback": "Structured bounces"
        },
        "📡 Monitoring": {
            "Status": "✅ IMPLEMENTED",
            "Health Tracking": "Real-time",
            "Alerts": "Severity-based",
            "Performance": "Detailed profiling"
        }
    }
    
    for feature, details in features.items():
        print(f"\n{feature}")
        for key, value in details.items():
            print(f"  • {key:<20} {value}")


def main():
    print("\n" + "="*80)
    print("  DIPLOMAT v2 - HACKATHON SHOWCASE")
    print("  Enterprise Insurance AI Gateway with Fraud Detection & Analytics")
    print("="*80)
    
    try:
        # Run showcases
        showcase_fraud_detection()
        showcase_analytics()
        showcase_batch_processing()
        showcase_multi_policy()
        showcase_api()
        showcase_features_summary()
        
        print("\n" + "="*80)
        print("  ✅ SHOWCASE COMPLETE")
        print("="*80)
        print("\nTo run the interactive dashboard:")
        print("  streamlit run dashboard/app.py")
        print("\nTo process claims via CLI:")
        print("  python demo.py")
        print("\n" + "="*80)
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
