"""
NeuroScale Ops — Streamlit Dashboard
Real-time visualization of the AI-powered K8s incident response pipeline
orchestrated by UiPath Maestro.

Usage:
    streamlit run dashboard/app.py
    DEMO_MODE=true streamlit run dashboard/app.py
"""

import sys
import os
import time
import json
import random
from datetime import datetime, timezone, timedelta
from pathlib import Path

import streamlit as st

# ── Path setup ────────────────────────────────────────────────────────────────
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
os.chdir(ROOT)
os.environ.setdefault("DEMO_MODE", "true")

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="NeuroScale Ops — AI Incident Response",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── CSS ───────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
  @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700&family=Inter:wght@400;500;600;700&display=swap');
  .stApp { background-color: #0a0e17; }
  .hero-title { font-family: 'Inter', sans-serif; font-size: 2.2rem; font-weight: 700; color: #e2e8f0; letter-spacing: -0.5px; }
  .hero-sub { font-family: 'Inter', sans-serif; font-size: 1rem; color: #64748b; margin-top: 4px; }
  .metric-card { background: linear-gradient(135deg, #111827 0%, #1a1f2e 100%); border: 1px solid #1e293b; border-radius: 12px; padding: 20px 24px; text-align: center; }
  .metric-value { font-family: 'JetBrains Mono', monospace; font-size: 2rem; font-weight: 700; color: #22d3ee; }
  .metric-label { font-family: 'Inter', sans-serif; font-size: 0.78rem; color: #64748b; text-transform: uppercase; letter-spacing: 1.2px; margin-top: 6px; }
  .badge-critical { background: #7f1d1d; color: #fca5a5; padding: 2px 10px; border-radius: 6px; font-size: 0.72rem; font-weight: 700; text-transform: uppercase; }
  .badge-warning { background: #431407; color: #fdba74; padding: 2px 10px; border-radius: 6px; font-size: 0.72rem; font-weight: 700; text-transform: uppercase; }
  .badge-resolved { background: #14532d; color: #86efac; padding: 2px 10px; border-radius: 6px; font-size: 0.72rem; font-weight: 700; text-transform: uppercase; }
  .stage-card { background: linear-gradient(135deg, #111827 0%, #1a1f2e 100%); border: 1px solid #1e293b; border-radius: 10px; padding: 16px 20px; margin-bottom: 10px; }
  .pipeline-node { background: #111827; border: 2px solid #1e293b; border-radius: 10px; padding: 12px 20px; text-align: center; }
  .pipeline-node.active { border-color: #22d3ee; box-shadow: 0 0 20px rgba(34,211,238,0.15); }
  .pipeline-node.done { border-color: #4ade80; }
  h1, h2, h3 { color: #e2e8f0 !important; }
  .stMarkdown { color: #cbd5e1; }
  section[data-testid="stSidebar"] { background-color: #0f1219; border-right: 1px solid #1e293b; }
</style>
""", unsafe_allow_html=True)

# ── Demo data generators ──────────────────────────────────────────────────────

def gen_incidents(n=8):
    types = ["OOMKILL", "CRASHLOOP", "POLICY_VIOLATION", "COST_SPIKE", "DEPLOYMENT_FAILURE"]
    namespaces = ["production", "ml-workloads", "staging", "default"]
    actions = ["patch_resources", "rollback", "scale_down", "create_exception", "monitor"]
    statuses = ["resolved", "in_progress", "pending_approval", "escalated"]
    incidents = []
    now = datetime.now(timezone.utc)
    for i in range(n):
        t = types[i % len(types)]
        st_ = statuses[i % len(statuses)]
        incidents.append({
            "id": f"INC-{1000+i}",
            "type": t,
            "severity": "critical" if t in ["OOMKILL", "CRASHLOOP", "DEPLOYMENT_FAILURE"] else "warning",
            "namespace": namespaces[i % len(namespaces)],
            "resource": f"neurascale-{['api', 'inference', 'bert', 'gateway', 'worker'][i%5]}-pod",
            "status": st_,
            "action": actions[i % len(actions)],
            "confidence": ["HIGH", "HIGH", "MEDIUM", "HIGH", "MEDIUM"][i % 5],
            "cost_delta": round(random.uniform(-50, 30), 2),
            "duration_s": round(random.uniform(5, 120), 1),
            "timestamp": (now - timedelta(minutes=i*12)).strftime("%H:%M:%S"),
        })
    return incidents

def gen_cost_data():
    return [
        {"namespace": "production",   "hourly": 1.23, "monthly": 369.0, "budget": 800.0, "pct": 46.1},
        {"namespace": "ml-workloads", "hourly": 0.83, "monthly": 249.0, "budget": 600.0, "pct": 41.5},
        {"namespace": "staging",      "hourly": 0.32, "monthly": 96.0,  "budget": 200.0, "pct": 48.0},
        {"namespace": "default",      "hourly": 0.04, "monthly": 12.0,  "budget": 100.0, "pct": 12.0},
    ]

STAGE_INFO = [
    ("1", "Detection",        "DetectorAgent",     "Watches K8s events, OOMKills, CrashLoops, Kyverno violations"),
    ("2", "AI Triage",        "TriageAgent",        "Groq llama-3.3-70b root cause analysis + runbook matching"),
    ("3", "Cost Analysis",    "CostImpactAgent",    "OpenCost namespace spend + budget utilisation"),
    ("4", "Human Approval",   "UiPath Apps",        "SRE reviews AI triage + cost context, approves/rejects"),
    ("5", "Remediation",      "RemediationAgent",   "kubectl patch / ArgoCD rollback / Kyverno exception"),
    ("6", "Post-Mortem",      "Document Understanding", "Auto-generated PDF post-mortem via UiPath DU"),
]

# ── Sidebar ───────────────────────────────────────────────────────────────────

with st.sidebar:
    st.markdown('<p class="hero-title" style="font-size:1.3rem;">⚡ NeuroScale Ops</p>', unsafe_allow_html=True)
    st.markdown('<p class="hero-sub">UiPath Maestro · AgentHack 2026</p>', unsafe_allow_html=True)
    st.divider()

    st.markdown("**Configuration**")
    demo_mode = st.toggle("Demo Mode", value=True, help="Use simulated K8s data")
    auto_refresh = st.toggle("Auto Refresh (10s)", value=False)
    show_cost = st.toggle("Show Cost Analysis", value=True)

    st.divider()
    st.markdown("**Maestro Pipeline**")
    for s_id, s_name, _, _ in STAGE_INFO:
        st.markdown(f"Stage {s_id}: `{s_name}`")

    st.divider()
    st.markdown("**Stack**")
    st.markdown("""
- 🤖 Groq llama-3.3-70b (Triage)
- ☸️ Kubernetes + KServe
- 🔒 Kyverno Policies
- 💰 OpenCost (FinOps)
- 🚀 ArgoCD (GitOps)
- 🧩 UiPath Maestro
""")

    if st.button("🔴 Trigger Demo Incident", use_container_width=True):
        st.session_state["trigger_demo"] = True

# ── Auto refresh ───────────────────────────────────────────────────────────────

if auto_refresh:
    time.sleep(10)
    st.rerun()

# ── Header ────────────────────────────────────────────────────────────────────

col_title, col_status = st.columns([3, 1])
with col_title:
    st.markdown('<p class="hero-title">⚡ NeuroScale Ops</p>', unsafe_allow_html=True)
    st.markdown('<p class="hero-sub">AI-Powered Kubernetes Incident Response — Orchestrated by UiPath Maestro</p>', unsafe_allow_html=True)
with col_status:
    st.markdown("")
    st.success("🟢 System Operational")
    st.caption(f"Last updated: {datetime.now().strftime('%H:%M:%S')}")

st.divider()

# ── KPIs ──────────────────────────────────────────────────────────────────────

incidents = gen_incidents()
active = sum(1 for i in incidents if i["status"] in ["in_progress", "pending_approval"])
resolved = sum(1 for i in incidents if i["status"] == "resolved")
escalated = sum(1 for i in incidents if i["status"] == "escalated")
avg_ttd = 0.8  # minutes to detect

c1, c2, c3, c4, c5 = st.columns(5)
with c1:
    st.markdown(f'<div class="metric-card"><div class="metric-value">{len(incidents)}</div><div class="metric-label">Total Incidents</div></div>', unsafe_allow_html=True)
with c2:
    st.markdown(f'<div class="metric-card"><div class="metric-value" style="color:#f87171">{active}</div><div class="metric-label">Active</div></div>', unsafe_allow_html=True)
with c3:
    st.markdown(f'<div class="metric-card"><div class="metric-value" style="color:#4ade80">{resolved}</div><div class="metric-label">Resolved</div></div>', unsafe_allow_html=True)
with c4:
    st.markdown(f'<div class="metric-card"><div class="metric-value" style="color:#fbbf24">{escalated}</div><div class="metric-label">Escalated</div></div>', unsafe_allow_html=True)
with c5:
    st.markdown(f'<div class="metric-card"><div class="metric-value">{avg_ttd}m</div><div class="metric-label">Avg. Time to Detect</div></div>', unsafe_allow_html=True)

st.markdown("---")

# ── Maestro Pipeline Stages ───────────────────────────────────────────────────

st.subheader("🧩 Maestro Case Pipeline")
stage_cols = st.columns(6)
for i, (s_id, s_name, agent, _) in enumerate(STAGE_INFO):
    with stage_cols[i]:
        color = "#22d3ee" if i < 3 else ("#4ade80" if i < 5 else "#fbbf24")
        st.markdown(f"""
<div class="pipeline-node active">
  <div style="font-size:1.4rem">{"🔍🧠💰👤⚡📄"[i]}</div>
  <div style="font-family:'Inter';font-size:0.78rem;font-weight:600;color:#e2e8f0;margin-top:4px">{s_name}</div>
  <div style="font-family:'JetBrains Mono';font-size:0.63rem;color:#475569">{agent}</div>
</div>
""", unsafe_allow_html=True)

st.markdown("---")

# ── Incident Feed ─────────────────────────────────────────────────────────────

col_incidents, col_detail = st.columns([2, 1])

with col_incidents:
    st.subheader("⚡ Live Incident Feed")

    for inc in incidents[:6]:
        sev_badge = f'<span class="badge-{inc["severity"]}">{inc["severity"].upper()}</span>'
        status_color = {"resolved": "#4ade80", "in_progress": "#22d3ee", "pending_approval": "#fbbf24", "escalated": "#f87171"}.get(inc["status"], "#94a3b8")

        with st.expander(f"[{inc['id']}] {inc['type']} — {inc['namespace']} @ {inc['timestamp']}", expanded=inc["status"] == "in_progress"):
            c1, c2, c3 = st.columns(3)
            with c1:
                st.markdown(f"**Severity:** {sev_badge}", unsafe_allow_html=True)
                st.markdown(f"**Namespace:** `{inc['namespace']}`")
            with c2:
                st.markdown(f"**Status:** `{inc['status']}`")
                st.markdown(f"**Confidence:** `{inc['confidence']}`")
            with c3:
                delta_color = "inverse" if inc["cost_delta"] > 0 else "normal"
                st.metric("Cost Delta", f"${inc['cost_delta']:+.2f}/mo")

            st.markdown(f"**Resource:** `{inc['resource']}`")
            st.markdown(f"**Action:** `{inc['action']}` | **Duration:** `{inc['duration_s']}s`")

with col_detail:
    st.subheader("🔍 Stage Detail")

    if st.session_state.get("trigger_demo"):
        st.warning("🔴 Demo incident triggered!")
        st.session_state["trigger_demo"] = False

    # Show triage detail for first active incident
    active_inc = next((i for i in incidents if i["status"] == "in_progress"), incidents[0])
    st.markdown(f"**Alert:** `{active_inc['id']}`")
    st.markdown(f"**Type:** `{active_inc['type']}`")
    st.markdown(f"**Root Cause Analysis:**")
    st.info(f"Groq llama-3.3-70b classified this as `{active_inc['type']}` with `{active_inc['confidence']}` confidence. Recommended action: `{active_inc['action']}`. Human approval required before execution.")

    st.markdown("**Maestro Stage:** `4 — Human Approval`")
    if st.button("✅ Approve (Demo)", use_container_width=True):
        st.success("Approved! Remediation queued.")
    if st.button("❌ Reject (Demo)", use_container_width=True):
        st.error("Rejected. Escalated to on-call.")

# ── Cost Analysis ─────────────────────────────────────────────────────────────

if show_cost:
    st.markdown("---")
    st.subheader("💰 OpenCost — Namespace Spend")

    import pandas as pd
    cost_data = gen_cost_data()
    df = pd.DataFrame(cost_data)

    col_chart, col_table = st.columns([1, 1])
    with col_chart:
        import plotly.express as px
        fig = px.bar(
            df, x="namespace", y="monthly",
            color="pct",
            color_continuous_scale=["#4ade80", "#fbbf24", "#f87171"],
            labels={"monthly": "Monthly Cost ($)", "pct": "Budget %"},
            template="plotly_dark",
        )
        fig.update_layout(
            plot_bgcolor="#111827",
            paper_bgcolor="#111827",
            font_color="#94a3b8",
            height=280,
            margin=dict(l=10, r=10, t=20, b=10),
        )
        st.plotly_chart(fig, use_container_width=True)

    with col_table:
        for row in cost_data:
            util = row["pct"]
            bar_color = "#4ade80" if util < 75 else ("#fbbf24" if util < 90 else "#f87171")
            st.markdown(f"""
**{row['namespace']}** — `${row['monthly']:.0f}` / `${row['budget']:.0f}` budget
""")
            st.progress(min(util / 100, 1.0))

st.markdown("---")
st.caption("NeuroScale Ops v1.0 · UiPath AgentHack 2026 · Track 1: Maestro Case · Built by Sodiq Jimoh")
