"""Reward functions used by the Gymnasium environment."""


def readiness_reward(desired_replicas: int, ready_replicas: int) -> float:
    """Reward readiness while penalizing incomplete rollout state."""

    return 1.0 if desired_replicas == ready_replicas else -1.0
