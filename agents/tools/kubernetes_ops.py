"""
NeuroScale Ops — Kubernetes Operations Toolkit
Provides ArgoCD sync, KServe management, kubectl wrappers, and OpenCost queries.

Used by:
  - RemediationAgent (Stage 5)
  - CostImpactAgent (Stage 4)
  - UiPath API Workflows (external trigger)
"""
from __future__ import annotations

import os
import subprocess
import requests
from typing import Optional
from rich.console import Console

console = Console()

ARGOCD_SERVER = os.getenv("ARGOCD_SERVER", "localhost:8080")
ARGOCD_TOKEN  = os.getenv("ARGOCD_TOKEN", "")
DEMO_MODE     = os.getenv("DEMO_MODE", "true").lower() == "true"
KUBECONFIG    = os.getenv("KUBECONFIG", os.path.expanduser("~/.kube/config"))
OPENCOST_URL  = os.getenv("OPENCOST_URL", "http://localhost:9090")


# ── kubectl wrapper ───────────────────────────────────────────────────────────

def _kubectl(cmd: list[str], timeout: int = 30) -> tuple[str, str, int]:
    """Run a kubectl command. Falls back to demo simulation if unavailable."""
    if DEMO_MODE:
        return _demo_kubectl(cmd)
    env = os.environ.copy()
    env["KUBECONFIG"] = KUBECONFIG
    try:
        result = subprocess.run(
            ["kubectl"] + cmd,
            capture_output=True, text=True, timeout=timeout, env=env
        )
        return result.stdout, result.stderr, result.returncode
    except FileNotFoundError:
        return _demo_kubectl(cmd)


def _demo_kubectl(cmd: list[str]) -> tuple[str, str, int]:
    """Simulated kubectl output for demo mode."""
    cmd_str = " ".join(cmd)
    if "get inferenceservice" in cmd_str or "get inferenceservices" in cmd_str:
        return (
            "NAME                       READY   URL                                      AGE\n"
            "neurascale-inference       True    http://neurascale-inference.production   2m\n"
            "neurascale-bert            True    http://neurascale-bert.ml-workloads      18h\n",
            "", 0
        )
    elif "rollout restart" in cmd_str:
        return "deployment.apps/neurascale-api restarted\n", "", 0
    elif "patch" in cmd_str:
        return "deployment.apps/neurascale-api patched\n", "", 0
    elif "get pods" in cmd_str:
        return (
            "NAME                                    READY   STATUS    RESTARTS   AGE\n"
            "neurascale-inference-predictor-0-abc   1/1     Running   0          2m\n"
            "neurascale-api-7d4f8b9c-xyz            1/1     Running   1          5h\n",
            "", 0
        )
    elif "rollout undo" in cmd_str:
        return "deployment.apps/neurascale-api rolled back\n", "", 0
    elif "scale" in cmd_str:
        return "deployment.apps/neurascale-inference scaled\n", "", 0
    elif "apply" in cmd_str:
        return "policyexception.kyverno.io/neurascale-exception created\n", "", 0
    return f"# [DEMO] kubectl {' '.join(cmd)}\n", "", 0


# ── ArgoCD Operations ─────────────────────────────────────────────────────────

def argocd_sync(app_name: str, hard_refresh: bool = True) -> dict:
    """
    Trigger an ArgoCD hard refresh + sync for the specified application.
    Primary self-healing action: Git is the source of truth.
    """
    console.print(f"[blue]ArgoCD sync:[/blue] triggering for '{app_name}'")

    if DEMO_MODE:
        return {
            "success": True,
            "app": app_name,
            "action": "sync_triggered",
            "message": f"[DEMO] ArgoCD sync triggered for '{app_name}'. Will be Synced/Healthy within 60s.",
        }

    if ARGOCD_TOKEN:
        result = _argocd_api_sync(app_name, hard_refresh)
        if result["success"]:
            return result

    # Fallback: annotation patch
    stdout, stderr, rc = _kubectl([
        "-n", "argocd", "patch", "application", app_name,
        "--type", "merge",
        "-p", '{"metadata":{"annotations":{"argocd.argoproj.io/refresh":"hard"}}}'
    ])
    if rc == 0:
        return {
            "success": True,
            "app": app_name,
            "action": "hard_refresh_triggered",
            "message": f"ArgoCD hard refresh triggered for '{app_name}'. Sync will complete within 60s.",
            "stdout": stdout.strip(),
        }
    return {"success": False, "app": app_name, "error": stderr.strip() or "kubectl patch failed"}


