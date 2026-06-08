"""
NeuroScale Ops — Triage Agent
Part of the UiPath Maestro Case pipeline (Stage 2: AI Triage).

Receives an Alert from the Detector, queries local runbook knowledge,
performs root cause analysis via Groq (llama-3.3-70b-versatile), and returns
a structured TriageReport to the Maestro Case for human approval (Stage 3).
"""
from __future__ import annotations

import json
import os
from dataclasses import dataclass, asdict
from typing import Optional
from datetime import datetime, timezone

try:
    from groq import Groq
    GROQ_AVAILABLE = bool(os.environ.get("GROQ_API_KEY"))
    _groq_client = Groq(api_key=os.environ.get("GROQ_API_KEY", "")) if GROQ_AVAILABLE else None
except ImportError:
    GROQ_AVAILABLE = False
    _groq_client = None

from agents.detector.detector import Alert


# ── Output schema ─────────────────────────────────────────────────────────────

@dataclass
class TriageReport:
    alert_id: str
    root_cause_type: str        # CPU_THROTTLING | OOMKILL | CRASHLOOP | POLICY_VIOLATION | COST_SPIKE | DEPLOYMENT_FAILURE
    confidence: str             # HIGH | MEDIUM | LOW
    severity: str
    description: str
    recommended_action: str     # patch_resources | rollback | scale_down | create_exception | monitor | escalate
    runbook_ref: str
    cost_impact_usd: float
    ai_reasoning: str
    timestamp: str
    requires_human_approval: bool
    namespace: str = "production"
    raw_data: dict = None       # populated from original Alert.raw_data

    def __post_init__(self):
        if self.raw_data is None:
            self.raw_data = {}

    def to_dict(self) -> dict:
        return asdict(self)

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2)


# ── Runbook knowledge base (embedded, no vector DB needed for demo) ────────────

RUNBOOK_KB: list[dict] = [
    {
        "id": "RB-001",
        "title": "OOMKill — Memory Limit Remediation",
        "tags": ["oomkill", "memory", "resource"],
        "action": "patch_resources",
        "description": "Increase container memory limits and requests by 2x, trigger rolling restart.",
        "cost_impact_usd": 15.0,
    },
    {
        "id": "RB-002",
        "title": "CrashLoopBackOff — Root Cause Analysis",
        "tags": ["crashloop", "crash", "restart"],
        "action": "rollback",
        "description": "Collect logs, identify crash cause, rollback to last stable image via ArgoCD.",
        "cost_impact_usd": 5.0,
    },
    {
        "id": "RB-003",
        "title": "Kyverno Policy Violation — Exception Creation",
        "tags": ["policy_violation", "kyverno", "policy"],
        "action": "create_exception",
        "description": "Create a scoped PolicyException after human approval for the specific workload.",
        "cost_impact_usd": 0.0,
    },
    {
        "id": "RB-004",
        "title": "Cost Spike — Namespace Budget Alert",
        "tags": ["cost_spike", "budget", "opencost", "finops"],
        "action": "scale_down",
        "description": "Scale down highest-cost workload after approval. Add resource quota to namespace.",
        "cost_impact_usd": -120.0,
    },
    {
        "id": "RB-005",
        "title": "Deployment Failure — Image Pull / Rollout",
        "tags": ["deployment_failure", "image", "rollout"],
        "action": "rollback",
        "description": "ArgoCD sync rollback to last healthy revision. Notify on-call via Slack.",
        "cost_impact_usd": 0.0,
    },
]


def _match_runbook(alert: Alert) -> dict:
    """Simple tag-based runbook lookup."""
    alert_type = alert.type.lower()
    for rb in RUNBOOK_KB:
        if any(tag in alert_type for tag in rb["tags"]):
            return rb
    return RUNBOOK_KB[0]


# ── Triage Agent ──────────────────────────────────────────────────────────────

