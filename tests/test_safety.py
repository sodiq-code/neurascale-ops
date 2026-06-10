"""
Tests for neurascale-ops safety fixes:
  1. Blast radius guard on _scale_down (MIN_SAFE_REPLICAS)
  2. Per-action confidence threshold gate in execute()
"""
import asyncio
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from unittest.mock import patch, AsyncMock, MagicMock

from agents.remediation.remediation_agent import (
    RemediationAgent,
    ExecutionResult,
    MIN_SAFE_REPLICAS,
    ACTION_CONFIDENCE_THRESHOLDS,
    CONFIDENCE_STR_TO_FLOAT,
)
from agents.triage.triage_agent import TriageReport
from datetime import datetime, timezone


def _make_report(**overrides) -> TriageReport:
    """Helper: build a TriageReport with sensible defaults."""
    defaults = dict(
        alert_id="ALERT-TEST-001",
        root_cause_type="OOMKILL",
        confidence="HIGH",
        severity="CRITICAL",
        description="Container OOMKilled",
        recommended_action="patch_resources",
        runbook_ref="RB-001",
        cost_impact_usd=15.0,
        ai_reasoning="Test reasoning",
        timestamp=datetime.now(timezone.utc).isoformat(),
        requires_human_approval=True,
        namespace="production",
        raw_data={},
    )
    defaults.update(overrides)
    return TriageReport(**defaults)


# ─── Blast Radius: MIN_SAFE_REPLICAS ─────────────────────────────────────────

class TestScaleDownBlastRadius:

    def test_min_safe_replicas_is_one(self):
        """MIN_SAFE_REPLICAS must be at least 1 — never allow scaling to zero."""
        assert MIN_SAFE_REPLICAS >= 1

    @pytest.mark.asyncio
    async def test_scale_down_uses_min_safe_replicas(self):
        """_scale_down must pass MIN_SAFE_REPLICAS (not 0) to kubectl."""
        agent = RemediationAgent()
        report = _make_report(
            recommended_action="scale_down",
            confidence="HIGH",
            raw_data={"top_consumer": "neurascale-inference"},
        )
        captured_cmd = []

        async def fake_run(cmd, timeout=120):
            captured_cmd.extend(cmd)
            return f"[DEMO] {' '.join(cmd)}", "", True

        agent._run = fake_run
        result = await agent._scale_down(report)

        # Must contain --replicas=1 (or whatever MIN_SAFE_REPLICAS is), never --replicas=0
        replicas_args = [a for a in captured_cmd if a.startswith("--replicas=")]
        assert len(replicas_args) == 1
        replicas_value = int(replicas_args[0].split("=")[1])
        assert replicas_value >= MIN_SAFE_REPLICAS
        assert replicas_value > 0

    @pytest.mark.asyncio
    async def test_scale_down_result_contains_blast_note(self):
        """Result dict must include blast_radius_note for auditability."""
        agent = RemediationAgent()
        report = _make_report(
            recommended_action="scale_down",
            confidence="HIGH",
            raw_data={"top_consumer": "neurascale-inference"},
        )

        async def fake_run(cmd, timeout=120):
            return "[DEMO]", "", True

        agent._run = fake_run
        result = await agent._scale_down(report)
        assert "blast_radius_note" in result
        assert str(MIN_SAFE_REPLICAS) in result["blast_radius_note"]


# ─── Per-Action Confidence Threshold Gate ─────────────────────────────────────

