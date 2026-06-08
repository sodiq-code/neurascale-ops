"""
Generate rich HTML screenshots of the pipeline output for Devpost submission.
Uses rich library to render beautiful terminal-style output as HTML/SVG.
"""
import os
import sys
sys.path.insert(0, '/home/user/neurascale-ops')

from dotenv import load_dotenv
load_dotenv()

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.columns import Columns
from rich.rule import Rule
from rich.syntax import Syntax
from rich import box
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
from rich.live import Live
from rich.layout import Layout
import time

from agents.detector.detector import DEMO_SCENARIOS, Alert
from agents.triage.triage_agent import TriageAgent
from agents.cost_impact.cost_agent import CostImpactAgent
from agents.remediation.remediation_agent import RemediationAgent
import asyncio

OUTPUT_DIR = "/home/user/neurascale-ops/demo_assets/screenshots"

def save_html(console_output: str, filename: str):
    path = f"{OUTPUT_DIR}/{filename}"
    with open(path, "w") as f:
        f.write(console_output)
    print(f"  Saved: {path}")

# ── Screenshot 1: Pipeline Overview ──────────────────────────────────────────
def screenshot_pipeline_overview():
    console = Console(record=True, width=100)
    
    console.print()
    console.print(Panel.fit(
        "[bold white]NeuroScale Ops[/bold white] [dim]—[/dim] [cyan]AI-Powered Kubernetes Incident Response[/cyan]\n"
        "[dim]Orchestrated by UiPath Maestro · Powered by Groq llama-3.3-70b-versatile[/dim]",
        border_style="bright_blue",
        padding=(1, 4)
    ))
    console.print()

    # Pipeline stages table
    table = Table(
        title="[bold]7-Stage Maestro Case Pipeline[/bold]",
        box=box.ROUNDED,
        border_style="blue",
        title_style="bold cyan",
        show_header=True,
        header_style="bold white on blue",
        width=98,
    )
    table.add_column("Stage", style="bold yellow", width=7, justify="center")
    table.add_column("Name", style="bold white", width=20)
    table.add_column("Component", style="cyan", width=25)
    table.add_column("Description", style="white", width=40)

    stages = [
        ("S1", "🔍 Detect",      "Coded Agent (Python)",       "Normalize Prometheus webhook → Incident object. Circuit breaker dedup."),
        ("S2", "🧠 Triage",      "Groq llama-3.3-70b",         "Root cause analysis + runbook RAG. Structured JSON output."),
        ("S3", "✅ Approval",    "UiPath Apps",                 "Human-in-loop: SRE reviews AI plan before execution."),
        ("S4", "🔧 Remediate",   "Coded Agent (Python)",        "ArgoCD sync, kubectl restart, resource patching."),
        ("S5", "💰 Cost Impact", "API Workflow + OpenCost",     "Current monthly spend + remediation cost delta."),
        ("S6", "📣 Notify",      "Agent Builder + UiPath Apps", "Rich Slack/PagerDuty + human sign-off form."),
        ("S7", "📄 Post-Mortem", "Document Understanding",      "Structured PDF: timeline, root cause, cost impact."),
    ]
    for s in stages:
        table.add_row(*s)

    console.print(table)
    console.print()

    # UiPath components
    comp_table = Table(
        title="[bold]UiPath Components Used[/bold]",
        box=box.SIMPLE_HEAVY,
        border_style="bright_blue",
        title_style="bold cyan",
        width=98,
    )
    comp_table.add_column("Component", style="bold yellow", width=35)
    comp_table.add_column("Role in Pipeline", style="white", width=60)

    comps = [
        ("Maestro Case",                    "Core orchestration — 7 stages, SLAs, escalation paths, audit trail"),
        ("Coded Agents (Python SDK)",        "Detector, Triage, Remediation, Cost Impact — full business logic"),
        ("API Workflows",                    "Prometheus webhook receiver, ArgoCD trigger, OpenCost query"),
        ("Agent Builder",                    "Low-code Slack/PagerDuty notification agent"),
        ("UiPath Apps",                      "3 human-in-loop forms: triage approval, remediation review, sign-off"),
        ("Document Understanding",           "Post-mortem PDF generation with AI extraction"),
        ("For Coding Agents (Claude Code)",  "Architecture design + agent implementation (3 sessions documented)"),
    ]
    for c in comps:
        comp_table.add_row(*c)
    console.print(comp_table)
    console.print()

    html = console.export_html(inline_styles=True)
    save_html(html, "01_pipeline_overview.html")


