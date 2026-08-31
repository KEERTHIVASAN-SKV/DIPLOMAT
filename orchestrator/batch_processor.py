"""
Batch Processing Engine for DIPLOMAT
Process multiple claims with advanced filtering and reporting
"""
from typing import List, Dict, Callable, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
import time
from datetime import datetime


class BatchProcessor:
    """Process multiple claims with parallelization and monitoring"""
    
    def __init__(self, max_workers: int = 4):
        self.max_workers = max_workers
        self.batch_results = []
        self.start_time = None
        self.end_time = None
    
    def process_batch(
        self,
        claims: List[Dict],
        process_fn: Callable,
        progress_callback: Optional[Callable] = None,
        parallel: bool = False
    ) -> Dict:
        """
        Process a batch of claims
        
        Args:
            claims: List of claim dictionaries
            process_fn: Function that takes a claim and returns result
            progress_callback: Optional callback for progress updates
            parallel: Use parallel processing if True
        
        Returns:
            {
                "total": count,
                "successful": count,
                "failed": count,
                "results": [...],
                "statistics": {...}
            }
        """
        self.start_time = time.time()
        self.batch_results = []
        
        if parallel and len(claims) > 1:
            results = self._process_parallel(claims, process_fn, progress_callback)
        else:
            results = self._process_sequential(claims, process_fn, progress_callback)
        
        self.end_time = time.time()
        
        return self._compile_results(results)
    
    def _process_sequential(
        self,
        claims: List[Dict],
        process_fn: Callable,
        progress_callback: Optional[Callable]
    ) -> List[Dict]:
        """Process claims sequentially"""
        results = []
        
        for idx, claim in enumerate(claims):
            try:
                start = time.time()
                result = process_fn(claim)
                processing_time = time.time() - start
                
                results.append({
                    "claim_index": idx,
                    "status": "SUCCESS",
                    "result": result,
                    "processing_time": processing_time,
                    "error": None
                })
            except Exception as e:
                results.append({
                    "claim_index": idx,
                    "status": "FAILED",
                    "result": None,
                    "error": str(e),
                    "processing_time": 0
                })
            
            if progress_callback:
                progress_callback(idx + 1, len(claims))
        
        return results
    
    def _process_parallel(
        self,
        claims: List[Dict],
        process_fn: Callable,
        progress_callback: Optional[Callable]
    ) -> List[Dict]:
        """Process claims in parallel"""
        results = [None] * len(claims)
        completed = 0
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = {
                executor.submit(self._safe_process, claim, idx, process_fn): idx
                for idx, claim in enumerate(claims)
            }
            
            for future in as_completed(futures):
                idx = futures[future]
                try:
                    results[idx] = future.result()
                    completed += 1
                    if progress_callback:
                        progress_callback(completed, len(claims))
                except Exception as e:
                    results[idx] = {
                        "claim_index": idx,
                        "status": "FAILED",
                        "result": None,
                        "error": str(e),
                        "processing_time": 0
                    }
        
        return results
    
    def _safe_process(self, claim: Dict, idx: int, process_fn: Callable) -> Dict:
        """Safely process a single claim"""
        try:
            start = time.time()
            result = process_fn(claim)
            processing_time = time.time() - start
            
            return {
                "claim_index": idx,
                "status": "SUCCESS",
                "result": result,
                "processing_time": processing_time,
                "error": None
            }
        except Exception as e:
            return {
                "claim_index": idx,
                "status": "FAILED",
                "result": None,
                "processing_time": 0,
                "error": str(e)
            }
    
    def _compile_results(self, results: List[Dict]) -> Dict:
        """Compile and analyze batch results"""
        successful = [r for r in results if r["status"] == "SUCCESS"]
        failed = [r for r in results if r["status"] == "FAILED"]
        
        processing_times = [r["processing_time"] for r in successful if r["processing_time"] > 0]
        
        # Analyze claim outcomes
        approved = len([r for r in successful if r["result"].get("status") == "APPROVED"])
        escalated = len([r for r in successful if r["result"].get("status") == "ESCALATED_TO_HUMAN"])
        rejected = len([r for r in successful if r["result"].get("status") == "REJECTED"])
        
        # Financial analysis
        total_bills = sum(r["result"].get("settlement", {}).get("bill_total", 0) for r in successful)
        total_payouts = sum(r["result"].get("settlement", {}).get("payable", 0) for r in successful)
        total_deductions = sum(r["result"].get("settlement", {}).get("total_deductions", 0) for r in successful)
        
        return {
            "batch_summary": {
                "total_claims": len(results),
                "successful": len(successful),
                "failed": len(failed),
                "success_rate_percent": round((len(successful) / len(results) * 100) if results else 0, 2)
            },
            "outcomes": {
                "approved": approved,
                "escalated_to_human": escalated,
                "rejected": rejected
            },
            "performance": {
                "total_time_seconds": round(self.end_time - self.start_time, 2) if self.end_time else 0,
                "avg_claim_time_ms": round((sum(processing_times) / len(processing_times) * 1000) if processing_times else 0, 2),
                "min_time_ms": round(min(processing_times) * 1000, 2) if processing_times else 0,
                "max_time_ms": round(max(processing_times) * 1000, 2) if processing_times else 0,
                "throughput_per_minute": round((len(successful) / ((self.end_time - self.start_time) / 60)) if self.end_time - self.start_time > 0 else 0, 2)
            },
            "financials": {
                "total_bill_amount": round(total_bills, 2),
                "total_approved_payout": round(total_payouts, 2),
                "total_deductions": round(total_deductions, 2),
                "deduction_rate_percent": round((total_deductions / total_bills * 100) if total_bills > 0 else 0, 2),
                "average_claim_value": round(total_bills / len(successful), 2) if successful else 0,
                "average_deduction_per_claim": round(total_deductions / len(successful), 2) if successful else 0
            },
            "errors": {
                "failed_claims": [
                    {"index": r["claim_index"], "error": r["error"]} for r in failed
                ] if failed else []
            },
            "detailed_results": results
        }


