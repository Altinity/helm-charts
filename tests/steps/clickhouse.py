from tests.steps.system import *
import json
import time
import tests.steps.kubernetes as kubernetes


@TestStep(When)
def execute_clickhouse_query(self, namespace, pod_name, query, user="default", password="", check=True):
    """Execute a query on ClickHouse pod.
    
    Args:
        namespace: Kubernetes namespace
        pod_name: Name of the ClickHouse pod
        query: SQL query to execute
        user: Username for authentication (default: "default")
        password: Password for authentication (default: "")
        check: Whether to raise exception on error (default: True)
        
    Returns:
        Command result object
    """
    auth_args = f"-u {user}"
    if password:
        auth_args += f" --password {password}"
    
    return run(
        cmd=f"kubectl exec -n {namespace} {pod_name} -- clickhouse-client {auth_args} -q '{query}'",
        check=check
    )


@TestStep(When)
def get_version(self, namespace, pod_name, user="default", password=""):
    """Get ClickHouse version from the specified pod."""
    
    result = execute_clickhouse_query(
        namespace=namespace,
        pod_name=pod_name,
        query="SELECT version()",
        user=user,
        password=password
    )
    return result.stdout.strip()


@TestStep(When)
def test_clickhouse_connection(self, namespace, pod_name, user, password):
    """Test ClickHouse connection with given credentials."""

    try:
        result = execute_clickhouse_query(
            namespace=namespace,
            pod_name=pod_name,
            query="SELECT 1",
            user=user,
            password=password,
            check=False
        )
        return result.returncode == 0
    except:
        return False


@TestStep(When)
def get_chi_list(self, namespace):
    """Get list of all ClickHouseInstallation resources in namespace.
    
    Args:
        namespace: Kubernetes namespace
        
    Returns:
        List of CHI resources
    """
    chi_result = run(cmd=f"kubectl get chi -n {namespace} -o json")
    chi_data = json.loads(chi_result.stdout)
    return chi_data.get("items", [])


@TestStep(When)
def get_chi_info(self, namespace):
    """Get the first ClickHouseInstallation resource information.
    
    Args:
        namespace: Kubernetes namespace
        
    Returns:
        Dict with CHI information or None if not found
    """
    chi_items = get_chi_list(namespace=namespace)
    return chi_items[0] if chi_items else None


@TestStep(When)
def get_chi_name(self, namespace):
    """Get the name of the first ClickHouseInstallation resource.
    
    Args:
        namespace: Kubernetes namespace
        
    Returns:
        CHI name string or None if not found
    """
    chi_info = get_chi_info(namespace=namespace)
    return chi_info["metadata"]["name"] if chi_info else None


def is_clickhouse_resource(resource_name):
    """Check if a resource name is a ClickHouse resource.
    
    Args:
        resource_name: Name of the resource (pod, pvc, etc.)
        
    Returns:
        True if resource is ClickHouse-related
    """
    name_lower = resource_name.lower()
    return "clickhouse" in name_lower or "chi-" in name_lower


@TestStep(Then)
def verify_clickhouse_pvc_size(self, namespace, expected_size):
    """Verify that ClickHouse PVCs have the expected storage size.
    
    Args:
        namespace: Kubernetes namespace
        expected_size: Expected storage size (e.g., "5Gi")
    
    Returns:
        True if PVC with expected size is found
    """
    pvcs = kubernetes.get_pvcs(namespace=namespace)
    assert len(pvcs) > 0, "No PVCs found for persistence"
    
    for pvc in pvcs:
        # Filter for ClickHouse PVCs
        if is_clickhouse_resource(pvc):
            storage_size = kubernetes.get_pvc_storage_size(namespace=namespace, pvc_name=pvc)
            if storage_size == expected_size:
                note(f"✓ Persistence: {storage_size}")
                return True
    
    raise AssertionError(f"No PVC found with expected storage size {expected_size}")


@TestStep(When)
def get_clickhouse_pods(self, namespace):
    """Get only ClickHouse pods (excluding operator pods) from the specified namespace."""

    pods = kubernetes.get_pods(namespace=namespace)
    return [p for p in pods if "chi-" in p and "operator" not in p]


