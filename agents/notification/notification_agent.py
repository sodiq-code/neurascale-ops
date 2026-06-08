"""
NeuroScale Ops — Notification Agent
Part of the UiPath Maestro Case pipeline (Stage 2.5: Notification & Routing).

Bridges between the Detector/Triage agents and UiPath Maestro.
Sends structured payloads to:
  - UiPath Orchestrator (Case creation webhook)
  - Slack (incident channel)
  - Email (on-call escalation)

In the hackathon demo, UiPath Agent Builder handles Slack/email;
this module handles the Maestro webhook call directly.
"""
from __future__ import annotations

import os
import json
import requests
from datetime import datetime, timezone
from typing import Optional

from agents.triage.triage_agent import TriageReport
from agents.cost_impact.cost_agent import CostReport


MAESTRO_WEBHOOK_URL  = os.getenv("MAESTRO_WEBHOOK_URL", "")
SLACK_WEBHOOK_URL    = os.getenv("SLACK_WEBHOOK_URL", "")
UIPATH_ORCHESTRATOR  = os.getenv("UIPATH_ORCHESTRATOR_URL", "https://cloud.uipath.com")
UIPATH_TENANT        = os.getenv("UIPATH_TENANT", "")
UIPATH_CLIENT_ID     = os.getenv("UIPATH_CLIENT_ID", "")
UIPATH_CLIENT_SECRET = os.getenv("UIPATH_CLIENT_SECRET", "")


class NotificationAgent:
    """
    Routes incident data to UiPath Maestro and optional Slack alerts.
    Uses UiPath Agent Builder JSON spec for the low-code counterpart.
    """

    def notify(
        self,
        triage: TriageReport,
        cost: Optional[CostReport] = None,
    ) -> dict:
        """
        Send triage + cost data to Maestro webhook and Slack.
        Returns a summary of notification results.
        """
        payload = self._build_maestro_payload(triage, cost)
        results = {}

        if MAESTRO_WEBHOOK_URL:
            results["maestro"] = self._send_maestro(payload)
        else:
            results["maestro"] = {"status": "skipped", "reason": "MAESTRO_WEBHOOK_URL not set (demo mode)"}

        if SLACK_WEBHOOK_URL:
            results["slack"] = self._send_slack(triage, cost)
        else:
            results["slack"] = {"status": "skipped", "reason": "SLACK_WEBHOOK_URL not set (demo mode)"}

        # Always print to console for demo visibility
        self._print_console(triage, cost)

        return results

    def _build_maestro_payload(self, triage: TriageReport, cost: Optional[CostReport]) -> dict:
        """Build the Maestro Case creation payload."""
        return {
            "case_type": "k8s_incident_response",
            "title": f"[{triage.severity.upper()}] {triage.root_cause_type} — {triage.alert_id}",
            "description": triage.description,
            "priority": "high" if triage.severity == "critical" else "medium",
            "metadata": {
                "alert_id": triage.alert_id,
                "root_cause_type": triage.root_cause_type,
                "confidence": triage.confidence,
                "severity": triage.severity,
                "recommended_action": triage.recommended_action,
                "runbook_ref": triage.runbook_ref,
                "ai_reasoning": triage.ai_reasoning,
                "requires_human_approval": triage.requires_human_approval,
                "cost_report": cost.to_dict() if cost else {},
                "timestamp": triage.timestamp,
            },
        }

    def _send_maestro(self, payload: dict) -> dict:
        """POST to UiPath Maestro webhook."""
        try:
            resp = requests.post(
                MAESTRO_WEBHOOK_URL,
                json=payload,
                timeout=15,
                headers={"Content-Type": "application/json"},
            )
            return {
                "status": "sent" if resp.status_code < 400 else "error",
                "status_code": resp.status_code,
                "response": resp.text[:200],
            }
        except Exception as e:
            return {"status": "error", "error": str(e)}

    def _send_slack(self, triage: TriageReport, cost: Optional[CostReport]) -> dict:
        """Send Slack notification with incident summary."""
        severity_emoji = {"critical": "🔴", "warning": "🟡", "info": "🟢"}.get(triage.severity, "⚪")
        cost_line = f"\n*Cost Impact:* `${cost.remediation_cost_delta_usd:+.2f}/mo` ({cost.cost_verdict})" if cost else ""

        msg = {
            "text": f"{severity_emoji} *NeuroScale Ops Incident Detected*",
            "attachments": [{
                "color": "#e74c3c" if triage.severity == "critical" else "#f39c12",
                "fields": [
                    {"title": "Alert ID",          "value": triage.alert_id,          "short": True},
                    {"title": "Root Cause",         "value": triage.root_cause_type,   "short": True},
                    {"title": "Confidence",         "value": triage.confidence,        "short": True},
                    {"title": "Severity",           "value": triage.severity.upper(),  "short": True},
                    {"title": "Recommended Action", "value": triage.recommended_action,"short": True},
                    {"title": "Runbook",            "value": triage.runbook_ref,       "short": True},
                    {"title": "Description",        "value": triage.description,       "short": False},
                ],
                "footer": f"NeuroScale Ops • UiPath Maestro Case • {triage.timestamp[:19]}Z",
            }],
        }

        try:
            resp = requests.post(SLACK_WEBHOOK_URL, json=msg, timeout=10)
            return {"status": "sent" if resp.status_code == 200 else "error", "status_code": resp.status_code}
        except Exception as e:
            return {"status": "error", "error": str(e)}

    def _print_console(self, triage: TriageReport, cost: Optional[CostReport]):
        """Rich console output for demo visibility."""
        from rich.console import Console
        from rich.panel import Panel
        from rich.table import Table
        import rich

        c = Console()
        c.print(f"\n[bold cyan]{'='*60}[/bold cyan]")
        c.print(f"[bold white]  NOTIFICATION AGENT — Incident Routed to Maestro[/bold white]")
        c.print(f"[bold cyan]{'='*60}[/bold cyan]")

        t = Table(show_header=False, box=None, padding=(0, 2))
        t.add_column(style="dim")
        t.add_column(style="white")
        t.add_row("Alert ID",   f"[bold]{triage.alert_id}[/bold]")
        t.add_row("Root Cause", f"[bold red]{triage.root_cause_type}[/bold red]")
        t.add_row("Severity",   f"[bold {'red' if triage.severity=='critical' else 'yellow'}]{triage.severity.upper()}[/bold {'red' if triage.severity=='critical' else 'yellow'}]")
        t.add_row("Confidence", triage.confidence)
        t.add_row("Action",     f"[green]{triage.recommended_action}[/green]")
        t.add_row("Runbook",    triage.runbook_ref)
        if cost:
            t.add_row("Cost Delta", f"${cost.remediation_cost_delta_usd:+.2f}/mo ({cost.cost_verdict})")
        t.add_row("Maestro",    "✓ Case Created" if MAESTRO_WEBHOOK_URL else "[dim]skipped (no webhook)[/dim]")
        t.add_row("Slack",      "✓ Notified" if SLACK_WEBHOOK_URL else "[dim]skipped[/dim]")
        c.print(t)
        c.print(f"\n  [dim]AI Reasoning: {triage.ai_reasoning[:120]}...[/dim]" if len(triage.ai_reasoning) > 120 else f"\n  [dim]AI Reasoning: {triage.ai_reasoning}[/dim]")
