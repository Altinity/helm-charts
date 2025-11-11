from tests.steps.system import *
import json
import time


@TestStep(When)
def get_pods(self, namespace):
    """Get the list of pods in the specified namespace and return in a list."""

    pods = run(cmd=f"minikube kubectl -- get pods -n {namespace} -o json")
    pods = json.loads(pods.stdout)["items"]

    return [p["metadata"]["name"] for p in pods]


@TestStep(When)
def get_pod_info(self, namespace, pod_name):
    """Get detailed information for a specific pod.

    Args:
        namespace: Kubernetes namespace
        pod_name: Name of the pod

    Returns:
        Dict with pod information
    """
    pod_info = run(cmd=f"kubectl get pod {pod_name} -n {namespace} -o json")
    return json.loads(pod_info.stdout)


@TestStep(Then)
def check_status(self, pod_name, namespace, status="Running"):
    """Check if the specified pod is in the desired status and ready."""

    pod_info = get_pod_info(namespace=namespace, pod_name=pod_name)
    phase = pod_info["status"]["phase"]
    conditions = pod_info["status"].get("conditions", [])
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
def get_pvc_info(self, namespace, pvc_name):
    """Get detailed information for a specific PVC.

    Args:
        namespace: Kubernetes namespace
        pvc_name: Name of the PVC

    Returns:
        Dict with PVC information
    """
    pvc_info = run(cmd=f"kubectl get pvc {pvc_name} -n {namespace} -o json")
    return json.loads(pvc_info.stdout)


@TestStep(When)
def get_pvc_storage_size(self, namespace, pvc_name):
    """Get storage size for a specific PVC.

    Args:
        namespace: Kubernetes namespace
        pvc_name: Name of the PVC

    Returns:
        Storage size string (e.g., "5Gi") or None if not found
    """
    pvc_data = get_pvc_info(namespace=namespace, pvc_name=pvc_name)
    return (
        pvc_data.get("spec", {}).get("resources", {}).get("requests", {}).get("storage")
    )


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
        pod_info = get_pod_info(namespace=namespace, pod_name=pod_name)
        nodes.append(pod_info["spec"]["nodeName"])

    return nodes


@TestStep(When)
def get_pod_image(self, namespace, pod_name):
    """Get the image used by a specific pod."""

    pod_info = get_pod_info(namespace=namespace, pod_name=pod_name)
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


@TestStep(Then)
def verify_pvc_storage_size(self, namespace, expected_size):
    """Verify that at least one PVC has the expected storage size."""

    pvcs = get_pvcs(namespace=namespace)
    assert len(pvcs) > 0, "No PVCs found for persistence"
    note(f"Created PVCs: {pvcs}")

    # Verify at least one PVC has the expected size
    for pvc in pvcs:
        storage_size = get_pvc_storage_size(namespace=namespace, pvc_name=pvc)
        if storage_size == expected_size:
            note(f"PVC {pvc} has correct storage size: {storage_size}")
            return pvc

    raise AssertionError(f"No PVC found with expected storage size {expected_size}")


@TestStep(Then)
def verify_loadbalancer_service_exists(self, namespace):
    """Verify that at least one LoadBalancer service exists."""

    services = get_services(namespace=namespace)
    lb_services = [
        s
        for s in services
        if get_service_type(service_name=s, namespace=namespace) == "LoadBalancer"
    ]
    assert len(lb_services) > 0, "LoadBalancer service not found"
    note(f"LoadBalancer services found: {lb_services}")

    return lb_services[0]


@TestStep(Then)
def verify_loadbalancer_source_ranges(self, namespace, service_name, expected_ranges):
    """Verify LoadBalancer service has correct source ranges."""

    service_info = get_service_info(service_name=service_name, namespace=namespace)
    source_ranges = service_info["spec"].get("loadBalancerSourceRanges", [])

    assert (
        source_ranges == expected_ranges
    ), f"Expected source ranges {expected_ranges}, got {source_ranges}"
    note(f"LoadBalancer source ranges verified: {source_ranges}")


@TestStep(Then)
def verify_loadbalancer_ports(self, namespace, service_name, expected_ports):
    """Verify LoadBalancer service has correct ports.

    Args:
        namespace: Kubernetes namespace
        service_name: Name of the service
        expected_ports: Dict mapping port names to port numbers, e.g. {"http": 8123, "tcp": 9000}
    """

    service_info = get_service_info(service_name=service_name, namespace=namespace)
    ports = service_info["spec"]["ports"]
    port_names = [p["name"] for p in ports]

    with By("verifying LoadBalancer ports"):
        for port_name in expected_ports.keys():
            assert (
                port_name in port_names
            ), f"Expected port '{port_name}' not found in {port_names}"

    with And("verifying port numbers"):
        for port in ports:
            if port["name"] in expected_ports:
                expected_port = expected_ports[port["name"]]
                assert (
                    port["port"] == expected_port
                ), f"Expected {port['name']} port {expected_port}, got {port['port']}"
                note(f"Port {port['name']}: {port['port']}")

    note(f"All LoadBalancer ports verified")


@TestStep(Then)
def verify_loadbalancer_service(self, namespace, expected_ranges=None):
    """Verify LoadBalancer service exists and has correct configuration.

    Args:
        namespace: Kubernetes namespace
        expected_ranges: Optional list of expected source ranges

    Returns:
        Service name of the LoadBalancer
    """
    services = get_services(namespace=namespace)
    lb_services = [
        s
        for s in services
        if get_service_type(service_name=s, namespace=namespace) == "LoadBalancer"
    ]

    assert len(lb_services) > 0, "LoadBalancer service not found"
    lb_service_name = lb_services[0]

    if expected_ranges:
        service_info = get_service_info(
            service_name=lb_service_name, namespace=namespace
        )
        source_ranges = service_info["spec"].get("loadBalancerSourceRanges", [])
        assert (
            source_ranges == expected_ranges
        ), f"Expected source ranges {expected_ranges}, got {source_ranges}"

    note(f"✓ LoadBalancer service: {lb_service_name}")
    return lb_service_name


@TestStep(When)
def delete_namespace(self, namespace):
    """Delete a Kubernetes namespace and wait for it to be removed.

    Args:
        namespace: Kubernetes namespace to delete
    """
    try:
        note(f"Deleting namespace: {namespace}")
        run(
            cmd=f"kubectl delete namespace {namespace} --wait=true --timeout=300s",
            exitcode=None,
        )
        note(f"✓ Namespace {namespace} deleted")
    except Exception as e:
        note(f"Warning: Failed to delete namespace {namespace}: {e}")
