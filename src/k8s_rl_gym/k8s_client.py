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
    pod_count: int
    cpu_usage_millicores: int | None
    memory_usage_mib: int | None


class KubernetesDeploymentClient:
    def __init__(self) -> None:
        config.load_kube_config()
        self.apps_api: AppsV1Api = client.AppsV1Api() # used for read and scale deployments
        self.core_api = client.CoreV1Api() # used for reading pods
        self.custom_api = client.CustomObjectsApi()


    def get_deployment_status(self, name: str, namespace: str = "default") -> DeploymentStatus:
        deployment = self.apps_api.read_namespaced_deployment(
            name=name,
            namespace=namespace,
        )

        desired = deployment.spec.replicas or 0
        ready = deployment.status.ready_replicas or 0
        available = deployment.status.available_replicas or 0
        unavailable = deployment.status.unavailable_replicas or 0
        pod_count = self.count_deployment_pods(name=name, namespace=namespace)
        cpu_usage_millicores, memory_usage_mib = self.get_deployment_resource_usage(name=name,namespace=namespace,)

        return DeploymentStatus(
            name=name,
            namespace=namespace,
            desired_replicas=desired,
            ready_replicas=ready,
            available_replicas=available,
            unavailable_replicas=unavailable,
            pod_count=pod_count,
            cpu_usage_millicores=cpu_usage_millicores,
            memory_usage_mib=memory_usage_mib,
        )
    
    def get_deployment_resource_usage(self, name: str, namespace: str = "default",) -> tuple[int | None, int | None]:
        deployment = self.apps_api.read_namespaced_deployment(
            name=name,
            namespace=namespace,
        )

        match_labels = deployment.spec.selector.match_labels or {}
        label_selector = ",".join(
            f"{key}={value}" for key, value in match_labels.items()
        )

        pods = self.core_api.list_namespaced_pod(
            namespace=namespace,
            label_selector=label_selector,
        )
        pod_names = {pod.metadata.name for pod in pods.items}

        try:
            metrics = self.custom_api.list_namespaced_custom_object(
                group="metrics.k8s.io",
                version="v1beta1",
                namespace=namespace,
                plural="pods",
            )
        except client.ApiException as error:
            if error.status == 404:
                return None, None
            raise

        total_cpu = 0
        total_memory = 0

        for item in metrics.get("items", []):
            if item["metadata"]["name"] not in pod_names:
                continue

            for container in item.get("containers", []):
                usage = container.get("usage", {})
                total_cpu += parse_cpu_to_millicores(usage.get("cpu", "0"))
                total_memory += parse_memory_to_mib(usage.get("memory", "0"))

        return total_cpu, total_memory


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
    
    def count_deployment_pods(self, name: str, namespace: str = "default") -> int:
        deployment = self.apps_api.read_namespaced_deployment(
            name=name,
            namespace=namespace,
        )

        match_labels = deployment.spec.selector.match_labels or {}
        label_selector = ",".join(
            f"{key}={value}" for key, value in match_labels.items()
        )

        pods = self.core_api.list_namespaced_pod(
            namespace=namespace,
            label_selector=label_selector,
        )

        return len(pods.items)
    
def parse_cpu_to_millicores(cpu: str) -> int:
    if cpu.endswith("n"):
        return int(cpu[:-1]) // 1_000_000
    if cpu.endswith("u"):
        return int(cpu[:-1]) // 1_000
    if cpu.endswith("m"):
        return int(cpu[:-1])
    return int(float(cpu) * 1000)


def parse_memory_to_mib(memory: str) -> int:
    if memory.endswith("Ki"):
        return int(memory[:-2]) // 1024
    if memory.endswith("Mi"):
        return int(memory[:-2])
    if memory.endswith("Gi"):
        return int(memory[:-2]) * 1024
    return int(memory) // (1024 * 1024)