class ClaimFilter:
    """Advanced filtering for claim batches"""
    
    @staticmethod
    def filter_by_bill_amount(claims: List[Dict], min_amount: float = 0, max_amount: float = float('inf')) -> List[Dict]:
        """Filter claims by bill amount range"""
        return [c for c in claims if min_amount <= c.get("bill_total", 0) <= max_amount]
    
    @staticmethod
    def filter_by_diagnosis(claims: List[Dict], diagnosis_keywords: List[str]) -> List[Dict]:
        """Filter claims by diagnosis keywords"""
        result = []
        for claim in claims:
            diagnosis = claim.get("diagnosis", "").lower()
            if any(kw.lower() in diagnosis for kw in diagnosis_keywords):
                result.append(claim)
        return result
    
    @staticmethod
    def filter_by_length_of_stay(claims: List[Dict], min_days: int = 0, max_days: int = 999) -> List[Dict]:
        """Filter claims by length of stay"""
        result = []
        for claim in claims:
            los = claim.get("length_of_stay", {}).get("value", 0)
            if min_days <= los <= max_days:
                result.append(claim)
        return result
    
    @staticmethod
    def filter_by_risk_level(results: List[Dict], risk_levels: List[str]) -> List[Dict]:
        """Filter processed results by fraud risk level"""
        return [r for r in results if r.get("fraud_analysis", {}).get("risk_level") in risk_levels]
    
    @staticmethod
    def filter_high_value_claims(claims: List[Dict], percentile: float = 90) -> List[Dict]:
        """Filter claims above a certain percentile by bill amount"""
        if not claims:
            return []
        
        bills = [c.get("bill_total", 0) for c in claims]
        threshold = sorted(bills)[int(len(bills) * percentile / 100)]
        
        return [c for c in claims if c.get("bill_total", 0) >= threshold]


class ReportGenerator:
    """Generate comprehensive reports from batch processing results"""
    
    @staticmethod
    def generate_executive_summary(batch_result: Dict) -> Dict:
        """Generate executive summary report"""
        return {
            "report_type": "Executive Summary",
            "generated_at": datetime.now().isoformat(),
            "total_claims_processed": batch_result["batch_summary"]["total_claims"],
            "success_rate": batch_result["batch_summary"]["success_rate_percent"],
            "approval_rate": (batch_result["outcomes"]["approved"] / batch_result["batch_summary"]["successful"] * 100) if batch_result["batch_summary"]["successful"] > 0 else 0,
            "total_payout": batch_result["financials"]["total_approved_payout"],
            "total_deductions": batch_result["financials"]["total_deductions"],
            "average_processing_time_ms": batch_result["performance"]["avg_claim_time_ms"],
            "throughput_per_minute": batch_result["performance"]["throughput_per_minute"],
            "failed_claims": batch_result["batch_summary"]["failed"]
        }
    
    @staticmethod
    def generate_detailed_report(batch_result: Dict) -> str:
        """Generate detailed text report"""
        lines = []
        lines.append("=" * 80)
        lines.append("DIPLOMAT BATCH PROCESSING REPORT")
        lines.append("=" * 80)
        lines.append(f"Generated: {datetime.now().isoformat()}")
        lines.append("")
        
        summary = batch_result["batch_summary"]
        lines.append(f"BATCH SUMMARY")
        lines.append("-" * 40)
        lines.append(f"Total Claims Processed:  {summary['total_claims']}")
        lines.append(f"Successful:              {summary['successful']}")
        lines.append(f"Failed:                  {summary['failed']}")
        lines.append(f"Success Rate:            {summary['success_rate_percent']}%")
        lines.append("")
        
        outcomes = batch_result["outcomes"]
        lines.append(f"CLAIM OUTCOMES")
        lines.append("-" * 40)
        lines.append(f"Approved:                {outcomes['approved']}")
        lines.append(f"Escalated to Human:      {outcomes['escalated_to_human']}")
        lines.append(f"Rejected:                {outcomes['rejected']}")
        lines.append("")
        
        financials = batch_result["financials"]
        lines.append(f"FINANCIAL SUMMARY")
        lines.append("-" * 40)
        lines.append(f"Total Bill Amount:       ₹{financials['total_bill_amount']:,.2f}")
        lines.append(f"Total Approved Payout:   ₹{financials['total_approved_payout']:,.2f}")
        lines.append(f"Total Deductions:        ₹{financials['total_deductions']:,.2f}")
        lines.append(f"Deduction Rate:          {financials['deduction_rate_percent']:.2f}%")
        lines.append(f"Average Claim Value:     ₹{financials['average_claim_value']:,.2f}")
        lines.append("")
        
        perf = batch_result["performance"]
        lines.append(f"PERFORMANCE METRICS")
        lines.append("-" * 40)
        lines.append(f"Total Processing Time:   {perf['total_time_seconds']:.2f}s")
        lines.append(f"Avg Time per Claim:      {perf['avg_claim_time_ms']:.2f}ms")
        lines.append(f"Throughput:              {perf['throughput_per_minute']:.2f} claims/min")
        lines.append("")
        lines.append("=" * 80)
        
        return "\n".join(lines)
