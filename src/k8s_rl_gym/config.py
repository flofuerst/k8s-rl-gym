"""Configuration models for the Kubernetes Gymnasium environment."""

from pydantic import BaseModel, Field


class EnvironmentConfig(BaseModel):
    """Minimal config skeleton that later phases will extend."""

    namespace: str = "default"
    deployments: list[str] = Field(default_factory=list)
    min_replicas: int = 1
    max_replicas: int = 3
    metrics: list[str] = Field(default_factory=lambda: ["desired_replicas", "ready_replicas"])
    step_wait_seconds: float = 2.0
    max_steps: int = 10
    reward: str = "readiness"