@TestStep(When)
def wait_for_clickhouse_pods_running(self, namespace, expected_count=None, timeout=300):
    """Wait for ClickHouse pods to be running and ready."""

    start_time = time.time()
    while True:
        clickhouse_pods = get_clickhouse_pods(namespace=namespace)

        if expected_count and len(clickhouse_pods) != expected_count:
            if time.time() - start_time > timeout:
                raise TimeoutError(
                    f"Timeout waiting for {expected_count} ClickHouse pods, got {len(clickhouse_pods)}"
                )
            time.sleep(5)
            continue

        if len(clickhouse_pods) == 0:
            if time.time() - start_time > timeout:
                raise TimeoutError("Timeout waiting for ClickHouse pods to be created")
            time.sleep(5)
            continue

        all_running = True

        for pod in clickhouse_pods:
            if not kubernetes.check_status(
                pod_name=pod, namespace=namespace, status="Running"
            ):
                all_running = False
                break

        if all_running:
            return clickhouse_pods

        if time.time() - start_time > timeout:
            pod_statuses = []
            for pod in clickhouse_pods:
                status = (
                    "Running"
                    if kubernetes.check_status(
                        pod_name=pod, namespace=namespace, status="Running"
                    )
                    else "Not Running"
                )
                pod_statuses.append(f"{pod}: {status}")
            raise TimeoutError(
                f"Timeout waiting for ClickHouse pods to be running. Pod statuses: {pod_statuses}"
            )

        time.sleep(10)


@TestStep(When)
def verify_clickhouse_version(self, namespace, expected_version, pod_name=None, user="default", password=""):
    """Verify ClickHouse version matches expected version."""

    if pod_name is None:
        clickhouse_pods = get_clickhouse_pods(namespace=namespace)
        if not clickhouse_pods:
            raise AssertionError("No ClickHouse pods found")
        pod_name = clickhouse_pods[0]

    version = get_version(namespace=namespace, pod_name=pod_name, user=user, password=password)
    note(f"ClickHouse version: {version}")

    assert (
        version == expected_version
    ), f"Expected version {expected_version}, got {version}"


@TestStep(When)
def verify_custom_name_in_resources(self, namespace, custom_name):
    """Verify that custom name appears in ClickHouse resources."""

    chi_name = get_chi_name(namespace=namespace)
    assert (
        custom_name in chi_name
    ), f"Custom name '{custom_name}' not found in CHI name: {chi_name}"

    clickhouse_pods = get_clickhouse_pods(namespace=namespace)
    assert len(clickhouse_pods) > 0, "No ClickHouse pods found"
    note(f"ClickHouse pods created: {clickhouse_pods}")


@TestStep(When)
def verify_persistence_configuration(self, namespace, expected_size="10Gi"):
    """Verify persistence configuration in ClickHouseInstallation."""

    chi_info = get_chi_info(namespace=namespace)
    assert chi_info is not None, "ClickHouseInstallation not found"

    volume_claim_templates = (
        chi_info.get("spec", {}).get("templates", {}).get("volumeClaimTemplates", [])
    )
    assert (
        len(volume_claim_templates) > 0
    ), "No volumeClaimTemplates found in ClickHouseInstallation"

    data_template = None
    for template in volume_claim_templates:
        if "data" in template.get("name", ""):
            data_template = template
            break

    assert data_template is not None, "Data volume claim template not found"
    storage_size = (
        data_template.get("spec", {})
        .get("resources", {})
        .get("requests", {})
        .get("storage")
    )
    assert (
        storage_size == expected_size
    ), f"Expected storage size {expected_size}, got {storage_size}"

    note(f"Persistence configuration verified: {expected_size} storage")


@TestStep(When)
def get_keeper_pods(self, namespace):
    """Get only Keeper pods (excluding operator pods) from the specified namespace."""

    pods = kubernetes.get_pods(namespace=namespace)
    return [p for p in pods if p.startswith("keeper-") and "operator" not in p]


@TestStep(Then)
def verify_keeper_pod_count(self, namespace, expected_count):
    """Verify the number of Keeper pods matches expected count.
    
    Args:
        namespace: Kubernetes namespace
        expected_count: Expected number of Keeper pods
        
    Returns:
        Number of Keeper pods found
    """
    keeper_pods = run(
        cmd=f"kubectl get pods -n {namespace} -l clickhouse-keeper.altinity.com/app=chop -o jsonpath='{{.items[*].metadata.name}}'"
    )
    keeper_pod_count = len(keeper_pods.stdout.split()) if keeper_pods.stdout else 0
    
    assert keeper_pod_count == expected_count, \
        f"Expected {expected_count} Keeper pods, got {keeper_pod_count}"
    
    note(f"✓ Keeper pods: {keeper_pod_count}/{expected_count}")
    return keeper_pod_count


@TestStep(When)
def verify_keeper_pods_running(self, namespace, expected_count=None):
    """Verify that Keeper pods are running and ready."""

    keeper_pods = get_keeper_pods(namespace=namespace)
    
    if expected_count is not None:
        assert len(keeper_pods) == expected_count, f"Expected {expected_count} Keeper pods, got {len(keeper_pods)}"
    
    for pod in keeper_pods:
        if not kubernetes.check_status(pod_name=pod, namespace=namespace, status="Running"):
            raise AssertionError(f"Keeper pod {pod} is not running")
    
    note(f"Keeper pods running: {keeper_pods}")
    return keeper_pods


