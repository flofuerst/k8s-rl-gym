#!/usr/bin/env bash
set -euo pipefail

CLUSTER_NAME="${CLUSTER_NAME:-k8s-rl-gym}"
NAMESPACE="${NAMESPACE:-default}"

if ! kind get clusters | grep -qx "${CLUSTER_NAME}"; then
  kind create cluster \
    --name "${CLUSTER_NAME}" \
    --config k8s/kind-config.yaml
fi

kubectl config use-context "kind-${CLUSTER_NAME}"

kubectl create namespace "${NAMESPACE}" \
  --dry-run=client \
  -o yaml | kubectl apply -f -

kubectl apply -n "${NAMESPACE}" -f k8s/deployment.yaml
kubectl apply -n "${NAMESPACE}" -f k8s/service.yaml

kubectl rollout status deployment/nginx-demo -n "${NAMESPACE}" --timeout=120s
kubectl get deployments,pods,services -n "${NAMESPACE}" -l app=nginx-demo