class TestConfidenceGate:

    def test_confidence_thresholds_defined(self):
        """All expected action types have thresholds."""
        expected = {"patch_resources", "rollback", "scale_down", "create_exception", "monitor", "escalate"}
        assert expected.issubset(set(ACTION_CONFIDENCE_THRESHOLDS.keys()))

    def test_destructive_actions_have_higher_thresholds(self):
        """rollback and scale_down need higher confidence than patch_resources."""
        assert ACTION_CONFIDENCE_THRESHOLDS["rollback"] >= ACTION_CONFIDENCE_THRESHOLDS["patch_resources"]
        assert ACTION_CONFIDENCE_THRESHOLDS["scale_down"] >= ACTION_CONFIDENCE_THRESHOLDS["patch_resources"]

    def test_all_thresholds_in_valid_range(self):
        for action, thresh in ACTION_CONFIDENCE_THRESHOLDS.items():
            assert 0.0 < thresh <= 1.0, f"{action}: {thresh} out of range"

    def test_confidence_string_mapping(self):
        assert CONFIDENCE_STR_TO_FLOAT["HIGH"]   == pytest.approx(0.90)
        assert CONFIDENCE_STR_TO_FLOAT["MEDIUM"] == pytest.approx(0.75)
        assert CONFIDENCE_STR_TO_FLOAT["LOW"]    == pytest.approx(0.50)

    @pytest.mark.asyncio
    async def test_low_confidence_blocked_for_rollback(self):
        """confidence=LOW (0.50) for rollback action → execute() returns blocked result."""
        agent = RemediationAgent()
        # Bypass circuit breaker
        with patch.object(agent.circuit_breaker, "is_open", return_value=False):
            report = _make_report(
                recommended_action="rollback",
                confidence="LOW",   # 0.50, below rollback threshold of 0.85
            )
            result = await agent.execute(report)

        assert result.success is False
        assert "confidence" in result.action_taken.lower() or "gate" in result.action_taken.lower() or "blocked" in result.action_taken.lower()
        assert "rollback" in result.error.lower()
        assert "0.85" in result.error or "85%" in result.error or "required" in result.error.lower()

    @pytest.mark.asyncio
    async def test_high_confidence_passes_for_patch_resources(self):
        """confidence=HIGH (0.90) for patch_resources → not blocked by confidence gate."""
        agent = RemediationAgent()

        with patch.object(agent.circuit_breaker, "is_open", return_value=False):
            report = _make_report(
                recommended_action="patch_resources",
                confidence="HIGH",
            )

            async def fake_patch(report):
                return {"success": True, "output": "[DEMO] patched", "error": None}

            agent._patch_resources = fake_patch
            result = await agent.execute(report)

        # Should NOT be blocked by confidence gate
        assert "confidence_gate_blocked" != result.action_taken

    @pytest.mark.asyncio
    async def test_medium_confidence_blocked_for_rollback(self):
        """confidence=MEDIUM (0.75) for rollback → blocked (threshold 0.85)."""
        agent = RemediationAgent()
        with patch.object(agent.circuit_breaker, "is_open", return_value=False):
            report = _make_report(
                recommended_action="rollback",
                confidence="MEDIUM",  # 0.75 < 0.85
            )
            result = await agent.execute(report)

        assert result.success is False
        assert "confidence_gate_blocked" in result.action_taken

    @pytest.mark.asyncio
    async def test_monitor_action_passes_with_low_confidence(self):
        """monitor action has 0.50 threshold → LOW confidence should pass."""
        agent = RemediationAgent()
        with patch.object(agent.circuit_breaker, "is_open", return_value=False):
            report = _make_report(
                recommended_action="monitor",
                confidence="LOW",  # 0.50, exactly at monitor threshold
            )
            result = await agent.execute(report)

        # monitor action: confidence gate should pass, action taken
        assert "confidence_gate_blocked" != result.action_taken

    @pytest.mark.asyncio
    async def test_circuit_breaker_checked_before_confidence_gate(self):
        """Circuit breaker takes priority over confidence gate."""
        agent = RemediationAgent()
        with patch.object(agent.circuit_breaker, "is_open", return_value=True):
            report = _make_report(recommended_action="patch_resources", confidence="HIGH")
            result = await agent.execute(report)

        assert result.success is False
        assert "Circuit breaker" in result.error or "circuit" in result.error.lower()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
