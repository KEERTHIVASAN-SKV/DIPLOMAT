"""
DIPLOMAT CLI Runner
====================
Run all 6 demo claims and display results with rich formatting.

Usage:
    python main.py              # Run all 6 demo claims
    python main.py --claim 2   # Run specific claim (1-6)
    python main.py --list      # List all available claims
"""
import json
import sys
import glob
import argparse
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich import box
from rich.rule import Rule
from rich.columns import Columns

from orchestrator.pipeline import InsurancePipeline
from models.diplomat_models import DiplomatStatus

console = Console()
CLAIMS_DIR = Path(__file__).parent / "test_claims"


def render_diplomat_result(step: str, payload: dict, dr):
    """Callback for real-time step display."""
    if dr.status == DiplomatStatus.PASS:
        icon = "[PASS]"
        style = "green"
    elif dr.status == DiplomatStatus.HUMAN_REVIEW:
        icon = "[REVIEW]"
        style = "yellow"
    else:
        icon = "[BLOCK]"
        style = "red"

    console.print(f"  {icon} [{style}]{dr.status.value}[/{style}] — {step}")
    if dr.error_code:
        console.print(f"     └─ [bold {style}]{dr.error_code}[/bold {style}]: {dr.message}")
        if dr.details:
            for k, v in dr.details.items():
                if k != "failed_check":
                    console.print(f"        • {k}: {v}")


def run_claim(claim_file: Path, pipeline: InsurancePipeline, claim_num: int, total: int):
    with open(claim_file, encoding="utf-8") as f:
        raw_claim = json.load(f)

    claim_id = raw_claim.get("claim_id", "UNKNOWN")
    claimant = raw_claim.get("claimant_name", "Unknown")
    incident = raw_claim.get("incident_type", "")

    console.print(Rule(f"[bold white]Claim {claim_num}/{total} — {claim_id}[/bold white]"))
    console.print(f"  [cyan]Claimant:[/cyan] {claimant}   [cyan]Type:[/cyan] {incident}")
    console.print()

    result = pipeline.run(raw_claim, on_step=render_diplomat_result)

    console.print()
    if result.final_status == "APPROVED":
        payout = result.final_output.get("payable_amount", 0) if result.final_output else 0
        console.print(Panel(
            f"[bold green][PASS] APPROVED[/bold green]\n\nPayable Amount: [bold]₹{payout:,.2f}[/bold]",
            border_style="green"
        ))
    elif result.final_status == "HUMAN_REVIEW":
        console.print(Panel(
            f"[bold yellow][REVIEW] HUMAN REVIEW REQUIRED[/bold yellow]\n\n"
            f"Reason: {result.error.message if result.error else 'N/A'}\n"
            f"Blocked At: {result.blocked_at or 'Post-validation'}",
            border_style="yellow"
        ))
    else:
        err = result.error
        console.print(Panel(
            f"[bold red][BLOCK] BLOCKED — {err.error_code if err else 'UNKNOWN'}[/bold red]\n\n"
            f"{err.message if err else ''}\n"
            f"At: {result.blocked_at}",
            border_style="red"
        ))

    return result


def print_summary(results: list):
    console.print()
    console.print(Rule("[bold white]DIPLOMAT SUMMARY[/bold white]"))

    table = Table(box=box.ROUNDED, show_header=True, header_style="bold white")
    table.add_column("Claim", style="cyan", width=12)
    table.add_column("Claimant", width=18)
    table.add_column("Status", width=14)
    table.add_column("Blocked At / Payout", width=40)

    approved = blocked = review = 0

    for claim_file, result in results:
        with open(claim_file, encoding="utf-8") as f:
            raw = json.load(f)
        claimant = raw.get("claimant_name", "?")

        if result.final_status == "APPROVED":
            approved += 1
            payout = result.final_output.get("payable_amount", 0) if result.final_output else 0
            status_str = "[green][PASS] APPROVED[/green]"
            detail = f"₹{payout:,.2f}"
        elif result.final_status == "HUMAN_REVIEW":
            review += 1
            status_str = "[yellow][REVIEW] HUMAN REVIEW[/yellow]"
            detail = result.blocked_at or "escalated"
        else:
            blocked += 1
            status_str = "[red][BLOCK] BLOCKED[/red]"
            err = result.error
            detail = f"{err.error_code if err else '?'} @ {result.blocked_at or '?'}"

        table.add_row(result.claim_id, claimant, status_str, detail)

    console.print(table)
    console.print()
    console.print(f"  [green][PASS] {approved} Approved[/green]   "
                  f"[red][BLOCK] {blocked} Blocked[/red]   "
                  f"[yellow][REVIEW] {review} Human Review[/yellow]   "
                  f"[dim]0 unsafe handoffs allowed through[/dim]")
    console.print()


def main():
    parser = argparse.ArgumentParser(description="DIPLOMAT Insurance Pipeline")
    parser.add_argument("--claim", type=int, help="Run a specific claim (1-6)", default=None)
    parser.add_argument("--list", action="store_true", help="List available claims")
    args = parser.parse_args()

    claim_files = sorted(CLAIMS_DIR.glob("claim_0*.json"))

    if args.list:
        for i, f in enumerate(claim_files, 1):
            with open(f, encoding="utf-8") as fp:
                data = json.load(fp)
            console.print(f"  {i}. {f.name} — {data.get('claim_id')} — {data.get('claimant_name')}")
        return

    console.print(Panel.fit(
        "[bold cyan]DIPLOMAT[/bold cyan]\n[dim]Fail-Closed Trust Layer for Insurance AI Agents[/dim]",
        border_style="cyan"
    ))
    console.print()

    pipeline = InsurancePipeline()
    all_results = []

    if args.claim:
        idx = args.claim - 1
        if 0 <= idx < len(claim_files):
            r = run_claim(claim_files[idx], pipeline, args.claim, len(claim_files))
            all_results.append((claim_files[idx], r))
        else:
            console.print(f"[red]Claim {args.claim} not found.[/red]")
            sys.exit(1)
    else:
        for i, cf in enumerate(claim_files, 1):
            r = run_claim(cf, pipeline, i, len(claim_files))
            all_results.append((cf, r))
            console.print()

    print_summary(all_results)


if __name__ == "__main__":
    main()

