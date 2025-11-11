from tests.steps.system import *
import json
import time
import tests.steps.kubernetes as kubernetes


@TestStep(When)
def get_version(self, namespace, pod_name, user="default", password=""):
    """Get ClickHouse version from the specified pod."""
    auth_args = f"-u {user}" if user else ""
    if password:
        auth_args += f" --password {password}"

    version = run(
        cmd=f"kubectl exec -n {namespace} {pod_name} "
        f"-- clickhouse-client {auth_args} -q 'SELECT version()'"
    )
    return version.stdout.strip()


@TestStep(When)
def execute_clickhouse_query(self, namespace, pod_name, query, user="default", password="", check=True):
    """Execute a ClickHouse query on a specific pod."""
    auth_args = f"-u {user}" if user else ""
    if password:
        auth_args += f" --password {password}"
    
    escaped_query = query.replace("'", "'\\''")
    
    result = run(
        cmd=f"kubectl exec -n {namespace} {pod_name} "
        f"-- clickhouse-client {auth_args} -q '{escaped_query}'",
        check=check,
    )
    return result


@TestStep(When)
def test_clickhouse_connection(self, namespace, pod_name, user, password):
    """Test ClickHouse connection with given credentials."""
    try:
        result = run(
            cmd=f"kubectl exec -n {namespace} {pod_name} "
            f"-- clickhouse-client -u {user} --password {password} "
            f"-q 'SELECT 1'",
            check=False,
        )
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
    """Get ClickHouse pods (excluding operator pods)."""
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
    """Get Keeper pods (excluding operator pods)."""
    pods = kubernetes.get_pods(namespace=namespace)
    return [p for p in pods if p.startswith("keeper-") and "operator" not in p]


@TestStep(When)
def get_chk_name(self, namespace):
    """Get the name of the ClickHouseKeeperInstallation resource."""
    chk_info = run(cmd=f"kubectl get chk -n {namespace} -o json", check=False)
    if chk_info.returncode != 0:
        return None
    
    chk_info = json.loads(chk_info.stdout)

    if chk_info.get("items"):
        return chk_info["items"][0]["metadata"]["name"]
    return None


@TestStep(When)
def get_chk_info(self, namespace):
    """Get the full ClickHouseKeeperInstallation resource information."""
    chk_info = run(cmd=f"kubectl get chk -n {namespace} -o json", check=False)
    if chk_info.returncode != 0:
        return None
    
    chk_info = json.loads(chk_info.stdout)

    if chk_info.get("items"):
        return chk_info["items"][0]
    return None


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
    """Verify that ClickHouse pods are running with the expected image tag."""
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
    """Verify that a user can connect to ClickHouse with given credentials."""
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
    """Verify that the expected number of ClickHouse pods are running."""
    clickhouse_pods = get_clickhouse_pods(namespace=namespace)
    assert len(clickhouse_pods) == expected_count, \
        f"Expected {expected_count} ClickHouse pods, got {len(clickhouse_pods)}"
    note(f"✓ ClickHouse pod count: {expected_count}")


@TestStep(Then)
def verify_keeper_pod_count(self, namespace, expected_count):
    """Verify that the expected number of Keeper pods are running."""
    keeper_pods = get_keeper_pods(namespace=namespace)
    assert len(keeper_pods) == expected_count, \
        f"Expected {expected_count} Keeper pods, got {len(keeper_pods)}"
    note(f"✓ Keeper pod count: {expected_count}")


@TestStep(When)
def is_clickhouse_resource(self, resource_name):
    """Check if a resource name belongs to a ClickHouse instance."""
    if "operator" in resource_name:
        return False
    return "chi-" in resource_name or resource_name.startswith("clickhouse-")


@TestStep(Then)
def verify_clickhouse_pvc_size(self, namespace, expected_size):
    """Verify that ClickHouse data PVCs have the expected size."""
    pvcs = kubernetes.get_pvcs(namespace=namespace)
    
    clickhouse_data_pvcs = [pvc for pvc in pvcs if 'data' in pvc and is_clickhouse_resource(resource_name=pvc)]
    
    assert len(clickhouse_data_pvcs) > 0, "No ClickHouse data PVCs found"
    
    for pvc in clickhouse_data_pvcs:
        pvc_info = kubernetes.get_pvc_info(namespace=namespace, pvc_name=pvc)
        actual_size = pvc_info.get("spec", {}).get("resources", {}).get("requests", {}).get("storage")
        
        assert actual_size == expected_size, \
            f"Expected PVC size {expected_size}, got {actual_size} for {pvc}"
    
    note(f"✓ All {len(clickhouse_data_pvcs)} data PVCs verified: {expected_size}")