def _argocd_api_sync(app_name: str, hard_refresh: bool) -> dict:
    """Sync via ArgoCD REST API."""
    try:
        headers = {"Authorization": f"Bearer {ARGOCD_TOKEN}"}
        if hard_refresh:
            requests.get(
                f"https://{ARGOCD_SERVER}/api/v1/applications/{app_name}?refresh=hard",
                headers=headers, verify=False, timeout=10
            )
        resp = requests.post(
            f"https://{ARGOCD_SERVER}/api/v1/applications/{app_name}/sync",
            headers=headers,
            json={"prune": False, "dryRun": False},
            verify=False, timeout=15
        )
        return {
            "success": resp.status_code in (200, 201),
            "app": app_name,
            "action": "synced_via_api",
            "status_code": resp.status_code,
            "message": f"ArgoCD API sync triggered for '{app_name}'.",
        }
    except Exception as exc:
        return {"success": False, "error": str(exc)}


def get_argocd_status() -> list[dict]:
    """Get status of all ArgoCD applications."""
    stdout, stderr, rc = _kubectl([
        "-n", "argocd", "get", "applications",
        "-o", "custom-columns=NAME:.metadata.name,SYNC:.status.sync.status,HEALTH:.status.health.status"
    ])
    if rc != 0:
        return [{"error": stderr.strip()}]
    lines = stdout.strip().split("\n")
    results = []
    for line in lines[1:]:
        parts = line.split()
        if len(parts) >= 3:
            results.append({"name": parts[0], "sync": parts[1], "health": parts[2]})
    return results


# ── KServe Operations ─────────────────────────────────────────────────────────

def restart_inference_service(name: str, namespace: str = "default") -> dict:
    """Delete the predictor pod so Kubernetes recreates it from the ReplicaSet."""
    console.print(f"[blue]KServe restart:[/blue] '{name}' in namespace '{namespace}'")
    stdout, _, rc = _kubectl([
        "-n", namespace, "get", "pods",
        "-l", f"serving.kserve.io/inferenceservice={name}",
        "-o", "jsonpath={.items[0].metadata.name}"
    ])
    pod_name = stdout.strip() or f"{name}-predictor-00001-deployment-xxx"
    del_stdout, del_stderr, del_rc = _kubectl(["-n", namespace, "delete", "pod", pod_name, "--grace-period=0"])
    return {
        "success": DEMO_MODE or del_rc == 0,
        "action": "predictor_pod_restarted",
        "pod": pod_name,
        "inference_service": name,
        "namespace": namespace,
        "message": f"Predictor pod '{pod_name}' deleted. Kubernetes will recreate in ~30s.",
    }


def patch_inference_service_memory(name: str, namespace: str = "default", new_limit: str = "1Gi") -> dict:
    """Patch InferenceService memory limit to resolve OOMKilled errors."""
    patch_json = (
        f'{{"spec":{{"predictor":{{"model":{{"resources":{{"limits":{{"memory":"{new_limit}"}}}}}}}}}}}}'
    )
    stdout, stderr, rc = _kubectl(["-n", namespace, "patch", "inferenceservice", name, "--type", "merge", "-p", patch_json])
    return {
        "success": DEMO_MODE or rc == 0,
        "action": "memory_limit_patched",
        "inference_service": name,
        "new_memory_limit": new_limit,
        "message": f"Memory limit for '{name}' updated to {new_limit}. Pod will restart automatically.",
    }


