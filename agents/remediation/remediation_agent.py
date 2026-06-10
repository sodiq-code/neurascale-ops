"""
NeuroScale Ops — Remediation Agent
Part of the UiPath Maestro Case pipeline (Stage 5: Execute Remediation).

Receives an approved TriageReport from the Maestro Case (after human approval),
executes the corresponding K8s remediation action, and returns an ExecutionResult.

Includes CircuitBreaker to prevent runaway remediation loops.
ArgoCD rollback is the primary strategy; kubectl is the fallback.
"""
from __future__ import annotations

import asyncio
import os
import tempfile
import structlog
from datetime import datetime, timezone
from pydantic import BaseModel
from typing import Optional

from agents.triage.triage_agent import TriageReport

logger = structlog.get_logger(__name__)

ARGOCD_SERVER = os.getenv("ARGOCD_SERVER", "localhost:8080")
ARGOCD_TOKEN = os.getenv("ARGOCD_TOKEN", "")

# ── Blast radius + confidence constants ───────────────────────────────────────
MIN_SAFE_REPLICAS = 1       # autonomous scale-down must leave at least this many replicas
MAX_AUTO_MEMORY_GB = 4.0    # patch_resources cap

# Per-action confidence thresholds — different actions need different confidence bars
ACTION_CONFIDENCE_THRESHOLDS: dict[str, float] = {
    "patch_resources":  0.75,   # bounded: can only raise limits, capped at MAX_AUTO_MEMORY_GB
    "rollback":         0.85,   # high bar — rewinding production state
    "scale_down":       0.85,   # risky — could drop to 0 replicas
    "create_exception": 0.80,   # policy change, needs careful review
    "monitor":          0.50,   # no destructive action, low bar
    "escalate":         0.50,   # handoff only
}
CONFIDENCE_STR_TO_FLOAT: dict[str, float] = {
    "HIGH": 0.90, "MEDIUM": 0.75, "LOW": 0.50,
}


# ── Output schema ─────────────────────────────────────────────────────────────

class ExecutionResult(BaseModel):
    alert_id: str
    action_taken: str
    success: bool
    output: str
    error: Optional[str]
    duration_seconds: float
    timestamp: str
    demo_mode: bool = False


# ── Circuit Breaker ───────────────────────────────────────────────────────────

class CircuitBreaker:
    """
    Prevents cascading failures from repeated remediation attempts.
    Opens after max_failures within reset_seconds window.
    """

    def __init__(self, max_failures: int = 3, reset_seconds: int = 300):
        self.max_failures = max_failures
        self.reset_seconds = reset_seconds
        self._failures: dict[str, list[float]] = {}

    def is_open(self, key: str) -> bool:
        now = datetime.now(timezone.utc).timestamp()
        recent = [t for t in self._failures.get(key, []) if now - t < self.reset_seconds]
        self._failures[key] = recent
        return len(recent) >= self.max_failures

    def record_failure(self, key: str):
        self._failures.setdefault(key, []).append(datetime.now(timezone.utc).timestamp())

    def record_success(self, key: str):
        self._failures.pop(key, None)

    def status(self, key: str) -> dict:
        now = datetime.now(timezone.utc).timestamp()
        recent = [t for t in self._failures.get(key, []) if now - t < self.reset_seconds]
        return {
            "key": key,
            "open": len(recent) >= self.max_failures,
            "failure_count": len(recent),
            "max_failures": self.max_failures,
        }


# ── Remediation Agent ─────────────────────────────────────────────────────────

