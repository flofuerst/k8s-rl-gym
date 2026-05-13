from k8s_rl_gym.config import EnvironmentConfig, load_environment_config
from pathlib import Path


def test_default_config_is_small_and_local() -> None:
    config = EnvironmentConfig(deployments=["nginx-demo"])

    assert config.namespace == "default"
    assert config.deployments == ["nginx-demo"]
    assert config.min_replicas == 1
    assert config.max_replicas == 3
    assert "ready_replicas" in config.metrics

def test_load_environment_config_from_yaml() -> None:
    config = load_environment_config(Path("configs/env.local.yaml"))

    assert config.namespace == "default"
    assert config.deployments == ["nginx-demo"]
    assert config.min_replicas == 1
    assert config.max_replicas == 3