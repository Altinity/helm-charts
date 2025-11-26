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
def debug_namespace_state(self, namespace, expected_count=None, current_count=None):
    """Print detailed debugging information about namespace state.

    Args:
        namespace: Kubernetes namespace to debug
        expected_count: Expected number of pods (optional)
        current_count: Current number of pods (optional)
    """
    pods = get_pods(namespace=namespace)

    if expected_count and current_count is not None:
        note(f"❌ TIMEOUT: Expected {expected_count} pods, found {current_count}")

    # Show all pods and their states
    if pods:
        note(f"📋 Current pods: {', '.join(pods)}")
        for pod_name in pods:
            try:
                pod_info = get_pod_info(namespace=namespace, pod_name=pod_name)
                phase = pod_info["status"].get("phase", "Unknown")
                conditions = pod_info["status"].get("conditions", [])
                ready = any(c["type"] == "Ready" and c["status"] == "True" for c in conditions)

                # Get container statuses
                container_statuses = pod_info["status"].get("containerStatuses", [])
                container_info = []
                for cs in container_statuses:
                    state = cs.get("state", {})
                    if "waiting" in state:
                        reason = state["waiting"].get("reason", "Unknown")
                        message = state["waiting"].get("message", "")
                        container_info.append(f"Waiting: {reason} - {message}")
                    elif "terminated" in state:
                        reason = state["terminated"].get("reason", "Unknown")
                        container_info.append(f"Terminated: {reason}")
                    elif "running" in state:
                        container_info.append("Running")

                note(f"  • {pod_name}: Phase={phase}, Ready={ready}, Containers=[{', '.join(container_info)}]")
            except Exception as e:
                note(f"  • {pod_name}: Failed to get info - {str(e)}")
    else:
        note(f"📋 No pods found in namespace {namespace}")

    # Get all resources in namespace to see what's being created
    note(f"\n📦 All resources in namespace {namespace}:")
    all_resources = run(cmd=f"kubectl get all -n {namespace}", check=False)
    if all_resources.returncode == 0:
        note(all_resources.stdout)

    # Get recent events to see why pods aren't being created
    note(f"\n📅 Recent events in namespace {namespace}:")
    events_result = run(cmd=f"kubectl get events -n {namespace} --sort-by='.lastTimestamp' | tail -20", check=False)
    if events_result.returncode == 0:
        note(events_result.stdout)

    # Check for pending pods and describe them
    note(f"\n🔍 Describing all pods:")
    describe_result = run(cmd=f"kubectl describe pods -n {namespace}", check=False)
    if describe_result.returncode == 0:
        note(describe_result.stdout)

    # Check CHI (ClickHouseInstallation) configuration
    note(f"\n🔧 ClickHouseInstallation resources:")
    chi_result = run(cmd=f"kubectl get chi -n {namespace} -o yaml", check=False)
    if chi_result.returncode == 0:
        note(chi_result.stdout)


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
    last_count = -1
    while True:
        pods = get_pods(namespace=namespace)
        current_count = len(pods)

        # Log when pod count changes
        if current_count != last_count:
            note(f"Pod count in {namespace}: {current_count}/{expected_count}")
            last_count = current_count

        if current_count == expected_count:
            return pods

        if time.time() - start_time > timeout:
            # Show detailed debugging info before failing
            debug_namespace_state(
                namespace=namespace,
                expected_count=expected_count,
                current_count=current_count
            )

            raise TimeoutError(
                f"Timeout waiting for {expected_count} pods in namespace {namespace}. Found {current_count} pods."
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


@TestStep(Then)
def verify_pvc_access_mode(self, namespace, expected_access_mode, pvc_name_filter, resource_matcher=None):
    """Verify PVC access mode for PVCs matching filter.

    Args:
        namespace: Kubernetes namespace
        expected_access_mode: Expected access mode (e.g., "ReadWriteOnce")
        pvc_name_filter: String to filter PVC names (e.g., "data", "logs")
        resource_matcher: Optional function to check if PVC belongs to target resource

    Returns:
        Name of verified PVC
    """
    pvcs = get_pvcs(namespace=namespace)

    # Find matching PVCs
    for pvc in pvcs:
        if pvc_name_filter in pvc.lower():
            # Apply resource matcher if provided
            if resource_matcher and not resource_matcher(resource_name=pvc):
                continue

            pvc_info = get_pvc_info(namespace=namespace, pvc_name=pvc)
            access_modes = pvc_info.get("spec", {}).get("accessModes", [])

            assert (
                    expected_access_mode in access_modes
            ), f"Expected accessMode {expected_access_mode} in PVC {pvc}, got {access_modes}"

            note(f"✓ PVC {pvc_name_filter} accessMode: {expected_access_mode}")
            return pvc

    raise AssertionError(f"No {pvc_name_filter} PVC found for verification")


@TestStep(When)
def get_endpoints_info(self, namespace, endpoints_name):
    """Get detailed information about Kubernetes endpoints.

    Args:
        namespace: Kubernetes namespace
        endpoints_name: Name of the endpoints resource

    Returns:
        dict: Endpoints information
    """
    endpoints_info = run(
        cmd=f"kubectl get endpoints {endpoints_name} -n {namespace} -o json"
    )
    return json.loads(endpoints_info.stdout)


@TestStep(When)
def get_secrets(self, namespace):
    """Get list of secret names in a namespace.

    Args:
        namespace: Kubernetes namespace

    Returns:
        list: List of secret names
    """
    secrets_info = run(cmd=f"kubectl get secrets -n {namespace} -o json")
    secrets_data = json.loads(secrets_info.stdout)
    return [item["metadata"]["name"] for item in secrets_data.get("items", [])]


@TestStep(Finally)
def delete_namespace(self, namespace):
    """Delete a Kubernetes namespace.

    Args:
        namespace: Kubernetes namespace to delete
    """
    note(f"Deleting namespace: {namespace}")

    # Just delete the namespace and force-remove finalizers if it hangs
    run(
        cmd=f"timeout 15 kubectl delete namespace {namespace} --wait=true 2>/dev/null || "
            f"kubectl patch namespace {namespace} -p '{{\"metadata\":{{\"finalizers\":null}}}}' --type=merge 2>/dev/null",
        check=False
    )

    note(f"✓ Namespace {namespace} deleted")


@TestStep(When)
def delete_pod(self, namespace, pod_name):
    """Delete a Kubernetes pod.

    Args:
        namespace: Kubernetes namespace
        pod_name: Name of the pod to delete
    """
    run(cmd=f"kubectl delete pod {pod_name} -n {namespace}", check=True)
    note(f"✓ Pod {pod_name} deleted from namespace {namespace}")
