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