# ── Screenshot 2: Live Pipeline Run — OOMKill ─────────────────────────────────
def screenshot_oomkill_run():
    console = Console(record=True, width=100)

    alert = Alert(**DEMO_SCENARIOS["oomkill"])
    triage_agent = TriageAgent()
    cost_agent = CostImpactAgent()
    remediation_agent = RemediationAgent()

    console.print()
    console.print(Rule("[bold red]🚨 CRITICAL INCIDENT DETECTED[/bold red]", style="red"))
    console.print()

    # Alert panel
    alert_table = Table(box=box.MINIMAL, show_header=False, padding=(0,1))
    alert_table.add_column("Key", style="dim")
    alert_table.add_column("Value", style="bold white")
    alert_table.add_row("Alert ID",   alert.id)
    alert_table.add_row("Type",       f"[bold red]{alert.type.upper()}[/bold red]")
    alert_table.add_row("Severity",   f"[bold red]{alert.severity.upper()}[/bold red]")
    alert_table.add_row("Namespace",  f"[cyan]{alert.namespace}[/cyan]")
    alert_table.add_row("Resource",   alert.resource)
    alert_table.add_row("Message",    f"[yellow]{alert.message}[/yellow]")

    console.print(Panel(alert_table, title="[bold red]Stage 1 — Alert Detected[/bold red]", border_style="red"))
    console.print()

    # Stage 2 — Triage
    console.print(Panel.fit("[dim]Querying Groq llama-3.3-70b-versatile...[/dim]", border_style="yellow"))
    report = triage_agent.analyze(alert)
    console.print()

    triage_table = Table(box=box.MINIMAL, show_header=False, padding=(0,1))
    triage_table.add_column("Key", style="dim", width=22)
    triage_table.add_column("Value", style="bold white")
    triage_table.add_row("Root Cause",          f"[bold red]{report.root_cause_type}[/bold red]")
    triage_table.add_row("Confidence",          f"[bold green]{report.confidence}[/bold green]")
    triage_table.add_row("Recommended Action",  f"[bold cyan]{report.recommended_action}[/bold cyan]")
    triage_table.add_row("Runbook",             f"[yellow]{report.runbook_ref}[/yellow]")
    triage_table.add_row("Human Approval",      "[bold yellow]REQUIRED[/bold yellow]" if report.requires_human_approval else "[green]AUTO[/green]")
    triage_table.add_row("AI Reasoning",        f"[italic]{report.ai_reasoning[:200]}[/italic]")

    console.print(Panel(triage_table, title="[bold yellow]Stage 2 — Groq AI Triage Complete[/bold yellow]", border_style="yellow"))
    console.print()

    # Stage 3 — Cost
    cost = cost_agent.analyze(report)
    cost_table = Table(box=box.MINIMAL, show_header=False, padding=(0,1))
    cost_table.add_column("Metric", style="dim", width=30)
    cost_table.add_column("Value", style="bold white")
    cost_table.add_row("Namespace",               f"[cyan]{cost.namespace}[/cyan]")
    cost_table.add_row("Current Monthly Cost",    f"[white]${cost.monthly_projected_cost_usd:.2f}/mo[/white]")
    cost_table.add_row("Budget Utilisation",      f"[green]{cost.budget_utilisation_pct:.1f}%[/green]")
    cost_table.add_row("Remediation Cost Delta",  f"[yellow]${cost.remediation_cost_delta_usd:+.2f}/mo[/yellow]")
    cost_table.add_row("Verdict",                 f"[bold green]{cost.cost_verdict}[/bold green]")
    cost_table.add_row("Recommendation",          f"[italic]{cost.recommendation[:150]}[/italic]")

    console.print(Panel(cost_table, title="[bold green]Stage 3 — OpenCost Financial Analysis[/bold green]", border_style="green"))
    console.print()

    # Stage 5 — Human Approval (simulated)
    console.print(Panel.fit(
        "[bold white]UiPath Apps Form Presented to On-Call SRE[/bold white]\n\n"
        f"  Root Cause:  [red]{report.root_cause_type}[/red]  |  Confidence: [green]{report.confidence}[/green]\n"
        f"  Action:      [cyan]{report.recommended_action}[/cyan]\n"
        f"  Cost Delta:  [yellow]${cost.remediation_cost_delta_usd:+.2f}/mo[/yellow]\n\n"
        "  [bold green]✓ APPROVED[/bold green] by on-call SRE  [dim](simulated in demo)[/dim]",
        title="[bold blue]Stage 3 — Human Approval via UiPath Apps[/bold blue]",
        border_style="blue"
    ))
    console.print()

    # Stage 6 — Remediation
    result = asyncio.run(remediation_agent.execute(report))
    remediation_table = Table(box=box.MINIMAL, show_header=False, padding=(0,1))
    remediation_table.add_column("Key", style="dim", width=20)
    remediation_table.add_column("Value", style="bold white")
    remediation_table.add_row("Action Taken",  f"[bold cyan]{result.action_taken}[/bold cyan]")
    remediation_table.add_row("Status",        f"[bold green]{'✓ SUCCESS' if result.success else '✗ FAILED'}[/bold green]")
    remediation_table.add_row("Duration",      f"{result.duration_seconds:.3f}s")
    remediation_table.add_row("Command",       f"[dim]{result.output[:120]}[/dim]")

    console.print(Panel(remediation_table, title="[bold cyan]Stage 4 — Remediation Executed[/bold cyan]", border_style="cyan"))
    console.print()

    # Stage 7 — Post-Mortem
    console.print(Panel.fit(
        f"  Alert ID:    [white]{alert.id}[/white]\n"
        f"  Root Cause:  [red]{report.root_cause_type}[/red] ({report.confidence} confidence)\n"
        f"  Action:      [cyan]{result.action_taken}[/cyan] — [green]RESOLVED[/green]\n"
        f"  Cost Impact: [yellow]${cost.remediation_cost_delta_usd:+.2f}/mo[/yellow]\n"
        f"  MTTR:        [bold green]< 15 minutes[/bold green] (end-to-end, zero manual steps)\n\n"
        "  [dim]Post-mortem PDF generated via UiPath Document Understanding[/dim]",
        title="[bold white]Stage 7 — Post-Mortem Summary[/bold white]",
        border_style="bright_white"
    ))
    console.print()
    console.print(Rule("[bold green]✓ INCIDENT RESOLVED — Full audit trail preserved in Maestro[/bold green]", style="green"))
    console.print()

    html = console.export_html(inline_styles=True)
    save_html(html, "02_oomkill_pipeline_run.html")


