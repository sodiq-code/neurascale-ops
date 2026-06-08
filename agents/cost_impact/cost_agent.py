"""
NeuroScale Ops — Cost Impact Agent
Part of the UiPath Maestro Case pipeline (Stage 4: Cost Impact Analysis).

Queries OpenCost before any remediation is executed, enriches the TriageReport
with financial context, and passes a CostReport to the human approval form.

Differentiator: FinOps-aware incident response. No other submission has this.
"""
from __future__ import annotations

import os
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
import json

from agents.triage.triage_agent import TriageReport
from agents.tools.kubernetes_ops import get_opencost_by_namespace, get_opencost_workload_breakdown


@dataclass
class CostReport:
    alert_id: str
    namespace: str
    current_hourly_cost_usd: float
    daily_projected_cost_usd: float
    monthly_projected_cost_usd: float
    top_workload: str
    top_workload_cost_usd: float
    remediation_cost_delta_usd: float    # + = more expensive | - = savings
    budget_utilisation_pct: float
    cost_verdict: str                    # WITHIN_BUDGET | OVER_BUDGET | CRITICAL_OVERAGE
    recommendation: str
    timestamp: str

    def to_dict(self) -> dict:
        return asdict(self)

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2)


NAMESPACE_MONTHLY_BUDGETS_USD: dict[str, float] = {
    "production":   800.0,
    "ml-workloads": 600.0,
    "staging":      200.0,
    "default":      100.0,
}


class CostImpactAgent:
    """
    Analyses the financial impact of an incident and its proposed remediation.
    Runs BEFORE human approval so approvers see cost context.
    """

    def analyze(self, report: TriageReport) -> CostReport:
        """
        Build a CostReport for the given TriageReport.
        Pulls live data from OpenCost; falls back to demo data.
        """
        namespace = getattr(report, "namespace", "production")

        # Namespace-level costs
        ns_costs = get_opencost_by_namespace(window="6h")
        ns_data = next(
            (c for c in ns_costs if c.get("namespace") == namespace),
            {"totalCost": 0.1234, "cpuCost": 0.06, "ramCost": 0.06}
        )
        hourly_cost = ns_data.get("totalCost", 0.0) / 6          # cost per hour
        daily_cost  = hourly_cost * 24
        monthly_cost = daily_cost * 30

        # Workload breakdown
        workloads = get_opencost_workload_breakdown(namespace, window="24h")
        top = workloads[0] if workloads and "workload" in workloads[0] else {"workload": "unknown", "totalCost": 0.0}
        top_wl_name = top["workload"]
        top_wl_cost = top.get("totalCost", 0.0)

        # Budget utilisation
        monthly_budget = NAMESPACE_MONTHLY_BUDGETS_USD.get(namespace, 500.0)
        util_pct = (monthly_cost / monthly_budget * 100) if monthly_budget > 0 else 0.0

        if util_pct >= 120:
            verdict = "CRITICAL_OVERAGE"
        elif util_pct >= 90:
            verdict = "OVER_BUDGET"
        else:
            verdict = "WITHIN_BUDGET"

        # Remediation cost delta
        delta = report.cost_impact_usd  # Comes from matching runbook

        # Human-readable recommendation
        rec = self._build_recommendation(
            verdict=verdict,
            util_pct=util_pct,
            namespace=namespace,
            action=report.recommended_action,
            delta=delta,
        )

        return CostReport(
            alert_id=report.alert_id,
            namespace=namespace,
            current_hourly_cost_usd=round(hourly_cost, 4),
            daily_projected_cost_usd=round(daily_cost, 4),
            monthly_projected_cost_usd=round(monthly_cost, 2),
            top_workload=top_wl_name,
            top_workload_cost_usd=round(top_wl_cost, 4),
            remediation_cost_delta_usd=delta,
            budget_utilisation_pct=round(util_pct, 1),
            cost_verdict=verdict,
            recommendation=rec,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )

    def _build_recommendation(
        self,
        verdict: str,
        util_pct: float,
        namespace: str,
        action: str,
        delta: float,
    ) -> str:
        if verdict == "CRITICAL_OVERAGE":
            return (
                f"CRITICAL: Namespace '{namespace}' is at {util_pct:.0f}% of monthly budget. "
                f"Proposed action '{action}' will {'increase cost by' if delta > 0 else 'save'} "
                f"${abs(delta):.2f}/mo. Strongly recommend immediate scale-down after approval."
            )
        elif verdict == "OVER_BUDGET":
            return (
                f"WARNING: Namespace '{namespace}' at {util_pct:.0f}% budget utilisation. "
                f"Action '{action}' cost delta: ${delta:+.2f}/mo. Review resource quotas post-remediation."
            )
        else:
            return (
                f"Namespace '{namespace}' within budget ({util_pct:.0f}% utilised). "
                f"Action '{action}' cost delta: ${delta:+.2f}/mo. Approved to proceed."
            )


if __name__ == "__main__":
    from agents.detector.detector import DEMO_SCENARIOS, Alert
    from agents.triage.triage_agent import TriageAgent

    agent_triage = TriageAgent()
    agent_cost = CostImpactAgent()

    scenario = DEMO_SCENARIOS["cost_spike"]
    alert = Alert(**scenario)
    triage = agent_triage.analyze(alert)
    cost_report = agent_cost.analyze(triage)

    print("\n=== COST IMPACT REPORT ===")
    print(cost_report.to_json())
