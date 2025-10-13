from tests.steps.system import *
import json
import time


@TestStep(When)
def get_pods(self, namespace):
    """Get the list of pods in the specified namespace and return in a list."""

    pods = run(cmd=f"minikube kubectl -- get pods -n {namespace} -o json")
    pods = json.loads(pods.stdout)["items"]

    return [p["metadata"]["name"] for p in pods]


@TestStep(Then)
def check_status(self, pod_name, namespace, status="Running"):
    """Check if the specified pod is in the desired status and ready."""

    actual_status = run(cmd=f"kubectl get pod {pod_name} -n {namespace} -o json")
    actual_status = json.loads(actual_status.stdout)
    phase = actual_status["status"]["phase"]
    conditions = actual_status["status"].get("conditions", [])
    ready = any(c["type"] == "Ready" and c["status"] == "True" for c in conditions)
    return phase == status and ready


@TestStep(Given)
def use_context(self, context_name):
    """Set the kubectl context to the specified context name."""

    run(cmd=f"kubectl config use-context {context_name}")


@TestStep(When)
def wait_for_pod_count(self, namespace, expected_count, timeout=300):
    """Wait until the number of pods in the specified namespace matches the expected count."""

    start_time = time.time()
    while True:
        pods = get_pods(namespace=namespace)
        if len(pods) == expected_count:
            return pods
        if time.time() - start_time > timeout:
            raise TimeoutError(
                f"Timeout waiting for {expected_count} pods in namespace {namespace}"
            )
        time.sleep(5)


@TestStep(When)
def get_pvcs(self, namespace):
    """Get the list of PVCs in the specified namespace."""

    pvcs = run(cmd=f"kubectl get pvc -n {namespace} -o json")
    pvcs = json.loads(pvcs.stdout)["items"]

    return [p["metadata"]["name"] for p in pvcs]


@TestStep(When)
def get_services(self, namespace):
    """Get the list of services in the specified namespace."""

    services = run(cmd=f"kubectl get svc -n {namespace} -o json")
    services = json.loads(services.stdout)["items"]

    return [s["metadata"]["name"] for s in services]


@TestStep(When)
def get_service_info(self, service_name, namespace):
    """Get the full service information as a dictionary."""

    service_info = run(cmd=f"kubectl get svc {service_name} -n {namespace} -o json")
    service_info = json.loads(service_info.stdout)

    return service_info


@TestStep(When)
def get_service_type(self, service_name, namespace):
    """Get the type of a specific service."""

    service_info = get_service_info(service_name=service_name, namespace=namespace)

    return service_info["spec"]["type"]


@TestStep(When)
def get_pod_nodes(self, namespace, pod_names):
    """Get the nodes where the specified pods are running."""

    nodes = []
    for pod_name in pod_names:
        pod_info = run(cmd=f"kubectl get pod {pod_name} -n {namespace} -o json")
        pod_info = json.loads(pod_info.stdout)
        nodes.append(pod_info["spec"]["nodeName"])

    return nodes


@TestStep(When)
def get_pod_image(self, namespace, pod_name):
    """Get the image used by a specific pod."""

    pod_info = run(cmd=f"kubectl get pod {pod_name} -n {namespace} -o json")
    pod_info = json.loads(pod_info.stdout)

    return pod_info["spec"]["containers"][0]["image"]


@TestStep(When)
def get_statefulsets(self, namespace):
    """Get the list of StatefulSets in the specified namespace."""

    statefulsets = run(cmd=f"kubectl get statefulsets -n {namespace} -o json")
    statefulsets = json.loads(statefulsets.stdout)

    return [s["metadata"]["name"] for s in statefulsets["items"]]


@TestStep(When)
def wait_for_pods_running(self, namespace, timeout=300):
    """Wait until all pods in the namespace are running and ready."""

    start_time = time.time()
    while True:
        pods = get_pods(namespace=namespace)
        all_running = True

        for pod in pods:
            if not check_status(pod_name=pod, namespace=namespace, status="Running"):
                all_running = False
                break

        if all_running:
            return pods

        if time.time() - start_time > timeout:
            # Get status of all pods for debugging
            pod_statuses = []
            for pod in pods:
                status = (
                    "Running"
                    if check_status(pod_name=pod, namespace=namespace, status="Running")
                    else "Not Running"
                )
                pod_statuses.append(f"{pod}: {status}")
            raise TimeoutError(
                f"Timeout waiting for pods to be running. Pod statuses: {pod_statuses}"
            )

        time.sleep(10)
