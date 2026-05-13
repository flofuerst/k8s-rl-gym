from dataclasses import dataclass
from time import sleep, time

from kubernetes import client, config
from kubernetes.client import AppsV1Api


@dataclass(frozen=True)
class DeploymentStatus:
    name: str
    namespace: str
    desired_replicas: int
    ready_replicas: int
    available_replicas: int
    unavailable_replicas: int


class KubernetesDeploymentClient:
    def __init__(self) -> None:
        config.load_kube_config()
        self.apps_api: AppsV1Api = client.AppsV1Api()

    def get_deployment_status(self, name: str, namespace: str = "default") -> DeploymentStatus:
        deployment = self.apps_api.read_namespaced_deployment(
            name=name,
            namespace=namespace,
        )

        desired = deployment.spec.replicas or 0
        ready = deployment.status.ready_replicas or 0
        available = deployment.status.available_replicas or 0
        unavailable = deployment.status.unavailable_replicas or 0

        return DeploymentStatus(
            name=name,
            namespace=namespace,
            desired_replicas=desired,
            ready_replicas=ready,
            available_replicas=available,
            unavailable_replicas=unavailable,
        )

    def scale_deployment(self, name: str, replicas: int, namespace: str = "default") -> None:
        body = {"spec": {"replicas": replicas}}

        self.apps_api.patch_namespaced_deployment_scale(
            name=name,
            namespace=namespace,
            body=body,
        )

    def wait_until_ready(
        self,
        name: str,
        namespace: str = "default",
        timeout_seconds: float = 120.0,
        poll_interval_seconds: float = 2.0,
    ) -> DeploymentStatus:
        deadline = time() + timeout_seconds

        while time() < deadline:
            status = self.get_deployment_status(name=name, namespace=namespace)

            if status.desired_replicas == status.ready_replicas:
                return status

            sleep(poll_interval_seconds)

        raise TimeoutError(
            f"Deployment {namespace}/{name} did not become ready within "
            f"{timeout_seconds} seconds."
        )
