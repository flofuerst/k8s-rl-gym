from k8s_rl_gym.k8s_client import KubernetesDeploymentClient


def print_status(label: str, status) -> None:
    print(f"{label}:")
    print(f"  deployment: {status.namespace}/{status.name}")
    print(f"  desired replicas: {status.desired_replicas}")
    print(f"  ready replicas: {status.ready_replicas}")
    print(f"  available replicas: {status.available_replicas}")
    print(f"  unavailable replicas: {status.unavailable_replicas}")


def main() -> None:
    namespace = "default"
    deployment_name = "nginx-demo"

    k8s = KubernetesDeploymentClient()

    initial_status = k8s.get_deployment_status(
        name=deployment_name,
        namespace=namespace,
    )
    print_status("Initial status", initial_status)

    target_replicas = 2 if initial_status.desired_replicas == 1 else 1
    print(f"\nScaling {deployment_name} to {target_replicas} replicas...")

    k8s.scale_deployment(
        name=deployment_name,
        namespace=namespace,
        replicas=target_replicas,
    )

    final_status = k8s.wait_until_ready(
        name=deployment_name,
        namespace=namespace,
        timeout_seconds=120,
    )
    print_status("Final status", final_status)


if __name__ == "__main__":
    main()
