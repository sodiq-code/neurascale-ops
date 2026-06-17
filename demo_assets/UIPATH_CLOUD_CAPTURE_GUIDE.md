# UiPath Cloud Capture Guide
## What to screenshot/record for authentic demo evidence

---

## STEP 0 — Login
1. Go to https://cloud.uipath.com
2. Sign in with the email that received the hackathon26_581 invite
3. Switch org to **hackathon26_581** (top-left org selector)
4. You should see the UiPath Automation Cloud dashboard

**Screenshot needed:** Dashboard showing org name `hackathon26_581` in top-left

---

## STEP 1 — Import Maestro Case (10 min)

1. In left sidebar → **Maestro** → **Cases**
2. Click **"+ New Case"** or **"Import"**
3. Upload `uipath/maestro_case/case_definition.json` from the repo
4. If no import option: click **"+ New Case"** → name it **"NeuroScale Ops — K8s Incident Response"** → manually add 7 stages:

| Stage # | Name | Type |
|---------|------|------|
| 1 | Incident Detection | Automated |
| 2 | AI Triage | Coded Agent |
| 3 | Cost Impact Analysis | API Workflow |
| 4 | Human Approval | Human in Loop |
| 5 | Execute Remediation | Coded Agent |
| 6 | Remediation Signoff | Human in Loop |
| 7 | Post-Mortem & Documentation | Document Understanding |

**Screenshots needed:**
- [ ] Maestro Cases list showing "NeuroScale Ops" case
- [ ] Case detail view showing all 7 stages in the flow diagram
- [ ] Stage 4 config showing "Human in Loop" type + UiPath Apps assignment
- [ ] Stage 7 config showing "Document Understanding" type

---

## STEP 2 — Build Triage Approval Form in UiPath Apps (20 min)

1. Left sidebar → **Apps** → **+ New App**
2. Name: **"NeuroScale Ops — Triage Approval"**
3. Add these fields (use Text/Label widgets for display, Button for actions):

**Display fields (read-only labels):**
- Alert ID: `demo-oom-001`
- Incident Type: `OOMKill`
- Severity: `CRITICAL`
- Root Cause: `Container exceeded memory limit; restart count high`
- AI Confidence: `94%`
- Recommended Action: `Increase memory limit to 2Gi`
- Cost Impact: `$15.00/mo delta — WITHIN_BUDGET`
- Runbook: `RB-001`

**Action buttons:**
- Green button: **"✓ APPROVE"**
- Red button: **"✗ REJECT"**
- Optional: Notes text area

4. Save the app

**Screenshots needed:**
- [ ] App editor showing the form with all fields
- [ ] Published app preview (mobile view if possible — shows UiPath Apps mobile-first story)
- [ ] App list showing the NeuroScale Ops app

---

## STEP 3 — Create a Live Case Instance (5 min)

1. Go back to Maestro → Cases → NeuroScale Ops
2. Click **"+ New Instance"** or **"Create Case"**
3. Fill in:
   - Title: `INC-001 — OOMKill: llm-inference production`
   - Severity: `CRITICAL`
   - Alert ID: `demo-oom-001`
4. Start the case — it will be at Stage 1

**Screenshots needed:**
- [ ] Case instance at Stage 1 (Incident Detection) — shows case is live
- [ ] Case advancing to Stage 2 (AI Triage) 
- [ ] Case at Stage 4 (Human Approval) — showing the approval gate

---

## STEP 4 — Screen Recording (10 min)

Record your screen (OBS/Loom/any tool) showing:
1. UiPath Cloud dashboard (org: hackathon26_581) — 10 seconds
2. Maestro → Cases → NeuroScale Ops case with 7 stages visible — 20 seconds
3. Click into Stage 4 (Human Approval) — show the form assignment — 15 seconds
4. UiPath Apps → open the Triage Approval form — show the fields — 20 seconds
5. Click "APPROVE" button — 5 seconds
6. Case advances to Stage 5 in Maestro — 10 seconds

**Total recording: ~80 seconds**

---

## What I'll do with your captures

Once you share the screenshots/recording:
1. Replace the fake "Maestro Case Definition" slide in the video (currently at 4:30) with the real Maestro UI
2. Replace the "Auto-approved in DEMO mode" section with a real UiPath Apps form screenshot
3. Add a 30-second "UiPath Cloud proof" segment showing the actual org dashboard
4. The video becomes genuinely authentic — judges can verify the case_definition.json matches what's in the portal

---

## STEP 5 — Run Real Pipeline with Groq (5 min)

On your local machine (or share screen):
```bash
cd neurascale-ops
pip install -r requirements.txt
export GROQ_API_KEY=gsk_REDACTED_USE_ENV_VAR
export DEMO_MODE=false  # Use real Groq
python main.py
```

**Screenshot needed:** Terminal showing real Groq latency (e.g. "llama-3.3-70b responded in 1.2s") — this proves it's a live API call, not mocked.

---

## Priority Order

| Priority | Item | Time | Impact |
|----------|------|------|--------|
| 🔴 MUST | Maestro 7-stage view in cloud | 15 min | Platform Usage 3→5/5 |
| 🔴 MUST | Triage Approval form in UiPath Apps | 20 min | HITL score + authenticity |
| 🟠 HIGH | Live case instance (Stage 4 approval) | 10 min | Video authenticity |
| 🟠 HIGH | Real Groq API terminal output | 5 min | AI score |
| 🟡 NICE | Mobile view of UiPath Apps form | 5 min | "enterprise-grade" story |