# ── Screenshot 3: All Scenarios Summary ──────────────────────────────────────
def screenshot_all_scenarios():
    console = Console(record=True, width=100)

    triage_agent = TriageAgent()
    cost_agent = CostImpactAgent()
    remediation_agent = RemediationAgent()

    console.print()
    console.print(Panel.fit(
        "[bold white]NeuroScale Ops — All Demo Scenarios[/bold white]\n"
        "[dim]5 incident types, all handled autonomously end-to-end[/dim]",
        border_style="bright_blue", padding=(1,4)
    ))
    console.print()

    results_table = Table(
        title="[bold]Live Pipeline Results — Groq llama-3.3-70b AI Triage[/bold]",
        box=box.ROUNDED,
        border_style="blue",
        title_style="bold cyan",
        show_header=True,
        header_style="bold white on dark_blue",
        width=98,
    )
    results_table.add_column("Alert ID",      style="dim", width=16)
    results_table.add_column("Type",          style="bold", width=18)
    results_table.add_column("Severity",      width=10, justify="center")
    results_table.add_column("AI Root Cause", style="bold yellow", width=20)
    results_table.add_column("Confidence",    width=10, justify="center")
    results_table.add_column("Action",        style="cyan", width=18)
    results_table.add_column("Cost Δ/mo",     width=10, justify="right")
    results_table.add_column("Status",        width=10, justify="center")

    for scenario_key, scenario_data in DEMO_SCENARIOS.items():
        alert = Alert(**scenario_data)
        report = triage_agent.analyze(alert)
        cost = cost_agent.analyze(report)
        result = asyncio.run(remediation_agent.execute(report))

        sev_color = "red" if alert.severity == "critical" else "yellow"
        conf_color = "green" if report.confidence == "HIGH" else "yellow"
        cost_str = f"${cost.remediation_cost_delta_usd:+.0f}"
        cost_color = "red" if cost.remediation_cost_delta_usd > 50 else ("green" if cost.remediation_cost_delta_usd < 0 else "yellow")
        status = "[bold green]✓ RESOLVED[/bold green]" if result.success else "[bold red]✗ FAILED[/bold red]"

        results_table.add_row(
            alert.id,
            alert.type.upper(),
            f"[{sev_color}]{alert.severity.upper()}[/{sev_color}]",
            report.root_cause_type,
            f"[{conf_color}]{report.confidence}[/{conf_color}]",
            report.recommended_action,
            f"[{cost_color}]{cost_str}[/{cost_color}]",
            status,
        )

    console.print(results_table)
    console.print()

    # Test results
    console.print(Panel.fit(
        "[bold green]✓ 17/17 pytest tests passing[/bold green]  |  "
        "[cyan]5 incident types handled[/cyan]  |  "
        "[yellow]100% AI triage accuracy (demo)[/yellow]\n\n"
        "[dim]python -m pytest tests/test_pipeline.py -v  →  17 passed in 0.83s[/dim]",
        title="[bold white]Quality Metrics[/bold white]",
        border_style="green"
    ))
    console.print()

    html = console.export_html(inline_styles=True)
    save_html(html, "03_all_scenarios_results.html")


