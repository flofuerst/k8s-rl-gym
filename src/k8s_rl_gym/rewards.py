from typing import Protocol

from k8s_rl_gym.k8s_client import DeploymentStatus


class RewardFunction(Protocol):
    def __call__(self, statuses: list[DeploymentStatus], max_replicas: int) -> float:
        ...


def readiness_reward(statuses: list[DeploymentStatus], max_replicas: int) -> float:
    deployment_rewards = []

    for status in statuses:
        reward = 1.0 if status.ready_replicas == status.desired_replicas else -1.0
        deployment_rewards.append(reward)

    return sum(deployment_rewards) / len(deployment_rewards)


def efficiency_reward(statuses: list[DeploymentStatus], max_replicas: int) -> float:
    total_desired = sum(status.desired_replicas for status in statuses)
    max_possible = len(statuses) * max_replicas

    return 1.0 - (total_desired / max_possible)


def combined_reward(statuses: list[DeploymentStatus], max_replicas: int) -> float:
    return readiness_reward(statuses, max_replicas) + 0.5 * efficiency_reward(
        statuses,
        max_replicas,
    )


REWARD_FUNCTIONS: dict[str, RewardFunction] = {
    "readiness": readiness_reward,
    "efficiency": efficiency_reward,
    "combined": combined_reward,
}


def get_reward_function(name: str) -> RewardFunction:
    try:
        return REWARD_FUNCTIONS[name]
    except KeyError as error:
        supported = ", ".join(sorted(REWARD_FUNCTIONS))
        raise ValueError(f"Unsupported reward function '{name}'. Supported: {supported}") from error
