from k8s_rl_gym.rewards import readiness_reward


def test_readiness_reward_is_positive_when_ready_matches_desired() -> None:
    assert readiness_reward(desired_replicas=2, ready_replicas=2) == 1.0


def test_readiness_reward_is_negative_when_rollout_is_not_ready() -> None:
    assert readiness_reward(desired_replicas=3, ready_replicas=1) == -1.0
