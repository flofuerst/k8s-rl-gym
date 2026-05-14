from time import sleep
from typing import Any

import gymnasium as gym
import numpy as np
from gymnasium import spaces

from k8s_rl_gym.k8s_client import DeploymentStatus, KubernetesDeploymentClient
from k8s_rl_gym.config import EnvironmentConfig
from k8s_rl_gym.rewards import get_reward_function


class KubernetesDeploymentEnv(gym.Env):
    metadata = {"render_modes": []}

    def __init__(self, config: EnvironmentConfig) -> None:
        super().__init__()

        self.config = config
        self.namespace = config.namespace
        self.min_replicas = config.min_replicas
        self.max_replicas = config.max_replicas
        self.max_steps = config.max_steps
        self.stabilization_seconds = config.step_wait_seconds
        
        self.reward_function = get_reward_function(config.reward)

        self.k8s = KubernetesDeploymentClient()
        self.current_step = 0

        replica_options = self.max_replicas - self.min_replicas + 1
        self.action_space = spaces.MultiDiscrete(
            [replica_options] * len(self.config.deployments)
        )

        self.observation_space = spaces.Box(
            low=0.0,
            high=1.0,
            shape=(len(config.metrics) * len(config.deployments),),
            dtype=np.float32,
        )

    def reset(
        self,
        *,
        seed: int | None = None,
        options: dict[str, Any] | None = None,
    ) -> tuple[np.ndarray, dict[str, Any]]:
        super().reset(seed=seed)

        self.current_step = 0
        statuses = []

        for deployment_name in self.config.deployments:
            self.k8s.scale_deployment(
                name=deployment_name,
                namespace=self.namespace,
                replicas=self.min_replicas,
            )

        for deployment_name in self.config.deployments:
            status = self.k8s.wait_until_ready(
                name=deployment_name,
                namespace=self.namespace,
                timeout_seconds=120,
            )
            statuses.append(status)

        observation = self._statuses_to_observation(statuses)
        info = self._statuses_to_info(statuses)

        return observation, info

    def step(
        self,
        action: int,
    ) -> tuple[np.ndarray, float, bool, bool, dict[str, Any]]:
        self.current_step += 1

        target_replicas = self._action_to_replicas(action)

        for deployment_name, replicas in zip(self.config.deployments, target_replicas):
            self.k8s.scale_deployment(
                name=deployment_name,
                namespace=self.namespace,
                replicas=replicas,
            )

        sleep(self.stabilization_seconds)

        statuses = []
        for deployment_name in self.config.deployments:
            status = self.k8s.get_deployment_status(
                name=deployment_name,
                namespace=self.namespace,
            )
            statuses.append(status)

        observation = self._statuses_to_observation(statuses)
        reward = self._calculate_reward(statuses)
        terminated = False
        truncated = self.current_step >= self.max_steps

        action_values = np.asarray(action, dtype=int).tolist()

        info = self._statuses_to_info(statuses)
        info["scaling"] = {
            deployment_name: {
                "action": action_value,
                "target_replicas": replicas,
            }
            for deployment_name, action_value, replicas in zip(
                self.config.deployments,
                action_values,
                target_replicas,
            )
        }

        return observation, reward, terminated, truncated, info

    def _action_to_replicas(self, action) -> list[int]:
        return [self.min_replicas + int(value) for value in action]

    def _statuses_to_observation(self, statuses: list[DeploymentStatus]) -> np.ndarray:
        values = []

        for status in statuses:
            for metric in self.config.metrics:
                value = self._metric_value(status, metric)
                values.append(self._normalize_metric(metric, value))

        return np.array(values, dtype=np.float32)

    def _metric_value(self, status: DeploymentStatus, metric: str) -> int:
        if metric == "desired_replicas":
            return status.desired_replicas
        if metric == "ready_replicas":
            return status.ready_replicas
        if metric == "available_replicas":
            return status.available_replicas
        if metric == "unavailable_replicas":
            return status.unavailable_replicas
        if metric == "pod_count":
            return status.pod_count
        if metric == "cpu_usage_millicores":
            if status.cpu_usage_millicores is None:
                raise ValueError("cpu_usage_millicores requires metrics-server")
            return status.cpu_usage_millicores
        if metric == "memory_usage_mib":
            if status.memory_usage_mib is None:
                raise ValueError("memory_usage_mib requires metrics-server")
            return status.memory_usage_mib

        raise ValueError(f"Unsupported metric: {metric}")
    
    def _normalize_metric(self, metric: str, value: int) -> float:
        if metric in {
            "desired_replicas",
            "ready_replicas",
            "available_replicas",
            "unavailable_replicas",
            "pod_count",
        }:
            return value / self.max_replicas

        if metric == "cpu_usage_millicores":
            return min(value / 1000.0, 1.0)

        if metric == "memory_usage_mib":
            return min(value / 512.0, 1.0)

        raise ValueError(f"Unsupported metric: {metric}")

    def _calculate_reward(self, statuses: list[DeploymentStatus]) -> float:
        return self.reward_function(statuses, self.max_replicas)

    def _statuses_to_info(self, statuses: list[DeploymentStatus]) -> dict[str, Any]:
        deployments = {}

        for status in statuses:
            deployments[status.name] = {
                "namespace": status.namespace,
                "desired_replicas": status.desired_replicas,
                "ready_replicas": status.ready_replicas,
                "available_replicas": status.available_replicas,
                "unavailable_replicas": status.unavailable_replicas,
                "observed_metrics": {
                    metric: {
                        "raw": self._metric_value(status, metric),
                        "normalized": self._normalize_metric(metric, self._metric_value(status, metric)),
                    }
                    for metric in self.config.metrics
                },
            }

        return {
            "step": self.current_step,
            "deployments": deployments,
        }
