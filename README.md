# 🛡️ NeuroScale Ops

**AI-powered Kubernetes Incident Response, orchestrated by UiPath Maestro**

[![UiPath AgentHack 2026](https://img.shields.io/badge/UiPath-AgentHack%202026-FF6700?style=for-the-badge&logo=uipath)](https://devpost.com)
[![Track 1 — Maestro Case](https://img.shields.io/badge/Track%201-Maestro%20Case-1565C0?style=for-the-badge)](https://uipath.com/maestro)
[![Python 3.11+](https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![GPT-4o-mini](https://img.shields.io/badge/LLM-GPT--4o--mini-412991?style=for-the-badge&logo=openai)](https://openai.com)
[![Kubernetes](https://img.shields.io/badge/Kubernetes-v1.29-326CE5?style=for-the-badge&logo=kubernetes&logoColor=white)](https://kubernetes.io)
[![License: MIT](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)](LICENSE)

---

## The Problem

Modern Kubernetes platforms generate hundreds of alerts daily. Engineers spend **3–8 hours per week** on manual incident triage, copy-pasting alert context into Slack, digging through runbooks, running kubectl commands, and writing post-mortems. During P1 incidents, every minute of response lag costs real money.

## The Solution

NeuroScale Ops is a **7-stage autonomous incident response pipeline** that takes alerts from Prometheus to resolved post-mortem — with human approval exactly where it matters — orchestrated end-to-end by **UiPath Maestro**.

```
Prometheus Alert → Maestro Case Created
        │
   ┌────▼────┐    ┌────────┐    ┌──────────┐    ┌───────────┐
   │ Detect  │───▶│ Triage │───▶│ Approval │───▶│ Remediate │
   │ (coded) │    │  GPT   │    │ UiPath   │    │  ArgoCD   │
   └─────────┘    │ 4o-mini│    │  Apps    │    │ + kubectl │
                  └────────┘    └──────────┘    └─────┬─────┘
                                                       │
                  ┌───────────┐    ┌────────┐    ┌────▼──────┐
                  │ Post-Mortem│◀───│Sign-off│◀───│Cost Impact│
                  │ Doc.Under.│    │  App   │    │ OpenCost  │
                  └───────────┘    └────────┘    └───────────┘
```

**Mean time to remediation: under 15 minutes, fully audited, zero alert fatigue.**

---

## Architecture

### 7-Stage Maestro Case Pipeline

| Stage | Name | Component | Description |
|-------|------|-----------|-------------|
| S1 | **Detect** | Coded Agent (Python) | Normalize Prometheus webhook → Incident object. Circuit breaker deduplication. |
| S2 | **Triage** | Coded Agent (Python) | GPT-4o-mini root cause analysis + runbook RAG. Structured JSON output. |
| S3 | **Approval** | UiPath Apps | Human-in-loop: on-call engineer reviews AI plan before execution. |
| S4 | **Remediate** | Coded Agent (Python) | ArgoCD sync, kubectl restart, resource patching — all approved actions executed. |
| S5 | **Cost Impact** | API Workflow + Coded Agent | OpenCost query: current monthly spend + remediation delta. |
| S6 | **Notify & Sign-off** | Agent Builder + UiPath Apps | Rich Slack/PagerDuty notifications + human sign-off form. |
| S7 | **Post-Mortem** | Document Understanding | Structured PDF: timeline, root cause, cost impact, action items. |

### UiPath Components Used

| Component | How Used |
|-----------|----------|
| **Maestro Case** | Core orchestration — 7-stage case definition, SLAs, escalation paths |
| **Coded Agents (Python SDK)** | Detector, Triage, Remediation, Cost Impact agents |
| **API Workflows** | Prometheus webhook receiver, ArgoCD trigger, OpenCost query |
| **Agent Builder** | Low-code Slack/PagerDuty notification agent |
| **UiPath Apps** | 3 human-in-loop forms: triage approval, remediation review, sign-off |
| **Document Understanding** | Post-mortem PDF generation |
| **For Coding Agents (Claude)** | Architecture design, agent implementation sessions (see `docs/coding-agents/`) |

### Alert Types Handled

| Alert | Severity | Automated Action |
|-------|----------|-----------------|
| CPU Throttling | CRITICAL | Patch InferenceService resource limits + ArgoCD sync |
| OOMKilled | CRITICAL | Increase memory limit + restart predictor pod |
| CrashLoopBackOff | HIGH | kubectl rollout restart + ArgoCD sync |
| ArgoCD OutOfSync | HIGH | Hard refresh + sync to Git HEAD |
| KServe High Latency | HIGH | Scale deployment replicas |
| Kyverno Policy Denial | MEDIUM | Alert only + manual review |
| Node NotReady | HIGH | Alert + PagerDuty escalation |

---

## Repository Structure

```
neurascale-ops/
├── agents/
│   ├── detector/          # Stage 1: Prometheus alert normalization
│   │   └── detector.py
│   ├── triage/            # Stage 2: GPT-4o-mini root cause analysis
│   │   └── triage_agent.py
│   ├── remediation/       # Stage 4: ArgoCD + kubectl execution
│   │   └── remediation_agent.py
│   ├── cost_impact/       # Stage 5: OpenCost financial analysis
│   │   └── cost_agent.py
│   ├── notification/      # Stage 6: Slack + PagerDuty bridge
│   │   └── notification_agent.py
│   └── tools/
│       └── kubernetes_ops.py   # Shared kubectl/ArgoCD/KServe utilities
│
├── uipath/
│   ├── maestro_case/      # 7-stage Maestro Case definition
│   ├── api_workflows/     # Prometheus, ArgoCD, OpenCost API schemas
│   ├── agent_builder/     # Notification Agent Builder config
│   └── apps/              # 3 UiPath Apps human approval forms
│
├── k8s/
│   ├── base/              # Namespace, InferenceServices, ArgoCD app, Prometheus rules
│   ├── policies/          # Kyverno policies (resource limits, labels)
│   └── scenarios/         # Demo scenarios for judges
│
├── runbooks/              # JSON runbooks (CPU throttling, OOM, ArgoCD, crash loop)
├── dashboard/             # Streamlit incident command center
│   └── app.py
├── scripts/
│   ├── demo_run.sh        # Full pipeline demo (no cluster required)
│   └── trigger_test.sh    # Send simulated alerts to webhook
├── docs/
│   ├── SETUP.md
│   └── coding-agents/
│       └── claude-sessions/  # Documented Claude Code sessions (+2 pts bonus)
├── .env.example
├── requirements.txt
├── Dockerfile
└── docker-compose.yml
```

---

## Quick Start

### Demo Mode (No cluster, no API keys required)

```bash
# Clone and run
git clone https://github.com/sodiq-code/neurascale-ops
cd neurascale-ops
cp .env.example .env

# Install deps
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# Run full pipeline
bash scripts/demo_run.sh

# Launch dashboard
streamlit run dashboard/app.py
# → http://localhost:8501
```

### With OpenAI API Key (recommended for judges)

```bash
# Edit .env
echo "OPENAI_API_KEY=sk-your-key" >> .env
echo "DEMO_MODE=true" >> .env  # still uses simulated K8s, real GPT-4o-mini triage

bash scripts/demo_run.sh
```

### Docker

```bash
docker-compose up dashboard
# → http://localhost:8501
```

### Simulate Alerts

```bash
# Trigger CPU throttling scenario
bash scripts/trigger_test.sh cpu

# Trigger all demo scenarios
bash scripts/trigger_test.sh all
```

---

## How Human Approval Works

NeuroScale Ops keeps humans in control for **CRITICAL and HIGH severity incidents**:

1. **Triage Agent** generates remediation plan (GPT-4o-mini, < 5 seconds)
2. **Slack notification** sent to `#incidents` with plan summary
3. **UiPath Apps form** opens automatically — shows:
   - AI root cause + confidence level
   - All proposed actions (step-by-step)
   - Monthly cost impact
   - Matched runbook references
4. **Engineer approves** (or rejects / escalates) — plan executes immediately
5. **Audit trail** preserved: who approved, when, what notes

LOW/MEDIUM incidents can be configured to auto-approve (no human delay).

---

## Cost Intelligence

Every incident includes a financial impact report powered by **OpenCost**:

```
Current monthly cost:     $51.20  (production namespace)
Remediation delta:        +$12.50/mo (memory limit increase)
Downtime cost estimate:   $2.56   (2h P1 at 5% revenue impact)
Projected after fix:      $63.70/mo
```

This lets engineers make informed decisions: is patching now cheaper than investigating later?

---

## Demo Scenarios

| Scenario | Alert | Expected Action |
|----------|-------|----------------|
| CPU Throttling | `CPUThrottlingHigh` (CRITICAL) | Patch CPU limits → ArgoCD sync |
| OOMKilled | `KubeContainerOOMKilled` (CRITICAL) | Patch memory → restart pod |
| ArgoCD Drift | `ArgoCDApplicationOutOfSync` (HIGH) | Hard refresh + sync |
| Crash Loop | `KubePodCrashLooping` (HIGH) | Rollout restart → ArgoCD sync |

---

## Built With

- **Python 3.11** — Agent runtime
- **OpenAI GPT-4o-mini** — Root cause analysis (structured JSON mode)
- **UiPath Maestro** — Case orchestration
- **UiPath Coded Agents (Python SDK)** — Agent execution
- **UiPath Apps** — Human approval forms
- **UiPath Agent Builder** — Low-code notification agent
- **UiPath Document Understanding** — Post-mortem generation
- **ArgoCD** — GitOps remediation
- **KServe** — ML inference service management
- **Kyverno** — Policy enforcement
- **OpenCost** — Cost allocation
- **Prometheus** — Alert detection
- **Streamlit** — Live dashboard

---

## Team

**Solo: Sodiq Jimoh** — DevOps/Cloud Engineer, Platform Engineering  
GitHub: [@sodiq-code](https://github.com/sodiq-code) | Devpost: [@sodiqjimoh80](https://devpost.com/sodiqjimoh80)

---

## License

MIT License — see [LICENSE](LICENSE)

---

*Built for UiPath AgentHack 2026 · Track 1: Maestro Case · Submitted June 2026*
