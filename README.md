# k8s-rl-gym

Proof-of-concept Gymnasium environment for controlling Kubernetes Deployment
replica counts through the Kubernetes API.

The project is intentionally small and seminar-oriented. The goal is not to
beat Kubernetes HPA, but to show that a reusable Gymnasium environment can be
configured for different Deployments, metrics, and reward functions without
rewriting the RL environment each time.

## Current Scope

- Local Kind cluster
- Native Kubernetes Deployments
- Actions: desired replica count per configured Deployment
- Observations: Deployment and Pod status values from the Kubernetes API
- Optional later metrics: CPU and memory via metrics-server
- Agents: random baseline first, then simple rule-based baseline, optional SB3

## Phase 0: Tooling

Expected local tools:

```bash
python3 --version
poetry --version
docker --version
docker info
kubectl version --client
kind --version
```

On macOS, missing tools can usually be installed with Homebrew:

```bash
brew install python poetry kubectl kind
brew install --cask docker
```

`docker info` must show a running server before creating a Kind cluster. If it
prints `Cannot connect to the Docker daemon`, start Docker Desktop first.

## Phase 1: Python Project

Install dependencies and run the smoke tests:

```bash
poetry install
poetry run pytest
```

Expected result:

- Poetry creates or reuses a virtual environment.
- Pytest reports the config and reward tests as passing.

## Phase 2: Local Kubernetes Setup

Start Docker Desktop first, then create the Kind cluster and deploy the test app:

```bash
docker info
bash scripts/deploy_test_app.sh
```

Expected result:

- `docker info` shows both `Client` and `Server` sections without daemon errors.
- Kind creates or reuses a cluster named `k8s-rl-gym`.
- kubectl switches to context `kind-k8s-rl-gym`.
- The `nginx-demo` Deployment rolls out successfully.
- `kubectl get deployments,pods,services -l app=nginx-demo` shows one ready
  Deployment, one running Pod, and one ClusterIP Service.

Manual scaling check:

```bash
kubectl scale deployment/nginx-demo --replicas=2
kubectl rollout status deployment/nginx-demo --timeout=120s
kubectl get deployment nginx-demo
kubectl get pods -l app=nginx-demo
```

Expected result:

- The Deployment reports `2/2` ready replicas.
- Two Pods with label `app=nginx-demo` are running.

## Planned Project Structure

```text
k8s-rl-gym/
  configs/
    env.local.yaml
  k8s/
  results/
  scripts/
  src/
    k8s_rl_gym/
      config.py
      rewards.py
  tests/
```

## Report Notes To Preserve

While implementing, record observations about:

- How much configuration is needed to target a new Deployment.
- Which observation metrics are available from the normal Kubernetes API.
- Which metrics require metrics-server or another monitoring component.
- How delayed pod readiness affects the RL step loop.
- How the action and observation spaces change when Deployments or metrics are
  added to the config.
- What this PoC deliberately does not solve compared to production Kubernetes
  control.
