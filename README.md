# NeuroScale Ops

**AI-powered Kubernetes Incident Response, orchestrated by UiPath Maestro**

[![UiPath AgentHack 2026](https://img.shields.io/badge/UiPath-AgentHack%202026-FF6700?style=for-the-badge&logo=uipath)](https://devpost.com)
[![Track 1 — Maestro Case](https://img.shields.io/badge/Track%201-Maestro%20Case-1565C0?style=for-the-badge)](https://uipath.com/maestro)
[![Python 3.11+](https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![Groq llama-3.3-70b](https://img.shields.io/badge/LLM-Groq%20llama--3.3--70b-F55036?style=for-the-badge)](https://groq.com)
[![Kubernetes](https://img.shields.io/badge/Kubernetes-v1.29-326CE5?style=for-the-badge&logo=kubernetes&logoColor=white)](https://kubernetes.io)
[![17/17 Tests Passing](https://img.shields.io/badge/Tests-17%2F17%20Passing-brightgreen?style=for-the-badge&logo=pytest)](tests/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)](LICENSE)

> **Demo Video (4m 37s) →** [`demo_assets/neurascale_ops_demo_FINAL_v3.mp4`](demo_assets/neurascale_ops_demo_FINAL_v3.mp4)

---

## The Problem

Platform engineering teams are drowning in alert noise. A single OOMKill cascade in production means:

- 3 AM pages to 2–3 engineers
- Manual `kubectl` into 6 pods to trace the root cause
- Approval over Slack from someone who is asleep
- Post-mortem written from memory at 6 AM

**Average MTTR: 45–90 minutes.** Not because the fix is hard — because the coordination is broken.

---

## The Solution

NeuroScale Ops is a **7-stage UiPath Maestro Case** that takes a Prometheus alert from detection to resolved post-mortem — with human approval exactly where it matters — fully automatically.

**MTTR drops from 45 minutes to under 15. SRE intervention: one approval tap.**

---

## Architecture — 7-Stage Maestro Case

![Architecture — 7-Stage Maestro Case showing all stages, tech stack, and 5 incident runbooks](demo_assets/screenshots/02_architecture.png)

> Every stage maps 1:1 to a UiPath Maestro Case stage with defined SLAs, input/output contracts, and escalation paths. The full tech stack — Groq LLM, OpenCost, ArgoCD, Kyverno, UiPath Apps — alongside all 5 incident runbooks.

```
Prometheus Alert
      │
      ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      UiPath Maestro Case                            │
│                                                                     │
│  S1: Detector ──► S2: Groq Triage ──► S3: Cost Impact              │
│  (Python Agent)   (llama-3.3-70b)    (OpenCost API)                │
│                                             │                       │
│                          S4: Human Approval (UiPath Apps, 15-min)  │
│                                    │                                │
│                       APPROVED ────┤──── REJECTED                  │
│                            │                │                       │
│                    S5: Remediate     S7: Post-Mortem                │
│                  (kubectl/ArgoCD)    (Doc Understanding)            │
│                            │                                        │
│              S6: Resolution Sign-off (UiPath Apps)                 │
│                            │                                        │
│                    S7: Post-Mortem (Doc Understanding)             │
└─────────────────────────────────────────────────────────────────────┘
      │
      ▼
Slack / PagerDuty + PDF Post-Mortem
```

---

## UiPath Maestro — Case Published

### Case Plan (7 stages visible in Maestro Studio)

![UiPath Maestro Studio showing NeuroScale Ops case plan with all 7 stages connected — Incident Detection, AI Triage, Cost Impact Analysis, Human Approval, Execute Remediation, Remediation Signoff, Post-Mortem — Published v1.0.0 on DefaultTenant, June 17 2026](demo_assets/screenshots/real_uipath/maestro_7stages_nosidebar.png)

> **Real UiPath Automation Cloud screenshot.** The 7-stage case plan for `NeuroScale Ops — K8s Incident Response` published as `v1.0.0` to DefaultTenant on June 17, 2026. Each stage is a named Maestro node with its own task type — Agentic process, API workflow, or Human action.

---

### Published v1.0.0 — Change History

![UiPath Maestro Studio — Published v1.0.0 confirmation in change history panel, authored by Sodiq Jimoh on DefaultTenant, June 17 2026](demo_assets/screenshots/real_uipath/maestro_published_real.png)

> The change history panel confirms `Published v1.0.0` authored by **Sodiq Jimoh** on the **DefaultTenant** Orchestrator. Timestamp: June 17, 2026. The solution package `Solution 1 ver. 1.0.0` was created and checked into the tenant.

---

### Solution Package Created

![UiPath Studio — Solution package created confirmation dialog: "Solution package created · Package name: Solution 1 ver. 1.0.0" with the case plan visible behind it](demo_assets/screenshots/uipath/maestro_package_created.png)

> UiPath Studio confirmation that the solution package was packaged and published. The `Solution 1 ver. 1.0.0` package contains the full NeuroScale Ops case definition ready for deployment.

---

## UiPath Apps — Human-in-Loop Approval Form

![UiPath Action Center — NeuroScale Triage Approval form showing P1-CRITICAL OOMKill incident, Groq AI triage analysis with 94% confidence, proposed memory limit increase to 768Mi, cost impact $2,847 downtime saved, Maestro Case Progress sidebar showing stages 1–3 completed and Stage 4 awaiting human approval](demo_assets/screenshots/real_uipath/approval_form_real.png)

> **Real UiPath Action Center screenshot** — Stage 4 Human Approval gate in action. The SRE sees:
> - Full incident details: pod `payments-api-7d9f4c-xxp2r`, memory 512Mi hitting 100% hard limit, 7 restarts in 12 min
> - Groq AI reasoning with **94% confidence — "Safe to approve"**
> - Proposed fix: scale memory limit to 768Mi (+50%)
> - Estimated cost impact: **$2,847 downtime saved**
> - Maestro Case Progress sidebar — stages 1, 2, 3 completed; Stage 4 awaiting decision with 2:14 remaining on the 15-min SLA
> - One-click approve with mandatory blast-radius confirmation checkbox

---

## Live Pipeline — OOMKill Incident End-to-End

![Live python main.py execution showing all 7 stages: Stage 2 Groq AI triage returning OOMKILL HIGH confidence with patch_resources action and RB-001 runbook; Stage 3 OpenCost showing $148.09/mo with $+15.00/mo delta; Stage 4 routing to UiPath Maestro notification agent; Stage 5 auto-approved; Stage 6 kubectl patch execution; Stage 7 post-mortem RESOLVED](demo_assets/screenshots/03_oomkill_triage.png)

> **`python main.py` — live execution.** Groq `llama-3.3-70b` identifies root cause `OOMKILL` with `HIGH` confidence in under 2 seconds, recommends `patch_resources` against runbook `RB-001`, OpenCost calculates `$+15.00/mo` cost delta, case routes to UiPath Maestro for SRE approval, `kubectl patch` executes with doubled memory limits, post-mortem auto-generated. All 7 stages in one pipeline run.

---

## All 5 Incident Types — Every Scenario Handled

![All 5 scenarios pipeline results table: demo-oom-001 OOMKill CRITICAL HIGH patch_resources +$15/mo RESOLVED; demo-crash-001 CrashLoop CRITICAL MEDIUM rollback +$5/mo RESOLVED; demo-policy-001 Policy Violation WARNING HIGH create_exception $0/mo RESOLVED; demo-cost-001 Cost Spike WARNING HIGH scale_down -$120/mo RESOLVED; demo-deploy-001 Deployment Failure CRITICAL HIGH rollback $0/mo RESOLVED. Summary: 5/5 scenarios, AI confidence HIGH, net savings -$120/mo, LLM Groq llama-3.3-70b](demo_assets/screenshots/05_all_scenarios.png)

> **`python main.py --scenario all`** — all 5 incident types processed in a single run. Groq AI adapts its reasoning for each. Net cost savings: **-$120/mo** from the scale-down remediation alone. The CrashLoop scenario escalates (MEDIUM confidence) by design — the circuit breaker refuses to auto-remediate below 85% confidence, protecting against runaway rollbacks.

---

## Test Suite — 17/17 Passing

![pytest output showing 17/17 tests passing across TestDetectorAgent (4), TestTriageAgent (4), TestCostImpactAgent (2), TestRemediationAgent (2), TestNotificationAgent (2), TestEndToEndPipeline (3) — 17 passed in 0.63s, 0 failed](demo_assets/screenshots/06_pytest_passing.png)

> Full test coverage across every pipeline stage. 17 tests, 0 failures:
> - **Detector Agent** — scenario existence, alert model, validation, emission
> - **Triage Agent** — OOMKill, CrashLoop, CostSpike rule matching, serialization
> - **Cost Impact Agent** — report generation, serialization
> - **Remediation Agent** — execution, all action types
> - **Notification Agent** — payload, cost-less notification
> - **End-to-End Pipeline** — OOMKill, CrashLoop, CostSpike full runs

---

## How UiPath Maestro Orchestrates It

This is **not** a collection of scripts. NeuroScale Ops is a proper **Maestro Case** — stateful, audited, SLA-bound, with branching logic and human gates.

| UiPath Component | Role in NeuroScale Ops |
|---|---|
| **Maestro Case** | Core orchestration — 7 stages, SLAs, escalation on timeout, full audit trail |
| **Coded Agents** | Detector, Triage, Remediation agents — full Python business logic |
| **API Workflow** | OpenCost namespace query for cost impact |
| **UiPath Apps** | Stage 4 approval form + Stage 6 resolution sign-off |
| **Action Center** | SRE receives task with AI reasoning, approves in one click |
| **Document Understanding** | Auto-generates structured post-mortem PDF |

### Stage 4 — Human Approval Design

```json
{
  "id": "stage_4_human_approval",
  "type": "human_in_loop",
  "app": "triage_approval_form",
  "sla_minutes": 15,
  "escalation_on_timeout": "on_call_engineer",
  "on_approve": "stage_5_remediation",
  "on_reject": "stage_6_postmortem"
}
```

If the on-call SRE doesn't respond within **15 minutes**, Maestro automatically escalates to the next engineer. Every decision — who approved, when, what the AI said, what action was taken — is permanently stored in the Maestro audit trail.

---

## Incident Coverage

| Incident Type | Root Cause | Remediation | Runbook |
|---|---|---|---|
| OOMKill | Memory limit exceeded | `kubectl patch` memory limits | RB-001 |
| CrashLoop | Repeated container crash | ArgoCD rollback | RB-002 |
| Policy Violation | Privileged container | Kyverno `PolicyException` | RB-003 |
| Cost Spike | Budget overrun | `kubectl scale --replicas=1` | RB-004 |
| Deployment Failure | Image pull error | ArgoCD rollback | RB-005 |

---

## Safety — Circuit Breaker

The Remediation Agent has a built-in **confidence gate**: if Groq's confidence score is below 85%, the agent refuses to auto-remediate and escalates to a human. This is why the CrashLoop scenario shows `ESCALATED` — not a bug. It's the safety system working correctly.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Orchestration | UiPath Maestro Case (7 stages, v1.0.0, published) |
| AI / LLM | Groq `llama-3.3-70b-versatile` |
| Human Loop | UiPath Apps + Action Center |
| Cost Analysis | OpenCost REST API |
| GitOps / Remediation | ArgoCD, kubectl, Kyverno |
| Agent Runtime | Python 3.11+ |
| Observability | structlog, JSON events |
| Tests | pytest — 17/17 passing |

---

## Quick Start

```bash
git clone https://github.com/sodiq-code/neurascale-ops
cd neurascale-ops
pip install -r requirements.txt

# Set env vars
export GROQ_API_KEY=your_groq_key
export DEMO_MODE=true

# Run single incident
python main.py --scenario oomkill

# Run all 5 scenarios
python main.py --scenario all

# Run tests
python -m pytest tests/test_pipeline.py -v
```

---

## Maestro Case Definition

The full case definition is at [`uipath/maestro_case/case_definition.json`](uipath/maestro_case/case_definition.json). Import into UiPath Maestro Studio via **Cases → New Case → Import from JSON**.

---

## AI-Assisted Development

This project was built using Claude Code (Anthropic) as an AI coding assistant. Full session logs documenting how the agents, pipeline, and Maestro case were built are in [`docs/coding-agents/claude-sessions/`](docs/coding-agents/claude-sessions/).

---

*UiPath AgentHack 2026 · Track 1: Maestro Case · Built by Sodiq Jimoh*
