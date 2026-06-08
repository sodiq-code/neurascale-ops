# Claude Code Session 001 — Architecture & Agent Design

**Date:** 2026-06-08  
**Tool:** UiPath for Coding Agents — Claude Code  
**Session Goal:** Design the overall NeuroScale Ops architecture and agent boundaries

---

## Prompt Used

```
Design a UiPath Maestro-orchestrated Kubernetes incident response system.
The system must:
1. Receive Prometheus Alertmanager webhooks
2. Use AI (llama-3.3-70b-versatile) for root cause analysis
3. Route through human approval for CRITICAL/HIGH alerts
4. Execute ArgoCD sync + kubectl remediation
5. Calculate OpenCost financial impact
6. Generate post-mortem documentation

Define the agent boundaries, data flow, and UiPath component mapping.
```

## Claude's Architecture Output

### Agent Boundary Decision

After analysis, Claude recommended 5 distinct agents + 1 notification bridge:

1. **DetectorAgent** — Pure normalization, no AI needed. Circuit breaker pattern for dedup.
2. **TriageAgent** — llama-3.3-70b-versatile with structured JSON output. Must be stateless.
3. **RemediationAgent** — Pure executor. Never makes decisions — only executes approved plans.
4. **CostImpactAgent** — OpenCost query wrapper. Separate concern from triage.
5. **NotificationAgent** — Thin bridge between coded agents and Agent Builder.

### Key Architecture Decision: Why llama-3.3-70b-versatile over GPT-4o?

Claude's reasoning:
> "For structured JSON output with well-defined schemas (root cause type + actions), 
> llama-3.3-70b-versatile at temperature=0.1 matches llama-3.3-70b-versatile quality at 15x lower cost. 
> The response_format=json_object mode eliminates hallucination risk on the schema. 
> Use llama-3.3-70b-versatile for this task; reserve llama-3.3-70b-versatile for open-ended reasoning if needed."

### Maestro Stage Mapping

Claude mapped each agent to a Maestro Case stage:
- S1 (Detect) → Coded Agent (Python SDK)
- S2 (Triage) → Coded Agent (Python SDK) with groq
- S3 (Approve) → UiPath Apps human task
- S4 (Remediate) → Coded Agent (Python SDK)
- S5 (Cost) → API Workflow → Coded Agent
- S6 (Notify) → Agent Builder (low-code Slack) + Coded Agent (PagerDuty)
- S7 (Post-Mortem) → Document Understanding

### Data Flow Diagram (ASCII)

```
Prometheus ──webhook──→ API Workflow ──→ Maestro Case Created
                                              │
                                         S1: Detector
                                         (normalize alert)
                                              │
                                         S2: Triage
                                         (llama-3.3-70b-versatile)
                                         (runbook RAG)
                                              │
                                    ┌─────────┴──────────┐
                                    │                    │
                               CRITICAL/HIGH           LOW/MEDIUM
                               (needs approval)      (auto-approve)
                                    │                    │
                               S3: UiPath Apps          │
                               Approval Form            │
                                    │                    │
                                    └────────┬───────────┘
                                             │
                                        S4: Remediation
                                        (ArgoCD + kubectl)
                                             │
                                        S5: OpenCost
                                        (cost delta)
                                             │
                                        S6: Notify
                                        (Slack + PagerDuty)
                                        (Sign-off form)
                                             │
                                        S7: Post-Mortem
                                        (Doc Understanding)
                                             │
                                        Case Closed ✅
```

## Files Generated in This Session
- `uipath/maestro_case/case_definition.json` — full 7-stage case definition
- `agents/detector/detector.py` — normalized alert processing
- `agents/triage/triage_agent.py` — llama-3.3-70b-versatile triage
- Initial architecture docs

## Prompt Iterations
- v1: Basic design → too simple, missed cost impact stage
- v2: Added cost agent → missed sign-off vs. post-mortem distinction  
- v3: Final 7-stage design → implemented as-is

---
*Session logged for UiPath for Coding Agents bonus scoring (+2 pts)*
