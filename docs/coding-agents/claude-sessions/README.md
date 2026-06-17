# Claude Code Sessions — NeuroScale Ops

**Tool:** UiPath for Coding Agents (Claude Code integration)  
**Project:** NeuroScale Ops — UiPath AgentHack 2026 | Track 1: Maestro Case  
**Team:** afsod (Sodiq Jimoh, solo)

---

## Overview

NeuroScale Ops was built end-to-end using **Claude** as the primary coding agent via the Runable AI platform. Claude was used not just for boilerplate generation but for architectural decisions, debugging, and production-grade error handling patterns.

This folder documents the 3 primary coding sessions that produced the full system.

---

## Sessions Index

| Session | Date | Goal | Key Output |
|---------|------|------|-----------|
| [session-01.md](./session-01.md) | 2026-06-08 | Full system build from scratch | All Python agents, K8s manifests, runbooks, Maestro JSON, CI pipeline |
| [session-001-architecture.md](./session-001-architecture.md) | 2026-06-08 | Agent boundary design & UiPath mapping | Architecture decisions, 7-stage Maestro flow, component-to-stage mapping |
| [session-002-agents.md](./session-002-agents.md) | 2026-06-08 | Agent implementation & LLM swap | Gemini→Groq migration, DEMO_MODE pattern, graceful degradation strategy |

---

## What Claude Built

### In a Single Session (session-01.md)
Claude produced **~2,000 lines of production-grade code** covering:

- 6 Python agents (`detector`, `triage`, `remediation`, `cost_impact`, `notification`, `tools`)
- 7 UiPath files (Maestro case JSON, 3 API workflow YAMLs, 3 Apps form JSONs)
- 9 incident runbooks (OOMKill, CrashLoop, PolicyViolation, CostSpike, DeploymentFailure + variants)
- Full Kubernetes manifests (deployment, namespace, ArgoCD app, Kyverno policies, 3 scenario YAMLs)
- Streamlit dashboard, CLI entrypoint, Dockerfile, docker-compose
- GitHub Actions CI pipeline
- 17-test pytest suite (all passing)

### Architectural Decisions Made by Claude

1. **Dual-mode architecture** — `DEMO_MODE=true` bypasses all external dependencies so judges can run without a real K8s cluster or API keys
2. **7-stage Maestro Case** — Claude recommended adding dedicated Cost Impact and Post-Mortem stages on top of the obvious 5, which deepens the orchestration story
3. **llama-3.3-70b-versatile with rule-based fallback** — If Groq is unavailable, every agent degrades gracefully rather than crashing
4. **TriageReport carries Alert context** — Avoided prop-drilling by embedding `namespace` and `raw_data` directly into TriageReport dataclass
5. **OpenCost over custom cost calc** — Claude identified OpenCost as the CNCF-standard cost attribution tool, making the integration production-credible

### Bugs Found and Fixed by Claude

| Bug | Root Cause | Fix |
|-----|-----------|-----|
| `TriageReport` missing `namespace`/`raw_data` | Initial dataclass only captured output, not input context | Added fields with defaults, updated both triage paths |
| Dataclass field ordering TypeError | Default fields placed before non-default fields | Moved new fields to end of dataclass |
| `response_format` not set in Groq call | Ported from Gemini which didn't need it | Added `response_format={"type": "json_object"}` to eliminate markdown stripping |

---

## Why Claude Was Essential

This project was built under hackathon time pressure with an existing codebase from 3 source repositories:

| Source Repo | Pattern Extracted | Claude's Role |
|-------------|------------------|---------------|
| `neuro-autopilot` (Qwen Cloud) | Detector + demo patterns | Replaced Qwen LLM with Groq llama |
| `neuro-agents-v2` (Google Cloud) | Diagnostician agent | Replaced Gemini with Groq, added fallback |
| `neuro-ops-agent` (Splunk) | K8s ops abstraction | Replaced Splunk SDK with Prometheus/OpenCost |

Claude reviewed all 3 source repos, extracted the relevant patterns, resolved the conflicts between them, and produced a unified codebase in one session — something that would have taken multiple human engineering days.

---

## UiPath for Coding Agents Integration

NeuroScale Ops uses **UiPath for Coding Agents** in the following ways:

1. **Claude Code via Runable** — Used for the primary build session (documented here)
2. **Agent Builder IncidentNotifier** — UiPath Agent Builder config at `uipath/agent_builder/notification_agent.json` defines a notification agent that fires on Maestro stage transitions
3. **Coded Agent stages** — Stages 2 (Triage) and 5 (Remediation) in the Maestro Case are `type: coded_agent`, meaning UiPath invokes the Python agents directly

The combination of Claude Code (build-time) + UiPath Agent Builder (runtime) represents a full coding-agents lifecycle: AI-assisted development → AI-powered execution → human oversight via Maestro.

---

## Reproducibility

To reproduce the full build from these sessions:

```bash
git clone https://github.com/sodiq-code/neurascale-ops.git
cd neurascale-ops
pip install -r requirements.txt
DEMO_MODE=true python main.py
```

All 17 tests pass in demo mode without external dependencies:

```bash
python -m pytest tests/ -v
# 17 passed in <5s
```

---

*Sessions documented for UiPath for Coding Agents bonus scoring (+2 pts)*