@TestStep(Then)
def verify_image_tag(self, namespace, expected_tag):
    """Verify that ClickHouse pods are using the expected image tag."""
    verify_pods_image(namespace=namespace, expected_image_tag=expected_tag)
    note(f"✓ Image tag verified: {expected_tag}")


@TestStep(Then)
def verify_pod_annotations(self, namespace, expected_annotations):
    """Verify that ClickHouse pods have expected annotations."""
    clickhouse_pods = get_clickhouse_pods(namespace=namespace)
    assert len(clickhouse_pods) > 0, "No ClickHouse pods found"
    
    for pod in clickhouse_pods:
        pod_info = kubernetes.get_pod_info(namespace=namespace, pod_name=pod)
        actual_annotations = pod_info.get("metadata", {}).get("annotations", {})
        
        for key, value in expected_annotations.items():
            assert key in actual_annotations, \
                f"Annotation '{key}' not found in pod {pod}"
            assert actual_annotations[key] == value, \
                f"Expected annotation '{key}={value}', got '{actual_annotations[key]}' in pod {pod}"
    
    note(f"✓ Pod annotations verified on {len(clickhouse_pods)} pods")


@TestStep(Then)
def verify_pod_labels(self, namespace, expected_labels):
    """Verify that ClickHouse pods have expected labels."""
    clickhouse_pods = get_clickhouse_pods(namespace=namespace)
    assert len(clickhouse_pods) > 0, "No ClickHouse pods found"
    
    for pod in clickhouse_pods:
        pod_info = kubernetes.get_pod_info(namespace=namespace, pod_name=pod)
        actual_labels = pod_info.get("metadata", {}).get("labels", {})
        
        for key, value in expected_labels.items():
            assert key in actual_labels, \
                f"Label '{key}' not found in pod {pod}"
            assert actual_labels[key] == value, \
                f"Expected label '{key}={value}', got '{actual_labels[key]}' in pod {pod}"
    
    note(f"✓ Pod labels verified on {len(clickhouse_pods)} pods")


@TestStep(Then)
def verify_service_annotations(self, namespace, expected_annotations):
    """Verify that ClickHouse services have expected annotations."""
    services = kubernetes.get_services(namespace=namespace)
    clickhouse_services = [svc for svc in services if is_clickhouse_resource(resource_name=svc)]
    
    assert len(clickhouse_services) > 0, "No ClickHouse services found"
    
    services_with_annotations = []
    for service in clickhouse_services:
        service_info = kubernetes.get_service_info(namespace=namespace, service_name=service)
        actual_annotations = service_info.get("metadata", {}).get("annotations", {})
        
        has_expected_annotation = any(key in actual_annotations for key in expected_annotations.keys())
        
        if has_expected_annotation:
            services_with_annotations.append(service)
            for key, value in expected_annotations.items():
                assert key in actual_annotations, \
                    f"Annotation '{key}' not found in service {service}"
                assert actual_annotations[key] == value, \
                    f"Expected annotation '{key}={value}', got '{actual_annotations[key]}' in service {service}"
    
    assert len(services_with_annotations) > 0, \
        f"No services found with expected annotations. Expected: {list(expected_annotations.keys())}, Services checked: {clickhouse_services}"
    
    note(f"✓ Service annotations verified on {len(services_with_annotations)} service(s)")


@TestStep(Then)
def verify_service_labels(self, namespace, expected_labels):
    """Verify that ClickHouse services have expected labels."""
    services = kubernetes.get_services(namespace=namespace)
    clickhouse_services = [svc for svc in services if is_clickhouse_resource(resource_name=svc)]
    
    assert len(clickhouse_services) > 0, "No ClickHouse services found"
    
    services_with_labels = []
    for service in clickhouse_services:
        service_info = kubernetes.get_service_info(namespace=namespace, service_name=service)
        actual_labels = service_info.get("metadata", {}).get("labels", {})
        
        has_expected_label = any(key in actual_labels for key in expected_labels.keys())
        
        if has_expected_label:
            services_with_labels.append(service)
            for key, value in expected_labels.items():
                assert key in actual_labels, \
                    f"Label '{key}' not found in service {service}"
                assert actual_labels[key] == value, \
                    f"Expected label '{key}={value}', got '{actual_labels[key]}' in service {service}"
    
    assert len(services_with_labels) > 0, \
        f"No services found with expected labels. Expected: {list(expected_labels.keys())}, Services checked: {clickhouse_services}"
    
    note(f"✓ Service labels verified on {len(services_with_labels)} service(s)")