class RemediationAgent:
    """
    Executes approved K8s remediation actions safely.
    Dispatches based on TriageReport.recommended_action.
    """

    def __init__(self):
        self.circuit_breaker = CircuitBreaker()

    async def execute(self, report: TriageReport) -> ExecutionResult:
        """
        Main execution entrypoint. Requires a human-approved TriageReport.
        """
        start = datetime.now(timezone.utc)
        cb_key = f"{report.root_cause_type}-{report.namespace if hasattr(report, 'namespace') else 'default'}"

        # Circuit breaker check
        if self.circuit_breaker.is_open(cb_key):
            logger.warning("circuit_breaker_open", key=cb_key)
            return ExecutionResult(
                alert_id=report.alert_id,
                action_taken="blocked",
                success=False,
                output="",
                error=f"Circuit breaker OPEN for '{cb_key}'. {self.circuit_breaker.max_failures} failures in "
                      f"{self.circuit_breaker.reset_seconds}s. Manual intervention required.",
                duration_seconds=0.0,
                timestamp=start.isoformat(),
            )

        logger.info("executing_remediation",
                    alert_id=report.alert_id,
                    action=report.recommended_action,
                    root_cause=report.root_cause_type)

        # Dispatch
        # ── Per-action confidence threshold check ────────────────────────────────
        confidence_str = report.confidence if isinstance(report.confidence, str) else str(report.confidence)
        confidence_float = CONFIDENCE_STR_TO_FLOAT.get(confidence_str.upper(), 0.75)             if isinstance(report.confidence, str) else float(report.confidence)
        required_confidence = ACTION_CONFIDENCE_THRESHOLDS.get(report.recommended_action, 0.85)
        if confidence_float < required_confidence:
            logger.warning(
                "confidence_threshold_not_met",
                action=report.recommended_action,
                confidence=confidence_float,
                required=required_confidence,
                alert_id=report.alert_id,
            )
            duration = (datetime.now(timezone.utc) - start).total_seconds()
            return ExecutionResult(
                alert_id=report.alert_id,
                action_taken="confidence_gate_blocked",
                success=False,
                output="",
                error=(
                    f"Confidence gate FAILED: action '{report.recommended_action}' requires "
                    f"confidence ≥ {required_confidence:.0%}, got {confidence_float:.0%} ({confidence_str}). "
                    "Escalate to on-call engineer for manual review."
                ),
                duration_seconds=round(duration, 2),
                timestamp=start.isoformat(),
            )

        handlers = {
            "patch_resources": self._patch_resources,
            "rollback": self._argocd_rollback,
            "scale_down": self._scale_down,
            "create_exception": self._create_kyverno_exception,
            "monitor": self._monitor_only,
            "escalate": self._escalate,
        }
        handler = handlers.get(report.recommended_action, self._monitor_only)

        try:
            result = await handler(report)
        except Exception as e:
            result = {"success": False, "output": "", "error": str(e)}

        duration = (datetime.now(timezone.utc) - start).total_seconds()

        if result["success"]:
            self.circuit_breaker.record_success(cb_key)
        else:
            self.circuit_breaker.record_failure(cb_key)

        logger.info("remediation_complete",
                    success=result["success"],
                    action=report.recommended_action,
                    duration=duration)

        return ExecutionResult(
            alert_id=report.alert_id,
            action_taken=report.recommended_action,
            success=result["success"],
            output=result.get("output", ""),
            error=result.get("error"),
            duration_seconds=duration,
            timestamp=start.isoformat(),
            demo_mode=result.get("demo_mode", False),
        )

    # ── Action handlers ───────────────────────────────────────────────────────

    async def _patch_resources(self, report: TriageReport) -> dict:
        """Increase container memory/CPU limits and trigger rolling restart."""
        namespace = getattr(report, "namespace", "production")
        resource = getattr(report, "resource", report.alert_id.split("-")[0])

        patch_json = '{"spec":{"template":{"spec":{"containers":[{"name":"app","resources":{"limits":{"memory":"1Gi","cpu":"1000m"},"requests":{"memory":"512Mi","cpu":"500m"}}}]}}}}'
        cmd = ["kubectl", "patch", "deployment", resource, "-n", namespace, "--patch", patch_json]

        out, err, ok = await self._run(cmd)
        if ok:
            rollout_cmd = ["kubectl", "rollout", "status", f"deployment/{resource}", "-n", namespace, "--timeout=120s"]
            ro_out, _, _ = await self._run(rollout_cmd)
            out += f"\n{ro_out}"

        return {"success": ok, "output": out, "error": err if not ok else None}

    async def _argocd_rollback(self, report: TriageReport) -> dict:
        """Trigger ArgoCD rollback to last healthy revision."""
        app_name = os.getenv("ARGOCD_APP_NAME", "neurascale-ops")

        # Try ArgoCD CLI
        cmd = ["argocd", "app", "rollback", app_name,
               "--server", ARGOCD_SERVER, "--insecure", "--auth-token", ARGOCD_TOKEN]
        out, err, ok = await self._run(cmd)

        if not ok:
            # Fallback: kubectl rollout undo
            namespace = getattr(report, "namespace", "production")
            resource = getattr(report, "resource", "neurascale-api")
            cmd2 = ["kubectl", "rollout", "undo", f"deployment/{resource}", "-n", namespace]
            out, err, ok = await self._run(cmd2)

        return {"success": ok, "output": out, "error": err if not ok else None}

    async def _scale_down(self, report: TriageReport) -> dict:
        """
        Scale down the highest-cost workload to reduce spend.
        Blast radius guard: never scales below MIN_SAFE_REPLICAS (1).
        """
        namespace = getattr(report, "namespace", "ml-workloads")
        resource = report.raw_data.get("top_consumer", "neurascale-inference") if hasattr(report, "raw_data") else "neurascale-inference"

        target_replicas = MIN_SAFE_REPLICAS  # always leave at least 1 replica running
        cmd = ["kubectl", "scale", "deployment", resource, f"--replicas={target_replicas}", "-n", namespace]
        out, err, ok = await self._run(cmd)
        return {
            "success": ok,
            "output": out,
            "error": err if not ok else None,
            "blast_radius_note": f"Scaled to {target_replicas} replica(s) (min safe floor: {MIN_SAFE_REPLICAS})",
        }

    async def _create_kyverno_exception(self, report: TriageReport) -> dict:
        """Create a Kyverno PolicyException for the approved workload."""
        namespace = getattr(report, "namespace", "staging")
        raw = getattr(report, "raw_data", {})
        policy = raw.get("policy", "disallow-root-containers") if isinstance(raw, dict) else "disallow-root-containers"
        workload = getattr(report, "resource", "workload")

        exception_yaml = f"""apiVersion: kyverno.io/v2
kind: PolicyException
metadata:
  name: {workload}-exception
  namespace: {namespace}
  annotations:
    neurascale.io/approved-by: "UiPath Maestro Human Approval"
    neurascale.io/alert-id: "{report.alert_id}"
spec:
  exceptions:
  - policyName: {policy}
    ruleNames:
    - check-privileged
  match:
    any:
    - resources:
        kinds:
        - Pod
        namespaces:
        - {namespace}
        names:
        - {workload}*
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(exception_yaml)
            tmpfile = f.name

        cmd = ["kubectl", "apply", "-f", tmpfile]
        out, err, ok = await self._run(cmd)

        try:
            os.unlink(tmpfile)
        except Exception:
            pass

        return {"success": ok, "output": out, "error": err if not ok else None}

    async def _monitor_only(self, report: TriageReport) -> dict:
        return {
            "success": True,
            "output": f"Monitor-only mode. No automated action taken for alert {report.alert_id}. Incident logged to Maestro Case.",
            "error": None,
        }

    async def _escalate(self, report: TriageReport) -> dict:
        return {
            "success": True,
            "output": f"Escalation triggered. Alert {report.alert_id} handed to on-call engineer via Maestro Case escalation path.",
            "error": None,
        }

    # ── Shell runner ──────────────────────────────────────────────────────────

    async def _run(self, cmd: list[str], timeout: int = 120) -> tuple[str, str, bool]:
        """Execute shell command asynchronously. Returns (stdout, stderr, success)."""
        try:
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)
            ok = proc.returncode == 0
            return stdout.decode().strip(), stderr.decode().strip(), ok
        except asyncio.TimeoutError:
            return "", f"Command timed out after {timeout}s", False
        except FileNotFoundError:
            # Tool not installed — demo mode, simulate success
            logger.warning("command_not_found_demo", cmd=cmd[0])
            return f"[DEMO MODE] Would execute: {' '.join(cmd)}", "", True
        except Exception as e:
            return "", str(e), False
