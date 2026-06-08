"""
NeuroScale Ops — Integration Tests
Runs the full detection→triage→cost→remediation pipeline in DEMO_MODE.
No real Kubernetes cluster, no OpenAI API key required.
"""
import os
import asyncio
import pytest

# Force demo mode for all tests
os.environ["DEMO_MODE"] = "true"
os.environ["GROQ_API_KEY"] = ""  # ensure rule-based path  # ensure rule-based path

from agents.detector.detector import Alert, DetectorAgent, DEMO_SCENARIOS
from agents.triage.triage_agent import TriageAgent, TriageReport
from agents.remediation.remediation_agent import RemediationAgent, ExecutionResult
from agents.cost_impact.cost_agent import CostImpactAgent, CostReport
from agents.notification.notification_agent import NotificationAgent


# ── Helpers ────────────────────────────────────────────────────────────────────

def make_alert(scenario_key: str = "oomkill") -> Alert:
    """Build a demo Alert directly from DEMO_SCENARIOS."""
    return Alert(**DEMO_SCENARIOS[scenario_key])


# ── Stage 1: Detection ─────────────────────────────────────────────────────────

class TestDetectorAgent:
    def test_demo_scenarios_exist(self):
        assert len(DEMO_SCENARIOS) >= 3

    def test_alert_model(self):
        alert = make_alert("oomkill")
        assert alert.id
        assert alert.severity in ("critical", "warning", "info")
        assert alert.type == "oomkill"
        assert alert.namespace
        assert alert.resource

    def test_all_scenarios_valid(self):
        for key, data in DEMO_SCENARIOS.items():
            alert = Alert(**data)
            assert alert.id, f"Missing id in scenario {key}"
            assert alert.type, f"Missing type in scenario {key}"

    def test_detector_agent_emit(self):
        """DetectorAgent can emit an alert synchronously via trigger_demo_alert."""
        received = []

        def handler(a: Alert):
            received.append(a)

        agent = DetectorAgent(on_alert=handler)

        async def run():
            await agent.simulate_alert("oomkill")

        asyncio.run(run())
        assert len(received) == 1
        assert received[0].type == "oomkill"


# ── Stage 2: AI Triage ────────────────────────────────────────────────────────

class TestTriageAgent:
    def test_rule_based_triage_oomkill(self):
        alert = make_alert("oomkill")
        agent = TriageAgent()
        report = agent.analyze(alert)

        assert isinstance(report, TriageReport)
        assert report.alert_id == alert.id
        assert report.root_cause_type in (
            "OOMKILL", "CPU_THROTTLING", "CRASHLOOP",
            "POLICY_VIOLATION", "COST_SPIKE", "DEPLOYMENT_FAILURE"
        )
        assert report.confidence in ("HIGH", "MEDIUM", "LOW")
        assert report.recommended_action in (
            "patch_resources", "rollback", "scale_down",
            "create_exception", "monitor", "escalate"
        )
        assert report.severity
        assert report.runbook_ref

    def test_rule_based_triage_crashloop(self):
        alert = make_alert("crashloop")
        agent = TriageAgent()
        report = agent.analyze(alert)
        assert report.root_cause_type in ("CRASHLOOP", "OOMKILL", "DEPLOYMENT_FAILURE")

    def test_rule_based_triage_cost_spike(self):
        alert = make_alert("cost_spike")
        agent = TriageAgent()
        report = agent.analyze(alert)
        assert report.root_cause_type in ("COST_SPIKE", "CPU_THROTTLING")

    def test_triage_report_serialization(self):
        alert = make_alert("oomkill")
        agent = TriageAgent()
        report = agent.analyze(alert)
        d = report.to_dict()
        assert "root_cause_type" in d
        assert "recommended_action" in d
        j = report.to_json()
        import json
        parsed = json.loads(j)
        assert parsed["alert_id"] == alert.id


# ── Stage 3: Cost Impact ──────────────────────────────────────────────────────

class TestCostImpactAgent:
    def test_cost_analysis_returns_report(self):
        alert = make_alert("oomkill")
        triage = TriageAgent().analyze(alert)
        agent = CostImpactAgent()
        cost = agent.analyze(triage)

        assert isinstance(cost, CostReport)
        assert cost.namespace
        assert cost.monthly_projected_cost_usd >= 0
        assert 0.0 <= cost.budget_utilisation_pct <= 200.0
        assert cost.cost_verdict in ("OVER_BUDGET", "AT_RISK", "HEALTHY", "WITHIN_BUDGET")

    def test_cost_serialization(self):
        alert = make_alert("oomkill")
        triage = TriageAgent().analyze(alert)
        cost = CostImpactAgent().analyze(triage)
        d = cost.to_dict()
        assert "monthly_projected_cost_usd" in d


# ── Stage 6: Remediation ──────────────────────────────────────────────────────

class TestRemediationAgent:
    def test_remediation_executes(self):
        alert = make_alert("oomkill")
        triage = TriageAgent().analyze(alert)
        agent = RemediationAgent()

        async def run():
            return await agent.execute(triage)

        result = asyncio.run(run())
        assert isinstance(result, ExecutionResult)
        assert result.alert_id == triage.alert_id
        assert result.action_taken
        assert result.timestamp

    def test_all_action_types(self):
        """Every recommended_action type should dispatch without raising."""
        actions = [
            "patch_resources", "rollback", "scale_down",
            "create_exception", "monitor", "escalate"
        ]
        agent = RemediationAgent()
        base_alert = make_alert("oomkill")
        base_triage = TriageAgent().analyze(base_alert)

        for action in actions:
            base_triage.recommended_action = action

            async def run(t=base_triage):
                return await agent.execute(t)

            result = asyncio.run(run())
            assert result.action_taken, f"No action_taken for {action}"


# ── Stage 4: Notification ─────────────────────────────────────────────────────

class TestNotificationAgent:
    def test_notify_returns_payload(self):
        alert = make_alert("oomkill")
        triage = TriageAgent().analyze(alert)
        cost = CostImpactAgent().analyze(triage)
        agent = NotificationAgent()
        result = agent.notify(triage, cost)
        assert isinstance(result, dict)

    def test_notify_without_cost(self):
        alert = make_alert("oomkill")
        triage = TriageAgent().analyze(alert)
        agent = NotificationAgent()
        result = agent.notify(triage, None)
        assert isinstance(result, dict)


# ── Full Pipeline (E2E) ───────────────────────────────────────────────────────

class TestEndToEndPipeline:
    """Smoke test: full pipeline runs for each demo scenario."""

    @pytest.mark.parametrize("scenario", ["oomkill", "crashloop", "cost_spike"])
    def test_full_pipeline(self, scenario):
        alert = make_alert(scenario)
        triage_agent = TriageAgent()
        cost_agent = CostImpactAgent()
        remediation_agent = RemediationAgent()
        notification_agent = NotificationAgent()

        # Stage 2
        triage = triage_agent.analyze(alert)
        assert triage.alert_id == alert.id

        # Stage 3
        cost = cost_agent.analyze(triage)
        assert cost.monthly_projected_cost_usd >= 0

        # Stage 4
        notif = notification_agent.notify(triage, cost)
        assert notif

        # Stage 6
        async def run():
            return await remediation_agent.execute(triage)

        result = asyncio.run(run())
        assert result.action_taken

        print(f"\n  [{scenario.upper()}] Pipeline OK: "
              f"{triage.root_cause_type} → {result.action_taken}")
