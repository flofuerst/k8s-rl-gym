from k8s_rl_gym.env import KubernetesDeploymentEnv


def main() -> None:
    env = KubernetesDeploymentEnv(
        deployment_name="nginx-demo",
        namespace="default",
        min_replicas=1,
        max_replicas=3,
        max_steps=5,
        stabilization_seconds=5.0,
    )

    observation, info = env.reset()

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