@TestStep(Then)
def verify_log_persistence(self, namespace, expected_log_size):
    """Verify that ClickHouse log PVCs have the expected size."""
    pvcs = kubernetes.get_pvcs(namespace=namespace)
    log_pvcs = [pvc for pvc in pvcs if 'log' in pvc and is_clickhouse_resource(resource_name=pvc)]
    
    assert len(log_pvcs) > 0, "No ClickHouse log PVCs found"
    
    for pvc in log_pvcs:
        pvc_info = kubernetes.get_pvc_info(namespace=namespace, pvc_name=pvc)
        actual_size = pvc_info.get("spec", {}).get("resources", {}).get("requests", {}).get("storage")
        
        assert actual_size == expected_log_size, \
            f"Expected log PVC size {expected_log_size}, got {actual_size} for {pvc}"
    
    note(f"✓ All {len(log_pvcs)} log PVCs verified: {expected_log_size}")


@TestStep(Then)
def verify_extra_config(self, namespace, expected_config_keys):
    """Verify that extraConfig is present in CHI."""
    chi_info = get_chi_info(namespace=namespace)
    assert chi_info is not None, "ClickHouseInstallation not found"
    
    settings = chi_info.get("spec", {}).get("configuration", {}).get("settings", {})
    files = chi_info.get("spec", {}).get("configuration", {}).get("files", {})
    
    for key in expected_config_keys:
        found = False
        if key in settings:
            found = True
        elif any(key in file_content for file_content in files.values()):
            found = True
        
        assert found, f"ExtraConfig key '{key}' not found in settings or files"
        note(f"✓ ExtraConfig key found: {key}")
    
    note(f"✓ ExtraConfig verified: {len(expected_config_keys)} keys")


@TestStep(Then)
def verify_keeper_storage(self, namespace, expected_storage_size):
    """Verify that Keeper storage volumes have the expected size."""
    pvcs = kubernetes.get_pvcs(namespace=namespace)
    keeper_pvcs = [pvc for pvc in pvcs if pvc.startswith("keeper-") or "-keeper-" in pvc]
    
    assert len(keeper_pvcs) > 0, f"No Keeper PVCs found in namespace {namespace}"
    
    for pvc in keeper_pvcs:
        pvc_info = kubernetes.get_pvc_info(namespace=namespace, pvc_name=pvc)
        actual_size = pvc_info.get("spec", {}).get("resources", {}).get("requests", {}).get("storage")
        
        assert actual_size == expected_storage_size, \
            f"Expected Keeper PVC size {expected_storage_size}, got {actual_size} for {pvc}"
    
    note(f"✓ Keeper storage verified: {len(keeper_pvcs)} PVCs with {expected_storage_size}")


@TestStep(Then)
def verify_keeper_annotations(self, namespace, expected_annotations):
    """Verify that Keeper pods have expected annotations."""
    keeper_pods = get_keeper_pods(namespace=namespace)
    assert len(keeper_pods) > 0, "No Keeper pods found"
    
    for pod in keeper_pods:
        pod_info = kubernetes.get_pod_info(namespace=namespace, pod_name=pod)
        actual_annotations = pod_info.get("metadata", {}).get("annotations", {})
        
        for key, value in expected_annotations.items():
            assert key in actual_annotations, \
                f"Annotation '{key}' not found in Keeper pod {pod}"
            assert actual_annotations[key] == value, \
                f"Expected annotation '{key}={value}', got '{actual_annotations[key]}' in Keeper pod {pod}"
    
    note(f"✓ Keeper annotations verified on {len(keeper_pods)} pods")


@TestStep(Then)
def verify_keeper_resources(self, namespace, expected_resources):
    """Verify that Keeper pods have expected resource requests and limits."""
    keeper_pods = get_keeper_pods(namespace=namespace)
    assert len(keeper_pods) > 0, "No Keeper pods found"
    
    for pod in keeper_pods:
        pod_info = kubernetes.get_pod_info(namespace=namespace, pod_name=pod)
        containers = pod_info.get("spec", {}).get("containers", [])
        
        assert len(containers) > 0, f"No containers found in Keeper pod {pod}"
        
        container = containers[0]
        actual_resources = container.get("resources", {})
        
        if 'requests' in expected_resources:
            assert 'requests' in actual_resources, f"No resource requests in Keeper pod {pod}"
            for key, value in expected_resources['requests'].items():
                actual_value = actual_resources['requests'].get(key)
                assert actual_value == value, \
                    f"Keeper {pod} request {key}: expected={value}, actual={actual_value}"
        
        if 'limits' in expected_resources:
            assert 'limits' in actual_resources, f"No resource limits in Keeper pod {pod}"
            for key, value in expected_resources['limits'].items():
                actual_value = actual_resources['limits'].get(key)
                assert actual_value == value, \
                    f"Keeper {pod} limit {key}: expected={value}, actual={actual_value}"
    
    note(f"✓ Keeper resources verified on {len(keeper_pods)} pods")
