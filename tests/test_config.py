from k8s_rl_gym.config import EnvironmentConfig


def test_default_config_is_small_and_local() -> None:
    config = EnvironmentConfig(deployments=["nginx-demo"])

    assert config.namespace == "default"
    assert config.deployments == ["nginx-demo"]
    assert config.min_replicas == 1
    assert config.max_replicas == 3
    assert "ready_replicas" in config.metrics
