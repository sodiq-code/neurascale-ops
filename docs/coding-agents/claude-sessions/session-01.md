# Coding Agent Session 01 — NeuroScale Ops Build Log

**Agent:** Claude (Anthropic) via Runable Platform  
**Project:** NeuroScale Ops — UiPath AgentHack 2026  
**Track:** Track 1 — UiPath Maestro Case  
**Team:** afsod (Sodiq Jimoh, solo)  
**Session Date:** 2026-06-08  
**Submission Deadline:** 2026-06-30  

---

## Session Objective

Build a production-grade UiPath Maestro-orchestrated Kubernetes incident response system from scratch in a single session, incorporating code and patterns from 3 existing NeuroScale projects.

---

## What Was Built

### System Architecture

```
[Prometheus Alert]
       │
       ▼
[IncidentDetector]  →  generates Alert dataclass
       │
       ▼
[UiPath Maestro Case — 7 Stages]
  Stage 1: Detection      — webhook ingest
  Stage 2: AI Triage      — llama-3.3-70b-versatile root cause analysis
  Stage 3: Cost Impact    — OpenCost namespace attribution
  Stage 4: Human Approval — UiPath Apps form (HITL gate)
  Stage 5: Remediation    — ArgoCD sync + kubectl patching
  Stage 6: Sign-Off       — second human approval
  Stage 7: Post-Mortem    — Jira ticket + runbook update
       │
       ▼
[Slack / Teams / PagerDuty notifications]
```

### Files Created by Coding Agent

#### Core Agents (Python)
- `agents/detector/detector.py` — Alert dataclass + IncidentDetector with 5 scenario types
- `agents/triage/triage_agent.py` — llama-3.3-70b-versatile triage + rule-based fallback, TriageReport dataclass
- `agents/remediation/remediation_agent.py` — ArgoCD sync, kubectl patching, demo dry-run mode
- `agents/tools/kubernetes_ops.py` — KubernetesOps abstraction layer (real + mock)
- `agents/cost_impact/cost_agent.py` — OpenCost API integration + cost attribution
- `agents/notification/notification_agent.py` — Slack/Teams webhook notifications

#### UiPath Integration
- `uipath/maestro_case/case_definition.json` — 7-stage Maestro Case definition
- `uipath/api_workflows/prometheus_webhook.yaml` — Alertmanager webhook receiver
- `uipath/api_workflows/argocd_trigger.yaml` — ArgoCD REST API workflow
- `uipath/api_workflows/opencost_query.yaml` — OpenCost query workflow
- `uipath/agent_builder/notification_agent.json` — UiPath Agent Builder config
- `uipath/apps/triage_approval_form.json` — Stage 3 HITL approval form
- `uipath/apps/remediation_approval_form.json` — Stage 4 execution gate form
- `uipath/apps/signoff_form.json` — Stage 6 post-remediation sign-off

#### Kubernetes
- `k8s/base/namespace.yaml` — neurascale-ops namespace
- `k8s/base/neurascale-ops-deployment.yaml` — K8s Deployment + Service + HPA
- `k8s/base/argocd-application.yaml` — ArgoCD Application manifest
- `k8s/policies/` — 3 Kyverno admission policies
- `k8s/scenarios/` — 3 live incident scenario manifests

#### Supporting Files
- `runbooks/` — 9 JSON incident runbooks (OOMKill, CrashLoop, PolicyViolation, etc.)
- `dashboard/app.py` — Streamlit real-time incident dashboard
- `main.py` — CLI entry point with `--demo` and `--scenario` flags
- `requirements.txt` — Python dependencies
- `.env.example` — Environment variable template
- `Dockerfile` — Production container image
- `docker-compose.yml` — Full local stack (app + Prometheus + Grafana)
- `scripts/demo_run.sh` — 5-scenario demo script
- `scripts/trigger_test.sh` — Webhook trigger simulation
- `tests/test_pipeline.py` — Full integration test suite
- `docs/SETUP.md` — Setup guide (demo + real K8s + UiPath)
- `.github/workflows/ci.yml` — CI pipeline (lint, test, Docker build, K8s validate)

---

## Key Design Decisions Made During Session

### 1. Dual-Mode Architecture (DEMO_MODE / Real Mode)
**Decision:** All agents support `DEMO_MODE=true` (env var) which bypasses real K8s API calls and Groq calls.  
**Reason:** Hackathon judges need to run the system without a real cluster. Demos must be zero-friction.  
**Implementation:** Every agent checks `os.environ.get("DEMO_MODE", "false").lower() == "true"` at the top of each method that would make external calls.