class TriageAgent:
    """
    AI-powered triage agent.
    Uses Groq (llama-3.3-70b-versatile) for structured reasoning; falls back
    to rule-based classification when Groq is unavailable (demo/offline mode).
    """

    MODEL = "llama-3.3-70b-versatile"

    def analyze(self, alert: Alert) -> TriageReport:
        """Main triage entrypoint. Returns a TriageReport."""
        runbook = _match_runbook(alert)

        if GROQ_AVAILABLE and _groq_client:
            return self._groq_triage(alert, runbook)
        return self._rule_based_triage(alert, runbook)

    # ── Groq llama-3.3-70b path ───────────────────────────────────────────────

    def _groq_triage(self, alert: Alert, runbook: dict) -> TriageReport:
        """Call Groq llama-3.3-70b-versatile for structured root cause analysis."""
        prompt = f"""You are an expert Kubernetes SRE AI agent performing incident triage.
Analyze the following alert and the matching runbook. Return ONLY valid JSON.

ALERT:
- id: {alert.id}
- type: {alert.type}
- severity: {alert.severity}
- namespace: {alert.namespace}
- resource: {alert.resource}
- message: {alert.message}
- raw_data: {json.dumps(alert.raw_data)}

MATCHING RUNBOOK ({runbook['id']}):
- title: {runbook['title']}
- recommended_action: {runbook['action']}
- description: {runbook['description']}

Respond ONLY with this exact JSON schema (no markdown, no explanation):
{{
  "root_cause_type": "OOMKILL|CRASHLOOP|CPU_THROTTLING|POLICY_VIOLATION|COST_SPIKE|DEPLOYMENT_FAILURE",
  "confidence": "HIGH|MEDIUM|LOW",
  "description": "<one-sentence root cause>",
  "recommended_action": "patch_resources|rollback|scale_down|create_exception|monitor|escalate",
  "ai_reasoning": "<2-3 sentences explaining diagnosis and why this action is recommended>",
  "requires_human_approval": true
}}"""

        try:
            response = _groq_client.chat.completions.create(
                model=self.MODEL,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=512,
                response_format={"type": "json_object"},
            )
            raw = response.choices[0].message.content
            result = json.loads(raw)

            return TriageReport(
                alert_id=alert.id,
                root_cause_type=result.get("root_cause_type", alert.type.upper()),
                confidence=result.get("confidence", "MEDIUM"),
                severity=alert.severity,
                description=result.get("description", alert.message),
                recommended_action=result.get("recommended_action", runbook["action"]),
                runbook_ref=runbook["id"],
                cost_impact_usd=runbook["cost_impact_usd"],
                ai_reasoning=result.get("ai_reasoning", ""),
                timestamp=datetime.now(timezone.utc).isoformat(),
                requires_human_approval=result.get("requires_human_approval", True),
                namespace=alert.namespace,
                raw_data=alert.raw_data,
            )

        except Exception as e:
            print(f"[TriageAgent] Groq call failed: {e} — falling back to rule-based")
            return self._rule_based_triage(alert, runbook)

    # ── Rule-based fallback ───────────────────────────────────────────────────

    def _rule_based_triage(self, alert: Alert, runbook: dict) -> TriageReport:
        """Deterministic triage for demo/offline mode."""
        type_map = {
            "oomkill":            ("OOMKILL",            "Container exceeded memory limit and was OOMKilled by the kernel."),
            "crashloop":          ("CRASHLOOP",           "Container is crash-looping; likely config error or missing dependency."),
            "policy_violation":   ("POLICY_VIOLATION",    "Kyverno admission policy blocked the workload deployment."),
            "cost_spike":         ("COST_SPIKE",          "Namespace compute spend exceeded budget threshold by >40%."),
            "deployment_failure": ("DEPLOYMENT_FAILURE",  "Kubernetes deployment rollout failed due to image pull error."),
        }
        rca_type, rca_desc = type_map.get(alert.type, ("UNKNOWN", alert.message))

        return TriageReport(
            alert_id=alert.id,
            root_cause_type=rca_type,
            confidence="HIGH",
            severity=alert.severity,
            description=rca_desc,
            recommended_action=runbook["action"],
            runbook_ref=runbook["id"],
            cost_impact_usd=runbook["cost_impact_usd"],
            ai_reasoning=(
                f"Rule-based triage matched alert type '{alert.type}' to runbook {runbook['id']}. "
                f"Recommended action: {runbook['action']}. "
                f"Human approval required before execution per NeuroScale Ops policy."
            ),
            timestamp=datetime.now(timezone.utc).isoformat(),
            requires_human_approval=True,
            namespace=alert.namespace,
            raw_data=alert.raw_data,
        )


# ── CLI usage ─────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    from agents.detector.detector import DEMO_SCENARIOS, Alert

    agent = TriageAgent()
    for scenario_name, scenario_data in DEMO_SCENARIOS.items():
        alert = Alert(**scenario_data)
        report = agent.analyze(alert)
        print(f"\n{'='*60}")
        print(f"  TRIAGE REPORT — {scenario_name.upper()}")
        print(f"{'='*60}")
        print(report.to_json())