def get_inference_services(namespace: str = "default") -> list[dict]:
    """List all InferenceServices and their readiness."""
    stdout, stderr, rc = _kubectl([
        "-n", namespace, "get", "inferenceservices",
        "-o", "custom-columns=NAME:.metadata.name,READY:.status.modelStatus.states.activeModelState,URL:.status.url"
    ])
    if rc != 0:
        return [{"error": stderr.strip()}]
    lines = stdout.strip().split("\n")
    results = []
    for line in lines[1:]:
        parts = line.split()
        if parts:
            results.append({
                "name": parts[0],
                "ready": parts[1] if len(parts) > 1 else "Unknown",
                "url": parts[2] if len(parts) > 2 else "None",
            })
    return results


# ── OpenCost Operations ───────────────────────────────────────────────────────

def get_opencost_by_namespace(window: str = "6h") -> list[dict]:
    """
    Query OpenCost for namespace-level cost attribution.
    FinOps intelligence layer — feeds into CostImpactAgent.
    """
    if DEMO_MODE:
        return [
            {"namespace": "production",   "totalCost": 1.2341, "cpuCost": 0.6102, "ramCost": 0.6239},
            {"namespace": "ml-workloads", "totalCost": 0.8341, "cpuCost": 0.4102, "ramCost": 0.4239},
            {"namespace": "staging",      "totalCost": 0.3203, "cpuCost": 0.1601, "ramCost": 0.1602},
            {"namespace": "default",      "totalCost": 0.0441, "cpuCost": 0.0220, "ramCost": 0.0221},
        ]

    try:
        resp = requests.get(
            f"{OPENCOST_URL}/model/allocation",
            params={"window": window, "aggregate": "namespace", "accumulate": "true"},
            timeout=10
        )
        data = resp.json()
        results = []
        for ns, info in (data.get("data") or [{}])[0].items():
            if ns == "__idle__":
                continue
            results.append({
                "namespace": ns,
                "totalCost": round(info.get("totalCost", 0), 4),
                "cpuCost": round(info.get("cpuCost", 0), 4),
                "ramCost": round(info.get("ramCost", 0), 4),
            })
        return sorted(results, key=lambda x: x["totalCost"], reverse=True)
    except Exception as exc:
        console.print(f"[yellow]OpenCost query warning:[/yellow] {exc}")
        return [{"error": str(exc)}]


def get_opencost_workload_breakdown(namespace: str, window: str = "24h") -> list[dict]:
    """Get per-workload cost breakdown within a namespace."""
    if DEMO_MODE:
        return [
            {"workload": "neurascale-inference", "totalCost": 0.6120, "cpuCost": 0.3060, "ramCost": 0.3060},
            {"workload": "neurascale-api",       "totalCost": 0.3241, "cpuCost": 0.1620, "ramCost": 0.1621},
            {"workload": "neurascale-bert",      "totalCost": 0.2980, "cpuCost": 0.1490, "ramCost": 0.1490},
        ]

    try:
        resp = requests.get(
            f"{OPENCOST_URL}/model/allocation",
            params={
                "window": window,
                "aggregate": "deployment",
                "accumulate": "true",
                "namespace": namespace,
            },
            timeout=10
        )
        data = resp.json()
        results = []
        for wl, info in (data.get("data") or [{}])[0].items():
            results.append({
                "workload": wl,
                "totalCost": round(info.get("totalCost", 0), 4),
                "cpuCost": round(info.get("cpuCost", 0), 4),
                "ramCost": round(info.get("ramCost", 0), 4),
            })
        return sorted(results, key=lambda x: x["totalCost"], reverse=True)
    except Exception as exc:
        return [{"error": str(exc)}]