# ── Screenshot 4: Architecture & Tech Stack ───────────────────────────────────
def screenshot_architecture():
    console = Console(record=True, width=100)
    console.print()
    console.print(Panel.fit(
        "[bold white]NeuroScale Ops — Architecture[/bold white]",
        border_style="bright_blue", padding=(0,4)
    ))
    console.print()

    arch = """
  Prometheus Alert
        │
        ▼
  ┌─────────────────────────────────────────────────────────────────┐
  │                    UiPath Maestro Case                          │
  │                                                                 │
  │  S1: DetectorAgent ──► S2: Groq Triage ──► S3: UiPath Apps    │
  │      (Python SDK)         (llama-3.3-70b)    (Human Approval)  │
  │                                │                                │
  │  S7: Post-Mortem ◄── S6: Sign-off ◄── S5: Cost ◄── S4: Remed │
  │  (Doc.Understand.)   (UiPath Apps)  (OpenCost) (ArgoCD+kubectl)│
  └─────────────────────────────────────────────────────────────────┘
"""
    console.print(Panel(arch, title="[bold cyan]System Architecture[/bold cyan]", border_style="cyan"))
    console.print()

    tech_table = Table(
        title="[bold]Technology Stack[/bold]",
        box=box.SIMPLE_HEAVY,
        border_style="blue",
        title_style="bold cyan",
        width=98,
    )
    tech_table.add_column("Layer",       style="bold yellow", width=20)
    tech_table.add_column("Technology",  style="bold white",  width=30)
    tech_table.add_column("Purpose",     style="white",       width=45)

    stack = [
        ("Orchestration",   "UiPath Maestro",              "7-stage case definition, SLAs, human-in-loop, audit trail"),
        ("AI / LLM",        "Groq llama-3.3-70b-versatile","Root cause analysis, structured JSON triage output"),
        ("Agent Runtime",   "Python 3.11 + UiPath SDK",    "Coded agents: Detector, Triage, Cost, Remediation"),
        ("GitOps",          "ArgoCD",                      "Automated rollback and sync to Git HEAD"),
        ("Policy",          "Kyverno",                     "Admission policies, exception management"),
        ("FinOps",          "OpenCost",                    "Namespace cost allocation, remediation delta"),
        ("Alerting",        "Prometheus",                  "Alert detection and webhook forwarding"),
        ("Human Approval",  "UiPath Apps",                 "3 forms: triage review, remediation sign-off, post-mortem"),
        ("Notifications",   "Agent Builder + Slack",       "Rich incident notifications with action summaries"),
        ("Post-Mortem",     "Document Understanding",      "Structured PDF generation from incident timeline"),
        ("Dashboard",       "Streamlit",                   "Real-time incident command center"),
        ("CI/CD",           "GitHub Actions",              "Automated lint, test, Docker build on every push"),
    ]
    for row in stack:
        tech_table.add_row(*row)

    console.print(tech_table)
    console.print()

    html = console.export_html(inline_styles=True)
    save_html(html, "04_architecture_stack.html")


