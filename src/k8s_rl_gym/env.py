from time import sleep
from typing import Any

import gymnasium as gym
import numpy as np
from gymnasium import spaces

from k8s_rl_gym.k8s_client import DeploymentStatus, KubernetesDeploymentClient
from k8s_rl_gym.config import EnvironmentConfig


class KubernetesDeploymentEnv(gym.Env):
    metadata = {"render_modes": []}

    def __init__(self, config: EnvironmentConfig) -> None:
        super().__init__()

        self.config = config
        self.deployment_name = config.deployments[0] # TODO: support multiple deployments in the future
        self.namespace = config.namespace
        self.min_replicas = config.min_replicas
        self.max_replicas = config.max_replicas
        self.max_steps = config.max_steps
        self.stabilization_seconds = config.step_wait_seconds

        self.k8s = KubernetesDeploymentClient()
        self.current_step = 0

        replica_options = self.max_replicas - self.min_replicas + 1
        self.action_space = spaces.Discrete(replica_options)

        self.observation_space = spaces.Box(
            low=0.0,
            high=1.0,
            shape=(len(config.metrics),),
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

        self.k8s.scale_deployment(
            name=self.deployment_name,
            namespace=self.namespace,
            replicas=self.min_replicas,
        )
        status = self.k8s.wait_until_ready(
            name=self.deployment_name,
            namespace=self.namespace,
            timeout_seconds=120,
        )

        observation = self._status_to_observation(status)
        info = self._status_to_info(status)

        return observation, info

    def step(
        self,
        action: int,
    ) -> tuple[np.ndarray, float, bool, bool, dict[str, Any]]:
        self.current_step += 1

        target_replicas = self._action_to_replicas(action)

        self.k8s.scale_deployment(
            name=self.deployment_name,
            namespace=self.namespace,
            replicas=target_replicas,
        )

        sleep(self.stabilization_seconds)

        status = self.k8s.get_deployment_status(
            name=self.deployment_name,
            namespace=self.namespace,
        )

        observation = self._status_to_observation(status)
        reward = self._calculate_reward(status)
        terminated = False
        truncated = self.current_step >= self.max_steps

        info = self._status_to_info(status)
        info["action"] = int(action)
        info["target_replicas"] = target_replicas

        return observation, reward, terminated, truncated, info

    def _action_to_replicas(self, action: int) -> int:
        return self.min_replicas + int(action)

    def _status_to_observation(self, status: DeploymentStatus) -> np.ndarray:
        values = []

        for metric in self.config.metrics:
            if metric == "desired_replicas":
                values.append(status.desired_replicas / self.max_replicas)
            elif metric == "ready_replicas":
                values.append(status.ready_replicas / self.max_replicas)
            elif metric == "available_replicas":
                values.append(status.available_replicas / self.max_replicas)
            elif metric == "unavailable_replicas":
                values.append(status.unavailable_replicas / self.max_replicas)
            else:
                raise ValueError(f"Unsupported metric: {metric}")

        return np.array(values, dtype=np.float32)

    def _calculate_reward(self, status: DeploymentStatus) -> float:
        ready_score = 1.0 if status.ready_replicas == status.desired_replicas else -1.0
        replica_penalty = 0.1 * status.desired_replicas
        return ready_score - replica_penalty

    def _status_to_info(self, status: DeploymentStatus) -> dict[str, Any]:
        return {
            "deployment": status.name,
            "namespace": status.namespace,
            "desired_replicas": status.desired_replicas,
            "ready_replicas": status.ready_replicas,
            "available_replicas": status.available_replicas,
            "unavailable_replicas": status.unavailable_replicas,
            "step": self.current_step,
        }
