from k8s_rl_gym.config import load_environment_config
from k8s_rl_gym.env import KubernetesDeploymentEnv


def print_observation(info: dict) -> None:
    for deployment_name, deployment_info in info["deployments"].items():
        print(f"  {deployment_name}:")
        for metric, values in deployment_info["observed_metrics"].items():
            print(
                f"    {metric}: "
                f"raw={values['raw']}, "
                f"normalized={values['normalized']:.3f}"
            )


def main() -> None:
    config = load_environment_config("configs/env.local.yaml")
    env = KubernetesDeploymentEnv(config)

    observation, info = env.reset()

    print("Observation space:", env.observation_space)
    print("Action space:", env.action_space)
    print("Initial observation:")
    print_observation(info)
    print("Initial info:", info)

    done = False

    while not done:
        action = env.action_space.sample()

        observation, reward, terminated, truncated, info = env.step(action)

        print()
        print(f"Step {info['step']}")
        print(f"Action: {action}")
        print("Scaling:")
        for deployment_name, scaling_info in info["scaling"].items():
            print(
                f"  {deployment_name}: action {scaling_info['action']} "
                f"-> target replicas {scaling_info['target_replicas']}"
            )
        print("Observation:")
        print_observation(info)
        print("Reward:", reward)
        print("Info:", info)

        done = terminated or truncated

    env.close()


if __name__ == "__main__":
    main()