### 2. llama-3.3-70b-versatile with Rule-Based Fallback
**Decision:** Use Groq llama-3.3-70b-versatile for AI triage, but fall back to rule-based logic when no API key is present.  
**Reason:** Hackathon judges may not have Groq keys. The system must always produce output.  
**Implementation:** `TriageAgent._gpt_triage()` catches all exceptions and calls `_rule_based_triage()` as fallback.

### 3. TriageReport Carries Alert Context
**Decision:** Added `namespace: str` and `raw_data: dict` fields to `TriageReport` dataclass.  
**Reason:** `RemediationAgent` needs namespace for kubectl commands, and raw_data for debugging. Passing both Alert and TriageReport everywhere is verbose — better to embed context in the report.  
**Bug discovered:** Initial `TriageReport` was missing these fields. Fixed mid-session.

### 4. 7-Stage Maestro Case (not 5)
**Decision:** Added dedicated Cost Impact stage (Stage 3) and Post-Mortem stage (Stage 7) on top of the obvious 5.  
**Reason:** Cost Impact is a first-class metric for FinOps-aware orgs. Post-Mortem closes the loop and enables runbook improvement. Both stages demonstrate Maestro's orchestration depth to judges.

### 5. OpenCost Integration over Custom Cost Calculation
**Decision:** Query OpenCost API for real cost data rather than calculating from resource metrics.  
**Reason:** OpenCost is the CNCF standard for K8s cost attribution. Using it signals production-readiness and domain expertise.

---

## Bugs Encountered and Fixed

### Bug 1: TriageReport Missing namespace/raw_data
- **Symptom:** `remediation_agent.py` referenced `report.namespace` and `report.raw_data` but `TriageReport` dataclass had neither field.
- **Root cause:** Initial dataclass design only captured triage output, not input context.
- **Fix:** Added `namespace: str = "production"` and `raw_data: dict = None` with `__post_init__` guard to TriageReport. Updated both `_gpt_triage()` and `_rule_based_triage()` to pass `namespace=alert.namespace, raw_data=alert.raw_data`.

### Bug 2: Dataclass Field Ordering
- **Symptom:** Python raises `TypeError: non-default argument follows default argument` for dataclasses.
- **Root cause:** Added `namespace` and `raw_data` (with defaults) — needed to ensure all fields with defaults come after fields without defaults.
- **Fix:** Placed both new fields at the end of the dataclass definition.

---

## Source Code Provenance

This project was bootstrapped from 3 existing NeuroScale projects:

| Source | Files Reused | Adaptation |
|--------|-------------|------------|
| NeuroScale Agents (Google Cloud) | `k8s/policies/`, runbook structure | Ported Kyverno policies to new namespace |
| NeuroScale Ops Agent (Splunk) | Agent architecture patterns | Replaced Splunk SDK with Prometheus/OpenCost |
| NeuroScale Autopilot (Qwen Cloud) | Scenario YAMLs, demo patterns | Replaced Qwen LLM with llama-3.3-70b-versatile |

All source files were reviewed at `/home/user/neurascale-source/` and key patterns extracted.

---

## What UiPath Maestro Adds That Custom Code Cannot

1. **Visual Case Flow** — Non-engineers can see the 7-stage workflow without reading code
2. **HITL Forms** — UiPath Apps provides enterprise-grade approval UIs without writing frontend
3. **Audit Trail** — Every stage transition is logged with user, timestamp, decision — compliance-ready
4. **SLA Management** — Maestro auto-escalates if humans don't respond within configured SLA minutes
5. **Integration Hub** — Native Jira, ServiceNow, Slack connectors without custom webhook code
6. **Role-Based Assignment** — Stage 4 assigns to `platform-engineer` role, Stage 6 to `sre-lead` role automatically

---

## Hackathon Positioning

**Primary Track:** Track 1 — UiPath Maestro Case  
**Award Targets:**
1. Best Maestro Case (deep 7-stage orchestration + HITL forms)
2. Best Use of Human-in-the-Loop (dual approval gates with audit trail)
3. Most Innovative Use Case (FinOps + DevOps convergence, OpenCost integration)

**Differentiators vs competing submissions:**
- Real Kubernetes workload — not a toy demo
- OpenCost integration shows FinOps awareness (rare in K8s incident response)
- Kyverno policy enforcement loop (detect policy violation → create exception → re-validate)
- Dual-mode (DEMO/Real) means judges can actually run it
- 9 runbooks covering the full incident taxonomy

---

## Next Steps (Post-Session)

- [ ] Record 3-5 minute demo video showing full pipeline run
- [ ] Deploy to live Kind cluster for video demo
- [ ] Submit via Devpost before 2026-06-30
- [ ] Add Prometheus Alertmanager config for live webhook testing
- [ ] Consider adding Grafana dashboard JSON for observability story
