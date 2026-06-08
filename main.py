"""
NeuroScale Ops — Main Entry Point
Runs the full incident response pipeline end-to-end.

Usage:
    python main.py                       # Full pipeline demo
    python main.py --scenario oomkill    # Specific scenario
    python main.py --scenario all        # All scenarios
    python main.py --list                # List scenarios
"""
from __future__ import annotations

import asyncio
import argparse
import json
import os
import sys

from agents.detector.detector import DetectorAgent, Alert, DEMO_SCENARIOS
from agents.triage.triage_agent import TriageAgent
from agents.cost_impact.cost_agent import CostImpactAgent
from agents.remediation.remediation_agent import RemediationAgent
from agents.notification.notification_agent import NotificationAgent


class NeuroScaleOpsPipeline:
    """
    End-to-end incident response pipeline.
    Maps directly to the UiPath Maestro Case 7-stage definition.

    Stage 1: Detection        — DetectorAgent
    Stage 2: AI Triage        — TriageAgent (Groq llama-3.3-70b)
    Stage 3: Cost Analysis    — CostImpactAgent (OpenCost)
    Stage 4: Notification     — NotificationAgent → Maestro
    Stage 5: Human Approval   — (Simulated in demo)
    Stage 6: Remediation      — RemediationAgent (kubectl/ArgoCD)
    Stage 7: Post-Mortem      — (UiPath Document Understanding)
    """

    def __init__(self, auto_approve: bool = True):
        self.triage_agent       = TriageAgent()
        self.cost_agent         = CostImpactAgent()
        self.remediation_agent  = RemediationAgent()
        self.notification_agent = NotificationAgent()
        self.auto_approve       = auto_approve

    async def run(self, alert: Alert) -> dict:
        """Execute the full pipeline for a given alert."""
        print(f"\n{'='*70}")
        print(f"  NEURASCALE OPS — INCIDENT RESPONSE PIPELINE")
        print(f"  Alert: {alert.id} | Type: {alert.type} | Severity: {alert.severity}")
        print(f"{'='*70}")

        results = {"alert_id": alert.id, "stages": {}}

        # ── Stage 2: AI Triage ─────────────────────────────────────────────
        print(f"\n  [STAGE 2] AI Triage (Groq llama-3.3-70b)...")
        triage = self.triage_agent.analyze(alert)
        results["stages"]["triage"] = triage.to_dict()
        print(f"  ✓ Root Cause: {triage.root_cause_type} ({triage.confidence})")
        print(f"    → Action:   {triage.recommended_action}")
        print(f"    → Runbook:  {triage.runbook_ref}")

        # ── Stage 3: Cost Analysis ─────────────────────────────────────────
        print(f"\n  [STAGE 3] Cost Impact Analysis (OpenCost)...")
        cost = self.cost_agent.analyze(triage)
        results["stages"]["cost"] = cost.to_dict()
        print(f"  ✓ Namespace: {cost.namespace} | ${cost.monthly_projected_cost_usd:.2f}/mo projected")
        print(f"    → Budget:   {cost.budget_utilisation_pct:.1f}% utilised ({cost.cost_verdict})")
        print(f"    → Delta:    ${cost.remediation_cost_delta_usd:+.2f}/mo for proposed action")

        # ── Stage 4: Notification → Maestro ────────────────────────────────
        print(f"\n  [STAGE 4] Routing to UiPath Maestro...")
        notif = self.notification_agent.notify(triage, cost)
        results["stages"]["notification"] = notif

        # ── Stage 5: Human Approval (simulated) ────────────────────────────
        print(f"\n  [STAGE 5] Human Approval...")
        if triage.requires_human_approval:
            if self.auto_approve:
                print(f"  ✓ [DEMO] Auto-approved. In production: UiPath Apps form presented to SRE.")
                approved = True
            else:
                resp = input(f"  Approve '{triage.recommended_action}' for {alert.resource}? [y/N]: ").strip().lower()
                approved = resp == "y"
        else:
            print(f"  ✓ Approval not required (low-severity action)")
            approved = True

        results["stages"]["approval"] = {"approved": approved, "auto": self.auto_approve}

        # ── Stage 6: Remediation ────────────────────────────────────────────
        if approved:
            print(f"\n  [STAGE 6] Executing Remediation ({triage.recommended_action})...")
            execution = await self.remediation_agent.execute(triage)
            results["stages"]["execution"] = execution.model_dump()
            if execution.success:
                print(f"  ✓ Remediation successful ({execution.duration_seconds:.1f}s)")
                print(f"    Output: {execution.output[:120]}")
            else:
                print(f"  ✗ Remediation failed: {execution.error}")
        else:
            print(f"\n  [STAGE 6] Skipped — Rejected by engineer. Escalating...")
            results["stages"]["execution"] = {"skipped": True, "reason": "rejected"}

        # ── Stage 7: Post-Mortem summary ────────────────────────────────────
        print(f"\n  [STAGE 7] Post-Mortem Summary")
        print(f"  ─────────────────────────────────────────────────────────")
        print(f"  Alert ID:        {alert.id}")
        print(f"  Root Cause:      {triage.root_cause_type}")
        print(f"  Confidence:      {triage.confidence}")
        print(f"  Action Taken:    {triage.recommended_action}")
        print(f"  Cost Impact:     ${triage.cost_impact_usd:+.2f}/mo")
        print(f"  Resolution:      {'Resolved' if approved and results['stages'].get('execution', {}).get('success') else 'Escalated'}")
        print(f"  ─────────────────────────────────────────────────────────")
        print(f"  AI Reasoning: {triage.ai_reasoning[:200]}")
        print(f"\n  [DONE] Pipeline complete for {alert.id}")

        results["summary"] = {
            "root_cause": triage.root_cause_type,
            "action_taken": triage.recommended_action,
            "resolved": approved,
            "cost_delta_usd": triage.cost_impact_usd,
        }

        return results


async def main():
    parser = argparse.ArgumentParser(description="NeuroScale Ops — AI Incident Response Pipeline")
    parser.add_argument("--scenario", default="oomkill", choices=list(DEMO_SCENARIOS.keys()) + ["all"])
    parser.add_argument("--list", action="store_true")
    parser.add_argument("--interactive", action="store_true", help="Prompt for human approval")
    parser.add_argument("--output", help="Save results to JSON file")
    args = parser.parse_args()

    if args.list:
        print("Available demo scenarios:")
        for k, v in DEMO_SCENARIOS.items():
            print(f"  {k:25s} — {v['message'][:60]}")
        return

    pipeline = NeuroScaleOpsPipeline(auto_approve=not args.interactive)

    if args.scenario == "all":
        all_results = {}
        for scenario_name, scenario_data in DEMO_SCENARIOS.items():
            alert = Alert(**scenario_data)
            result = await pipeline.run(alert)
            all_results[scenario_name] = result
        if args.output:
            with open(args.output, "w") as f:
                json.dump(all_results, f, indent=2)
            print(f"\nResults saved to {args.output}")
    else:
        scenario_data = DEMO_SCENARIOS[args.scenario]
        alert = Alert(**scenario_data)
        result = await pipeline.run(alert)
        if args.output:
            with open(args.output, "w") as f:
                json.dump(result, f, indent=2)
            print(f"\nResults saved to {args.output}")


if __name__ == "__main__":
    asyncio.run(main())
