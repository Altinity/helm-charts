from tests.steps.system import *
import json
import time


@TestStep(When)
def get_version(self, namespace, pod_name):
    """Get ClickHouse version from the specified pod."""

    version = run(cmd=f"kubectl exec -n {namespace} {pod_name} "
        "-- clickhouse-client -q 'SELECT version()'"
    )
    return version.stdout.strip()


@TestStep(When)
def test_clickhouse_connection(self, namespace, pod_name, user, password):
    """Test ClickHouse connection with given credentials."""
    
    try:
        result = run(cmd=f"kubectl exec -n {namespace} {pod_name} "
                    f"-- clickhouse-client -u {user} --password {password} "
                    f"-q 'SELECT 1'", check=False)
        return result.returncode == 0
    except:
        return False


@TestStep(When)
def get_chi_name(self, namespace):
    """Get the name of the ClickHouseInstallation resource."""
    
    chi_info = run(cmd=f"kubectl get chi -n {namespace} -o json")
    chi_info = json.loads(chi_info.stdout)
    
    if chi_info["items"]:
        return chi_info["items"][0]["metadata"]["name"]
    return None


@TestStep(When)
def get_chi_info(self, namespace):
    """Get the full ClickHouseInstallation resource information."""
    
    chi_info = run(cmd=f"kubectl get chi -n {namespace} -o json")
    chi_info = json.loads(chi_info.stdout)
    
    if chi_info["items"]:
        return chi_info["items"][0]
    return None


@TestStep(When)
def get_clickhouse_pods(self, namespace):
    """Get only ClickHouse pods (excluding operator pods) from the specified namespace."""
    
    from tests.steps.kubernetes import get_pods
    pods = get_pods(namespace=namespace)
    return [p for p in pods if "chi-" in p and "operator" not in p]


@TestStep(When)
def wait_for_clickhouse_pods_running(self, namespace, expected_count=None, timeout=300):
    """Wait for ClickHouse pods to be running and ready."""
    
    start_time = time.time()
    while True:
        clickhouse_pods = get_clickhouse_pods(namespace=namespace)
        
        if expected_count and len(clickhouse_pods) != expected_count:
            if time.time() - start_time > timeout:
                raise TimeoutError(f"Timeout waiting for {expected_count} ClickHouse pods, got {len(clickhouse_pods)}")
            time.sleep(5)
            continue
        
        if len(clickhouse_pods) == 0:
            if time.time() - start_time > timeout:
                raise TimeoutError("Timeout waiting for ClickHouse pods to be created")
            time.sleep(5)
            continue
        
        all_running = True
        from tests.steps.kubernetes import check_status
        for pod in clickhouse_pods:
            if not check_status(pod_name=pod, namespace=namespace, status="Running"):
                all_running = False
                break
        
        if all_running:
            return clickhouse_pods
            
        if time.time() - start_time > timeout:
            pod_statuses = []
            for pod in clickhouse_pods:
                status = "Running" if check_status(pod_name=pod, namespace=namespace, status="Running") else "Not Running"
                pod_statuses.append(f"{pod}: {status}")
            raise TimeoutError(f"Timeout waiting for ClickHouse pods to be running. Pod statuses: {pod_statuses}")
            
        time.sleep(10)


@TestStep(When)
def verify_clickhouse_version(self, namespace, expected_version, pod_name=None):
    """Verify ClickHouse version matches expected version."""
    
    if pod_name is None:
        clickhouse_pods = get_clickhouse_pods(namespace=namespace)
        if not clickhouse_pods:
            raise AssertionError("No ClickHouse pods found")
        pod_name = clickhouse_pods[0]
    
    version = get_version(namespace=namespace, pod_name=pod_name)
    note(f"ClickHouse version: {version}")
    
    assert version == expected_version, f"Expected version {expected_version}, got {version}"


@TestStep(When)
def verify_custom_name_in_resources(self, namespace, custom_name):
    """Verify that custom name appears in ClickHouse resources."""
    
    chi_name = get_chi_name(namespace=namespace)
    assert custom_name in chi_name, f"Custom name '{custom_name}' not found in CHI name: {chi_name}"
    
    clickhouse_pods = get_clickhouse_pods(namespace=namespace)
    assert len(clickhouse_pods) > 0, "No ClickHouse pods found"
    note(f"ClickHouse pods created: {clickhouse_pods}")


@TestStep(When)
def verify_persistence_configuration(self, namespace, expected_size="10Gi"):
    """Verify persistence configuration in ClickHouseInstallation."""
    
    chi_info = get_chi_info(namespace=namespace)
    assert chi_info is not None, "ClickHouseInstallation not found"
    
    volume_claim_templates = chi_info.get("spec", {}).get("templates", {}).get("volumeClaimTemplates", [])
    assert len(volume_claim_templates) > 0, "No volumeClaimTemplates found in ClickHouseInstallation"
    
    data_template = None
    for template in volume_claim_templates:
        if "data" in template.get("name", ""):
            data_template = template
            break
    
    assert data_template is not None, "Data volume claim template not found"
    storage_size = data_template.get("spec", {}).get("resources", {}).get("requests", {}).get("storage")
    assert storage_size == expected_size, f"Expected storage size {expected_size}, got {storage_size}"
    
    note(f"✅ Persistence configuration verified: {expected_size} storage")

