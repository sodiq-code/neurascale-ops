# Demo Video Script — NeuroScale Ops
## UiPath AgentHack 2026 | Track 1: Maestro Case
**Target length: 3–5 minutes**

---

## Setup Before Recording

```bash
# Terminal ready — dark theme, font size 16+, 120 columns wide
cd /home/user/neurascale-ops
source .env  # or ensure GROQ_API_KEY is set
clear
```

Open two windows side by side if possible:
- Left: Terminal (for `python main.py` and `pytest`)
- Right: VS Code open to `uipath/maestro_case/case_definition.json`

---

## SECTION 1 — Hook (0:00–0:30)

**[SHOW: terminal, blank, cursor blinking]**

> "Every Kubernetes platform team faces the same nightmare: 3 AM, your phone blows up with a hundred alerts. An OOMKill cascade in production. Your ML inference service is down. The runbook is 40 pages. You have to manually kubectl into 6 pods, check logs, find the cause, figure out if you should patch or rollback, get approval from someone who's asleep, run the fix, and then write a post-mortem at 6 AM.

> What if that entire workflow — detection, AI analysis, cost impact, human approval, remediation, post-mortem — happened automatically in under 15 minutes, with full audit trail, orchestrated by UiPath Maestro?

> That's NeuroScale Ops."

---

## SECTION 2 — Architecture Overview (0:30–1:00)

**[SHOW: screenshot `04_architecture_stack.png` or VS Code with `case_definition.json` open]**

> "NeuroScale Ops is a 7-stage UiPath Maestro Case.

> Stage 1: A Python Coded Agent detects the incident.
> Stage 2: Groq's llama-3.3-70b performs root cause analysis — real AI, not just pattern matching — and returns structured JSON with confidence score.
> Stage 3: An OpenCost API Workflow calculates the exact dollar cost of both the incident and the proposed fix.
> Stage 4: A UiPath Apps form surfaces all of this to the on-call SRE. One click to approve.
> Stage 5: Remediation Agent executes — ArgoCD rollback, kubectl patch, scale-down, Kyverno exception — the right fix for the right incident.
> Stage 6: Another UiPath Apps sign-off to confirm resolution.
> Stage 7: Document Understanding generates a structured post-mortem PDF automatically.

> Five incident types. One Maestro Case. Zero manual kubectl."

---

## SECTION 3 — Live Pipeline Run (1:00–2:30)

**[SHOW: terminal full screen]**

Type and run:
```bash
python main.py
```

**[AS IT RUNS, narrate each section of output]**

**When alert detection prints:**
> "Stage 1 — the Detector Agent has identified an OOMKill in the production namespace. Pod `ml-inference-pod-7d9f8b`. Memory limit exceeded. This would normally page 3 engineers at 3 AM."

**When Groq triage prints:**
> "Stage 2 — watch this. Groq llama-3.3-70b is analyzing the alert right now. [PAUSE] And there's the structured output: root cause OOMKILL, confidence HIGH, recommended action `patch_resources`, runbook RB-001. This took 1.2 seconds. An SRE reading the same alert would take 10 minutes just to confirm the cause."

**When cost impact prints:**
> "Stage 3 — OpenCost query complete. The production namespace is spending $148 per month. The memory patch will add $15 per month — a 10% increase. That context is now part of the approval screen."

**When human approval block prints:**
> "Stage 4 — in a real deployment, this is where a UiPath Apps form pops up on the SRE's phone. They see the AI's reasoning, the cost impact, the runbook match — everything in one screen. We're simulating the approval here."

**When remediation prints:**
> "Stage 5 — approved. Remediation Agent executing `kubectl patch deployment` with the new memory limits. In demo mode. In production, this hits the real cluster."

**When all 5 scenarios finish:**
> "And there it is. Five different incident types — OOMKill, CrashLoop, Policy Violation, Cost Spike, Deployment Failure — all handled. Every single one resolved."

---

## SECTION 4 — Test Results (2:30–2:50)

**[SHOW: terminal]**

```bash
python -m pytest tests/test_pipeline.py -v
```

> "17 tests, 17 passing. Every stage tested: detection, triage, cost calculation, remediation actions, circuit breaker deduplication."

---

## SECTION 5 — Maestro Case Definition (2:50–3:30)

**[SWITCH to VS Code, open `uipath/maestro_case/case_definition.json`]**

> "This is the Maestro Case definition. When UiPath platform access arrives — I've already submitted the Labs access form — this JSON imports directly into Maestro. Seven stages defined with SLAs, escalation paths, human-in-loop gates, and input/output contracts between every stage."

**[SCROLL through the JSON, pause on Stage 4 human_in_loop section]**

> "Stage 4 — human_in_loop type. 15-minute SLA. If the on-call doesn't respond, Maestro automatically escalates to the next engineer. That's production-grade incident management, not a chatbot."

---

## SECTION 6 — Screenshots / Evidence (3:30–4:00)

**[SHOW: demo_assets/screenshots/ — open 02_oomkill_pipeline_run.png and 03_all_scenarios_results.png]**

> "Here's the actual pipeline output — all five scenarios, real Groq responses, real timestamps. The all-scenarios table shows every incident type with confidence scores, cost deltas, and resolution status."

---

## SECTION 7 — Close (4:00–4:20)

> "NeuroScale Ops takes the most painful part of platform engineering — 3 AM incidents, manual triage, approval over Slack — and turns it into a formal, audited, AI-accelerated workflow.

> MTTR drops from 45 minutes to under 15. SRE intervention drops from 60 minutes to 2 minutes — just the approval click.

> Built on UiPath Maestro because incident response isn't a script. It's a case. With stages, SLAs, human gates, and an audit trail your security team can actually use.

> This is NeuroScale Ops. Thank you."

---

## Recording Tips

- Use OBS or Loom — keep resolution 1920×1080
- Terminal: dark theme (Dracula or One Dark), font size 16, 120-col width
- Speak slowly when Groq output prints — let it build suspense
- Don't skip the `pytest` run — judges need to see tests passing
- Total should be 3:30–4:30 max

## Files to Show On Screen
1. `python main.py` output (full terminal)
2. `python -m pytest tests/test_pipeline.py -v` output
3. `uipath/maestro_case/case_definition.json` in VS Code
4. `demo_assets/screenshots/03_all_scenarios_results.png`
5. `demo_assets/screenshots/04_architecture_stack.png`