@TestStep(Then)
def verify_pods_image(self, namespace, expected_image_tag, pod_names=None):
    """Verify that ClickHouse pods are running with the expected image tag.
    
    Args:
        namespace: Kubernetes namespace
        expected_image_tag: Expected image tag string
        pod_names: Optional list of pod names. If None, gets all ClickHouse pods
    """
    
    if pod_names is None:
        pod_names = get_clickhouse_pods(namespace=namespace)
    
    assert len(pod_names) > 0, "No ClickHouse pods found"
    
    for pod in pod_names:
        image = kubernetes.get_pod_image(namespace=namespace, pod_name=pod)
        assert expected_image_tag in image, (
            f"Expected image tag '{expected_image_tag}' in pod {pod}, got {image}"
        )
        note(f"Pod {pod} is running with correct image: {image}")
    
    note(f"All {len(pod_names)} pods verified with image tag: {expected_image_tag}")


@TestStep(Then)
def verify_user_connection(self, namespace, user, password, pod_name=None):
    """Verify that a user can connect to ClickHouse with given credentials.
    
    Args:
        namespace: Kubernetes namespace
        user: Username to test
        password: Password for the user
        pod_name: Optional pod name. If None, uses first ClickHouse pod
    """
    
    if pod_name is None:
        clickhouse_pods = get_clickhouse_pods(namespace=namespace)
        if not clickhouse_pods:
            raise AssertionError("No ClickHouse pods found")
        pod_name = clickhouse_pods[0]
    
    result = test_clickhouse_connection(
        namespace=namespace,
        pod_name=pod_name,
        user=user,
        password=password
    )
    
    assert result, f"Failed to connect to ClickHouse with user '{user}'"
    note(f"Successfully connected with user: {user}")
    
    return result


@TestStep(Then)
def verify_clickhouse_pod_count(self, namespace, expected_count):
    """Verify the number of ClickHouse pods matches expected count.
    
    Args:
        namespace: Kubernetes namespace
        expected_count: Expected number of ClickHouse pods
    """
    clickhouse_pods = get_clickhouse_pods(namespace=namespace)
    actual_count = len(clickhouse_pods)
    
    assert actual_count == expected_count, \
        f"Expected {expected_count} ClickHouse pods, got {actual_count}"
    
    note(f"✓ ClickHouse pods: {actual_count}/{expected_count}")
    return clickhouse_pods


@TestStep(Then)
def verify_users_configuration(self, namespace, default_user_config=None, users_config=None):
    """Verify user configuration and connectivity for default and additional users.
    
    Args:
        namespace: Kubernetes namespace
        default_user_config: Dict with default user configuration (must have 'password' key)
        users_config: List of dicts with user configurations (each must have 'name' and 'password')
    """
    clickhouse_pods = get_clickhouse_pods(namespace=namespace)
    if not clickhouse_pods:
        note("No ClickHouse pods found, skipping user verification")
        return
    
    pod_name = clickhouse_pods[0]
    
    # Test default user
    if default_user_config and 'password' in default_user_config:
        password = default_user_config['password']
        result = test_clickhouse_connection(
            namespace=namespace,
            pod_name=pod_name,
            user="default",
            password=password
        )
        assert result, f"Failed to connect with default user"
        note(f"✓ Default user connection successful")
    
    # Test additional users
    if users_config:
        for user_config in users_config:
            user_name = user_config.get('name')
            if user_name and 'password' in user_config:
                password = user_config['password']
                result = test_clickhouse_connection(
                    namespace=namespace,
                    pod_name=pod_name,
                    user=user_name,
                    password=password
                )
                assert result, f"Failed to connect with user {user_name}"
                note(f"✓ User '{user_name}' connection successful")
            elif user_name:
                note(f"⊘ User '{user_name}' has hashed password, skipping connection test")


@TestStep(Then)
def verify_image_tag(self, namespace, expected_tag):
    """Verify all ClickHouse pods are running with expected image tag.
    
    Args:
        namespace: Kubernetes namespace
        expected_tag: Expected image tag
    """
    clickhouse_pods = get_clickhouse_pods(namespace=namespace)
    
    for pod in clickhouse_pods:
        import tests.steps.kubernetes as kubernetes
        image = kubernetes.get_pod_image(namespace=namespace, pod_name=pod)
        assert expected_tag in image, \
            f"Expected image tag {expected_tag}, got {image}"
    
    note(f"✓ Image tag: {expected_tag}")
