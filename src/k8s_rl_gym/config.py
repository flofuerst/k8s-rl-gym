from pathlib import Path

import yaml
from pydantic import BaseModel, Field, model_validator


class EnvironmentConfig(BaseModel):
    namespace: str = "default"
    deployments: list[str] = Field(default_factory=list)
    min_replicas: int = 1
    max_replicas: int = 3
    metrics: list[str] = Field(default_factory=lambda: ["desired_replicas", "ready_replicas"])
    step_wait_seconds: float = 2.0
    max_steps: int = 10
    reward: str = "readiness"

    @model_validator(mode="after")
    def validate_replica_bounds(self) -> "EnvironmentConfig":
        if self.min_replicas > self.max_replicas:
            raise ValueError("min_replicas must be <= max_replicas")
        return self

    @model_validator(mode="after")
    def validate_deployments(self) -> "EnvironmentConfig":
        if not self.deployments:
            raise ValueError("at least one deployment must be configured")
        return self


def load_environment_config(path: str | Path) -> EnvironmentConfig:
    config_path = Path(path)

    with config_path.open("r", encoding="utf-8") as file:
        raw_config = yaml.safe_load(file)

    return EnvironmentConfig(**raw_config)