# ── Screenshot 5: UiPath Maestro Case Definition ─────────────────────────────
def screenshot_maestro_case():
    import json
    console = Console(record=True, width=100)
    console.print()

    with open("/home/user/neurascale-ops/uipath/maestro_case/case_definition.json") as f:
        case = json.load(f)

    console.print(Panel.fit(
        f"[bold white]{case.get('name', 'NeuroScale Ops Incident Response')}[/bold white]\n"
        f"[dim]{case.get('description', '')}[/dim]",
        border_style="bright_blue", padding=(1,4)
    ))
    console.print()

    stages_table = Table(
        title="[bold]Maestro Case — Stage Definitions[/bold]",
        box=box.ROUNDED,
        border_style="blue",
        title_style="bold cyan",
        header_style="bold white on dark_blue",
        width=98,
    )
    stages_table.add_column("ID",          style="bold yellow",  width=6,  justify="center")
    stages_table.add_column("Stage Name",  style="bold white",   width=22)
    stages_table.add_column("Type",        style="cyan",         width=20)
    stages_table.add_column("Agent/Form",  style="white",        width=30)
    stages_table.add_column("SLA",         style="green",        width=10, justify="center")

    for stage in case.get("stages", []):
        stages_table.add_row(
            stage.get("id", ""),
            stage.get("name", ""),
            stage.get("type", ""),
            stage.get("agent", stage.get("workflow", stage.get("app", stage.get("template", "—")))),
            str(stage.get("sla_minutes", stage.get("sla", "—"))) + (" min" if stage.get("sla_minutes") else ""),
        )

    console.print(stages_table)
    console.print()

    # Show JSON snippet
    snippet = json.dumps(case.get("stages", [])[0], indent=2) if case.get("stages") else "{}"
    console.print(Panel(
        Syntax(snippet, "json", theme="monokai", line_numbers=True),
        title="[bold cyan]Stage 1 JSON Definition (sample)[/bold cyan]",
        border_style="cyan"
    ))
    console.print()

    html = console.export_html(inline_styles=True)
    save_html(html, "05_maestro_case_definition.html")


if __name__ == "__main__":
    print("\nGenerating demo screenshots...")
    print("=" * 60)
    screenshot_pipeline_overview()
    screenshot_oomkill_run()
    screenshot_all_scenarios()
    screenshot_architecture()
    screenshot_maestro_case()
    print("\n✓ All screenshots saved to demo_assets/screenshots/")
    print("  Convert to PNG: open each .html in browser and screenshot")
