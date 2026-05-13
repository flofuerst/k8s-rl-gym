from k8s_rl_gym.config import load_environment_config
from k8s_rl_gym.env import KubernetesDeploymentEnv


def main() -> None:
    config = load_environment_config("configs/env.local.yaml")
    env = KubernetesDeploymentEnv(config)

    observation, info = env.reset()

    print("Observation space:", env.observation_space)
    print("Action space:", env.action_space)
    print("Initial observation:", observation)
    print("Initial info:", info)

    done = False

    while not done:
        action = env.action_space.sample()

        observation, reward, terminated, truncated, info = env.step(action)

        print()
        print(f"Step {info['step']}")
        print(f"Action: {action} -> target replicas: {info['target_replicas']}")
        print("Observation:", observation)
        print("Reward:", reward)
        print("Info:", info)

        done = terminated or truncated

    env.close()


if __name__ == "__main__":
    main()
