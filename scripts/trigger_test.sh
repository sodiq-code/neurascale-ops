#!/usr/bin/env bash
# NeuroScale Ops — Trigger Test Scenarios
# Injects incident conditions into a running Kind cluster for live demo.
# Run AFTER `kind create cluster` and `kubectl apply -k k8s/base/`
#
# Usage:
#   ./scripts/trigger_test.sh oomkill           # OOMKill scenario
#   ./scripts/trigger_test.sh crashloop         # CrashLoop scenario
#   ./scripts/trigger_test.sh policy_violation  # Kyverno violation
#   ./scripts/trigger_test.sh cost_spike        # Simulate cost spike
#   ./scripts/trigger_test.sh all               # All scenarios

set -euo pipefail
SCENARIO="${1:-oomkill}"

echo ""
echo "🔴 Triggering Test Scenario: $SCENARIO"
echo ""

case "$SCENARIO" in
  oomkill)
    echo "Injecting OOMKill scenario..."
    kubectl apply -f k8s/scenarios/inject-oomkill.yaml
    echo "✓ OOMKill pod deployed in 'default' namespace."
    echo "  Watch: kubectl get pods -w"
    ;;

  crashloop)
    echo "Injecting CrashLoop scenario..."
    kubectl apply -f k8s/scenarios/inject-crashloop.yaml
    echo "✓ CrashLoop pod deployed."
    echo "  Watch: kubectl get pods -w"
    ;;

  policy_violation)
    echo "Injecting Kyverno Policy Violation scenario..."
    kubectl apply -f k8s/scenarios/inject-policy-violation.yaml
    echo "✓ Policy violation test pod applied (should be blocked by Kyverno)."
    echo "  Check: kubectl get events -A | grep kyverno"
    ;;

  cost_spike)
    echo "Simulating cost spike via Prometheus pushgateway..."
    # Push a fake metric to alert on
    curl -s --data-binary @- "http://localhost:9091/metrics/job/neurascale_cost_test" << 'EOF'
# HELP neurascale_namespace_cost_usd Simulated namespace cost
# TYPE neurascale_namespace_cost_usd gauge
neurascale_namespace_cost_usd{namespace="ml-workloads"} 847.50
EOF
    echo "✓ Cost spike metric pushed. Alert will fire within ~1min."
    ;;

  all)
    echo "Running all scenarios with 10s delay between each..."
    for s in oomkill crashloop; do
      "$0" "$s"
      sleep 10
    done
    ;;

  cleanup)
    echo "Cleaning up all test resources..."
    kubectl delete pod oomkill-test crashloop-test 2>/dev/null || true
    kubectl delete deployment nginx-privileged 2>/dev/null || true
    echo "✓ Cleanup complete."
    ;;

  *)
    echo "Unknown scenario: $SCENARIO"
    echo "Available: oomkill | crashloop | policy_violation | cost_spike | all | cleanup"
    exit 1
    ;;
esac

echo ""
echo "📊 Monitor pipeline: streamlit run dashboard/app.py"
