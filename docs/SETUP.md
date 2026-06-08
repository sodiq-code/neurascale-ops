# NeuroScale Ops — Setup Guide

## Prerequisites

| Tool | Version | Notes |
|------|---------|-------|
| Python | 3.10+ | 3.11 recommended |
| Docker | 24+ | For containerized run |
| kubectl | 1.28+ | For real cluster mode |
| kind | 0.20+ | Local K8s cluster |
| ArgoCD CLI | 2.9+ | Optional — for sync ops |
| UiPath Orchestrator | 2024.10+ | Required for Maestro |

---

## Quick Start (Demo Mode — No Cluster Needed)

```bash
# 1. Clone the repo
git clone https://github.com/sodiq-code/neurascale-ops.git
cd neurascale-ops

# 2. Create virtual environment
python -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment
cp .env.example .env
# Edit .env — set DEMO_MODE=true (default), optionally add OPENAI_API_KEY

# 5. Run full demo pipeline
python main.py --demo

# Or run a specific incident scenario
python main.py --scenario oomkill --demo
python main.py --scenario crashloop --demo
python main.py --scenario cost_spike --demo
```

**Expected output:**
```
[NeuroScale Ops] Detecting incidents... (DEMO_MODE)
[Detector] Generated alert: INC-20240115-001 [OOMKILL/CRITICAL]
[TriageAgent] Analyzing alert... rule-based mode
[TriageAgent] Root cause: OOMKILL (confidence: HIGH)
[CostAgent] Projected waste: $45.50/hr if unresolved
[RemediationAgent] DRY_RUN: would patch_resources on payment-service/production
[Notification] Slack payload generated
Pipeline complete in 0.42s
```

---

## With OpenAI GPT-4o-mini (AI Triage Mode)

```bash
# Add your key to .env
echo "OPENAI_API_KEY=sk-..." >> .env

# Re-run — triage will now use GPT-4o-mini
python main.py --scenario oomkill
```

---

## Real Kubernetes Mode

### 1. Create a local cluster with kind

```bash
kind create cluster --name neurascale-ops

# Verify
kubectl cluster-info --context kind-neurascale-ops
```

### 2. Install ArgoCD

```bash
kubectl create namespace argocd
kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml

# Expose ArgoCD API
kubectl port-forward svc/argocd-server -n argocd 8080:443 &

# Get initial password
argocd admin initial-password -n argocd
```

### 3. Install Kyverno

```bash
helm repo add kyverno https://kyverno.github.io/kyverno/
helm install kyverno kyverno/kyverno -n kyverno --create-namespace
```

### 4. Apply NeuroScale Ops manifests

```bash
kubectl apply -f k8s/base/namespace.yaml
kubectl apply -f k8s/base/neurascale-ops-deployment.yaml
kubectl apply -f k8s/policies/
```

### 5. Deploy via ArgoCD

```bash
kubectl apply -f k8s/base/argocd-application.yaml
argocd app sync neurascale-ops
```

### 6. Configure .env for real mode

```bash
DEMO_MODE=false
KUBECONFIG=/path/to/kubeconfig
ARGOCD_SERVER=localhost:8080
ARGOCD_TOKEN=<your-argocd-token>
PROMETHEUS_URL=http://localhost:9090
OPENCOST_URL=http://localhost:9003
```

---

## UiPath Orchestrator Integration

### 1. Import Maestro Case

1. Log in to UiPath Orchestrator
2. Navigate to **Maestro** → **Cases**
3. Click **Import** → upload `uipath/maestro_case/case_definition.json`
4. Configure triggers: set Prometheus webhook URL to your Orchestrator webhook endpoint

### 2. Configure Agent Builder

1. Go to **Agent Builder** in Orchestrator
2. Import `uipath/agent_builder/notification_agent.json`
3. Set Slack webhook URL in agent settings

### 3. Import UiPath Apps (Human-in-the-Loop Forms)

1. Go to **Apps** in Orchestrator
2. Import all files from `uipath/apps/`:
   - `triage_approval_form.json` — Stage 3 human approval
   - `remediation_approval_form.json` — Stage 4 execution gate
   - `signoff_form.json` — Stage 6 post-remediation sign-off

### 4. Configure API Workflows

The workflow YAMLs in `uipath/api_workflows/` define Orchestrator API connections:

| File | Purpose |
|------|---------|
| `prometheus_webhook.yaml` | Receive alerts from Prometheus Alertmanager |
| `argocd_trigger.yaml` | Trigger ArgoCD sync via REST API |
| `opencost_query.yaml` | Query OpenCost for cost attribution |

---

## Run Tests

```bash
# Run full test suite (demo mode, no API keys needed)
pytest tests/ -v --tb=short

# With coverage
pytest tests/ -v --cov=agents --cov-report=term-missing
```

---

## Live Dashboard

```bash
# Start the Streamlit incident dashboard
streamlit run dashboard/app.py

# Visit: http://localhost:8501
```

---

## Docker Compose (All-in-One)

```bash
# Start everything: app + Prometheus + Grafana
docker-compose up

# NeuroScale Ops dashboard: http://localhost:8501
# Prometheus: http://localhost:9090
# Grafana: http://localhost:3000
```

---

## Demo Scripts

```bash
# Full 5-scenario demo
chmod +x scripts/demo_run.sh
./scripts/demo_run.sh

# Webhook trigger simulation
chmod +x scripts/trigger_test.sh
./scripts/trigger_test.sh
```

---

## Troubleshooting

| Issue | Fix |
|-------|-----|
| `ModuleNotFoundError: agents` | Run from repo root: `cd neurascale-ops && python main.py` |
| OpenAI quota exceeded | Set `OPENAI_API_KEY=""` to use rule-based fallback |
| ArgoCD 401 Unauthorized | Regenerate token: `argocd account generate-token` |
| Kyverno policies not enforcing | Check Kyverno pod: `kubectl get pods -n kyverno` |
| K8s connection refused | Verify `KUBECONFIG` path and context |

---

## Architecture Overview

```
Prometheus Alert
      │
      ▼
 IncidentDetector  ──────►  UiPath Maestro Case
      │                          │
      │                    Stage 1: Detection
      │                    Stage 2: AI Triage (GPT-4o-mini)
      │                    Stage 3: Cost Analysis (OpenCost)
      │                    Stage 4: Human Approval (UiPath Apps)
      │                    Stage 5: Remediation (ArgoCD)
      │                    Stage 6: Sign-Off (UiPath Apps)
      │                    Stage 7: Post-Mortem (Jira)
      │
      └──► Notification (Slack/Teams/PagerDuty)
```
