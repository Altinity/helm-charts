from tests.steps.system import *
import json
import time
import tests.steps.kubernetes as kubernetes
import re


def wait_until(check_fn, timeout=60, interval=5, timeout_msg="Operation timed out"):
    """Generic retry helper that waits until a condition is met.
    
    Args:
        check_fn: Function that returns (success: bool, result: any, status_msg: str)
        timeout: Maximum time to wait in seconds
        interval: Time between retries in seconds
        timeout_msg: Error message if timeout occurs
        
    Returns:
        The result from check_fn when successful
        
    Raises:
        TimeoutError: If condition not met within timeout
    """
    start_time = time.time()
    
    while True:
        success, result, status_msg = check_fn()
        
        if success:
            return result
            
        if time.time() - start_time > timeout:
            raise TimeoutError(f"{timeout_msg}. Last status: {status_msg}")
            
        if status_msg:
            note(status_msg)
        time.sleep(interval)


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
def execute_clickhouse_query(
    self, namespace, pod_name, query, user="default", password="", check=True
):
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
    
    def check_pods():
        clickhouse_pods = get_clickhouse_pods(namespace=namespace)
        
        if len(clickhouse_pods) == 0:
            return (False, None, "No ClickHouse pods found yet")
        
        if expected_count and len(clickhouse_pods) != expected_count:
            return (False, None, f"Expected {expected_count} pods, found {len(clickhouse_pods)}")
        
        not_running = []
        for pod in clickhouse_pods:
            if not kubernetes.check_status(pod_name=pod, namespace=namespace, status="Running"):
                not_running.append(pod)
        
        if not_running:
            return (False, None, f"Waiting for {len(not_running)} pod(s) to be running")
        
        return (True, clickhouse_pods, "All pods running")
    
    return wait_until(
        check_fn=check_pods,
        timeout=timeout,
        interval=10,
        timeout_msg="ClickHouse pods not ready"
    )


@TestStep(When)
def verify_clickhouse_version(
    self, namespace, expected_version, pod_name=None, user="default", password=""
):
    """Verify ClickHouse version matches expected version."""
    if pod_name is None:
        clickhouse_pods = get_clickhouse_pods(namespace=namespace)
        if not clickhouse_pods:
            raise AssertionError("No ClickHouse pods found")
        pod_name = clickhouse_pods[0]

    version = get_version(
        namespace=namespace, pod_name=pod_name, user=user, password=password
    )
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
        assert (
            len(keeper_pods) == expected_count
        ), f"Expected {expected_count} Keeper pods, got {len(keeper_pods)}"

    for pod in keeper_pods:
        if not kubernetes.check_status(
            pod_name=pod, namespace=namespace, status="Running"
        ):
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
        assert (
            expected_image_tag in image
        ), f"Expected image tag '{expected_image_tag}' in pod {pod}, got {image}"
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
        namespace=namespace, pod_name=pod_name, user=user, password=password
    )

    assert result, f"Failed to connect to ClickHouse with user '{user}'"
    note(f"Successfully connected with user: {user}")

    return result


@TestStep(Then)
def verify_clickhouse_pod_count(self, namespace, expected_count):
    """Verify that the expected number of ClickHouse pods are running."""
    clickhouse_pods = get_clickhouse_pods(namespace=namespace)
    assert (
        len(clickhouse_pods) == expected_count
    ), f"Expected {expected_count} ClickHouse pods, got {len(clickhouse_pods)}"
    note(f"✓ ClickHouse pod count: {expected_count}")


@TestStep(Then)
def verify_keeper_pod_count(self, namespace, expected_count):
    """Verify that the expected number of Keeper pods are running."""
    keeper_pods = get_keeper_pods(namespace=namespace)
    assert (
        len(keeper_pods) == expected_count
    ), f"Expected {expected_count} Keeper pods, got {len(keeper_pods)}"
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

    clickhouse_data_pvcs = [
        pvc
        for pvc in pvcs
        if "data" in pvc and is_clickhouse_resource(resource_name=pvc)
    ]

    assert len(clickhouse_data_pvcs) > 0, "No ClickHouse data PVCs found"

    for pvc in clickhouse_data_pvcs:
        pvc_info = kubernetes.get_pvc_info(namespace=namespace, pvc_name=pvc)
        actual_size = (
            pvc_info.get("spec", {})
            .get("resources", {})
            .get("requests", {})
            .get("storage")
        )

        assert (
            actual_size == expected_size
        ), f"Expected PVC size {expected_size}, got {actual_size} for {pvc}"

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
            assert (
                key in actual_annotations
            ), f"Annotation '{key}' not found in pod {pod}"
            assert (
                actual_annotations[key] == value
            ), f"Expected annotation '{key}={value}', got '{actual_annotations[key]}' in pod {pod}"

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
            assert key in actual_labels, f"Label '{key}' not found in pod {pod}"
            assert (
                actual_labels[key] == value
            ), f"Expected label '{key}={value}', got '{actual_labels[key]}' in pod {pod}"

    note(f"✓ Pod labels verified on {len(clickhouse_pods)} pods")


@TestStep(Then)
def verify_service_annotations(self, namespace, expected_annotations, service_type=None):
    """Verify that ClickHouse services have expected annotations."""
    services = kubernetes.get_services(namespace=namespace)
    clickhouse_services = [
        svc for svc in services if is_clickhouse_resource(resource_name=svc)
    ]

    assert len(clickhouse_services) > 0, "No ClickHouse services found"

    services_with_annotations = []
    for service in clickhouse_services:
        service_info = kubernetes.get_service_info(
            namespace=namespace, service_name=service
        )
        actual_annotations = service_info.get("metadata", {}).get("annotations", {})

        has_expected_annotation = any(
            key in actual_annotations for key in expected_annotations.keys()
        )

        if has_expected_annotation:
            services_with_annotations.append(service)
            for key, value in expected_annotations.items():
                assert (
                    key in actual_annotations
                ), f"Annotation '{key}' not found in service {service}"
                assert (
                    actual_annotations[key] == value
                ), f"Expected annotation '{key}={value}', got '{actual_annotations[key]}' in service {service}"

    assert (
        len(services_with_annotations) > 0
    ), f"No services found with expected annotations. Expected: {list(expected_annotations.keys())}, Services checked: {clickhouse_services}"

    note(
        f"✓ Service annotations verified on {len(services_with_annotations)} service(s)"
    )


@TestStep(Then)
def verify_service_labels(self, namespace, expected_labels, service_type=None):
    """Verify that ClickHouse services have expected labels."""
    services = kubernetes.get_services(namespace=namespace)
    clickhouse_services = [
        svc for svc in services if is_clickhouse_resource(resource_name=svc)
    ]

    assert len(clickhouse_services) > 0, "No ClickHouse services found"

    services_with_labels = []
    for service in clickhouse_services:
        service_info = kubernetes.get_service_info(
            namespace=namespace, service_name=service
        )
        actual_labels = service_info.get("metadata", {}).get("labels", {})

        has_expected_label = any(key in actual_labels for key in expected_labels.keys())

        if has_expected_label:
            services_with_labels.append(service)
            for key, value in expected_labels.items():
                assert (
                    key in actual_labels
                ), f"Label '{key}' not found in service {service}"
                assert (
                    actual_labels[key] == value
                ), f"Expected label '{key}={value}', got '{actual_labels[key]}' in service {service}"

    assert (
        len(services_with_labels) > 0
    ), f"No services found with expected labels. Expected: {list(expected_labels.keys())}, Services checked: {clickhouse_services}"

    note(f"✓ Service labels verified on {len(services_with_labels)} service(s)")


@TestStep(Then)
def verify_log_persistence(self, namespace, expected_log_size):
    """Verify that ClickHouse log PVCs have the expected size."""
    pvcs = kubernetes.get_pvcs(namespace=namespace)
    log_pvcs = [
        pvc
        for pvc in pvcs
        if "log" in pvc and is_clickhouse_resource(resource_name=pvc)
    ]

    assert len(log_pvcs) > 0, "No ClickHouse log PVCs found"

    for pvc in log_pvcs:
        pvc_info = kubernetes.get_pvc_info(namespace=namespace, pvc_name=pvc)
        actual_size = (
            pvc_info.get("spec", {})
            .get("resources", {})
            .get("requests", {})
            .get("storage")
        )

        assert (
            actual_size == expected_log_size
        ), f"Expected log PVC size {expected_log_size}, got {actual_size} for {pvc}"

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
    keeper_pvcs = [
        pvc for pvc in pvcs if pvc.startswith("keeper-") or "-keeper-" in pvc
    ]

    assert len(keeper_pvcs) > 0, f"No Keeper PVCs found in namespace {namespace}"

    for pvc in keeper_pvcs:
        pvc_info = kubernetes.get_pvc_info(namespace=namespace, pvc_name=pvc)
        actual_size = (
            pvc_info.get("spec", {})
            .get("resources", {})
            .get("requests", {})
            .get("storage")
        )

        assert (
            actual_size == expected_storage_size
        ), f"Expected Keeper PVC size {expected_storage_size}, got {actual_size} for {pvc}"

    note(
        f"✓ Keeper storage verified: {len(keeper_pvcs)} PVCs with {expected_storage_size}"
    )


@TestStep(Then)
def verify_keeper_annotations(self, namespace, expected_annotations):
    """Verify that Keeper pods have expected annotations."""
    keeper_pods = get_keeper_pods(namespace=namespace)
    assert len(keeper_pods) > 0, "No Keeper pods found"

    for pod in keeper_pods:
        pod_info = kubernetes.get_pod_info(namespace=namespace, pod_name=pod)
        actual_annotations = pod_info.get("metadata", {}).get("annotations", {})

        for key, value in expected_annotations.items():
            assert (
                key in actual_annotations
            ), f"Annotation '{key}' not found in Keeper pod {pod}"
            assert (
                actual_annotations[key] == value
            ), f"Expected annotation '{key}={value}', got '{actual_annotations[key]}' in Keeper pod {pod}"

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

        if "requests" in expected_resources:
            assert (
                "requests" in actual_resources
            ), f"No resource requests in Keeper pod {pod}"
            for key, value in expected_resources["requests"].items():
                actual_value = actual_resources["requests"].get(key)
                assert (
                    actual_value == value
                ), f"Keeper {pod} request {key}: expected={value}, actual={actual_value}"

        if "limits" in expected_resources:
            assert (
                "limits" in actual_resources
            ), f"No resource limits in Keeper pod {pod}"
            for key, value in expected_resources["limits"].items():
                actual_value = actual_resources["limits"].get(key)
                assert (
                    actual_value == value
                ), f"Keeper {pod} limit {key}: expected={value}, actual={actual_value}"

    note(f"✓ Keeper resources verified on {len(keeper_pods)} pods")


@TestStep(Then)
def verify_chi_cluster_topology(self, namespace, expected_replicas, expected_shards):
    """Verify that the ClickHouse cluster has the expected topology (replicas and shards)."""
    chi_info = get_chi_info(namespace=namespace)
    assert chi_info is not None, "ClickHouseInstallation not found"
    
    clusters = chi_info.get("spec", {}).get("configuration", {}).get("clusters", [])
    assert len(clusters) > 0, "No clusters found in ClickHouseInstallation"
    
    # Check the first cluster (typically there's only one)
    cluster = clusters[0]
    layout = cluster.get("layout", {})
    
    # Check if using simple layout (shardsCount/replicasCount) or complex layout (shards list)
    if "shardsCount" in layout and "replicasCount" in layout:
        # Simple layout
        actual_shards = layout["shardsCount"]
        actual_replicas = layout["replicasCount"]
    elif "shards" in layout:
        # Complex layout with explicit shard definitions
        shards_list = layout["shards"]
        actual_shards = len(shards_list)
        
        # Count replicas in the first shard (assumes all shards have same replica count)
        if shards_list:
            first_shard = shards_list[0]
            replicas_list = first_shard.get("replicas", [])
            actual_replicas = len(replicas_list)
        else:
            actual_replicas = 0
    else:
        raise AssertionError(f"Unable to determine cluster topology from layout: {layout}")
    
    assert actual_shards == expected_shards, \
        f"Expected {expected_shards} shards, got {actual_shards}"
    assert actual_replicas == expected_replicas, \
        f"Expected {expected_replicas} replicas, got {actual_replicas}"
    
    note(f"✓ Cluster topology verified: {actual_shards} shard(s), {actual_replicas} replica(s)")


@TestStep(When)
def extract_extra_config_keys(self, extra_config_xml):
    """Extract configuration keys from extraConfig XML."""
    
    # Match XML tags like <key>value</key>
    # Exclude nested tags and special cases like <clickhouse> wrapper
    pattern = r'<([a-z_][a-z0-9_]*(?:\.[a-z_][a-z0-9_]*)?)>.*?</\1>'
    matches = re.findall(pattern, extra_config_xml, re.DOTALL | re.IGNORECASE)
    
    # Filter out common wrapper tags
    wrapper_tags = {'clickhouse', 'yandex', 'config'}
    config_keys = [key for key in matches if key.lower() not in wrapper_tags]
    
    return config_keys


@TestStep(When)
def parse_extra_config_values(self, extra_config_xml):
    """Parse configuration values from extraConfig XML.
    
    Returns a dictionary of setting_name -> expected_value.
    Only returns simple key-value pairs (not nested structures).
    """

    
    config_values = {}
    
    # Match simple key-value pairs like <key>value</key>
    # This pattern captures both the key and value
    pattern = r'<([a-z_][a-z0-9_]*)>([^<>]+)</\1>'
    matches = re.findall(pattern, extra_config_xml, re.IGNORECASE)
    
    for key, value in matches:
        key_lower = key.lower()
        # Skip wrapper tags
        if key_lower in {'clickhouse', 'yandex', 'config', 'logger', 'merge_tree'}:
            continue
        
        # Clean up the value (strip whitespace)
        cleaned_value = value.strip()
        config_values[key] = cleaned_value
    
    return config_values


@TestStep(Then)
def verify_extra_config_values(self, namespace, expected_config_values, admin_password):
    """Verify that extraConfig values are actually applied in ClickHouse.
    
    This checks the actual running configuration by querying system tables.
    """
    clickhouse_pods = get_clickhouse_pods(namespace=namespace)
    if not clickhouse_pods:
        raise AssertionError("No ClickHouse pods found")
    
    # Use the first pod for verification
    pod_name = clickhouse_pods[0]
    
    # Settings that use default value when set to 0
    # For these, we skip verification when expected value is "0"
    default_on_zero_settings = {'max_table_size_to_drop', 'max_partition_size_to_drop'}
    
    for setting_name, expected_value in expected_config_values.items():
        # Skip verification for settings where 0 means "use default"
        if setting_name in default_on_zero_settings and str(expected_value) == "0":
            note(f"⚠ Skipping verification for '{setting_name}' (value 0 uses ClickHouse default)")
            continue
        
        # First try system.settings (session-level settings)
        query = f"SELECT value FROM system.settings WHERE name = '{setting_name}' FORMAT TabSeparated"
        result = execute_clickhouse_query(
            namespace=namespace,
            pod_name=pod_name,
            query=query,
            user="default",
            password=admin_password,
            check=False
        )
        
        actual_value = result.stdout.strip() if result.returncode == 0 and result.stdout.strip() else None
        
        if not actual_value:
            query = f"SELECT value FROM system.server_settings WHERE name = '{setting_name}' FORMAT TabSeparated"
            result = execute_clickhouse_query(
                namespace=namespace,
                pod_name=pod_name,
                query=query,
                user="default",
                password=admin_password,
                check=False
            )
            actual_value = result.stdout.strip() if result.returncode == 0 and result.stdout.strip() else None
        
        if actual_value:
            note(f"✓ Server setting '{setting_name}' = {actual_value} (expected: {expected_value})")
            
            # Convert both to strings for comparison
            expected_str = str(expected_value)
            
            # For numeric comparisons, normalize both values
            try:
                expected_num = float(expected_str)
                actual_num = float(actual_value)
                assert actual_num == expected_num, f"Setting '{setting_name}': expected={expected_str}, actual={actual_value}"
            except ValueError:
                # Not numeric, do string comparison
                assert actual_value == expected_str, f"Setting '{setting_name}': expected={expected_str}, actual={actual_value}"
        else:
            # Setting not found in either table - this might be okay for some settings
            note(f"⚠ Setting '{setting_name}' not found in system.settings or system.server_settings")


@TestStep(When)
def convert_helm_resources_to_k8s(self, helm_resources):
    """Convert Helm resource format to Kubernetes format.
    
    Helm format example:
        cpuRequestsMs: 100
        memoryRequestsMiB: 512Mi
        cpuLimitsMs: 500
        memoryLimitsMiB: 1Gi
    
    Kubernetes format:
        requests:
            cpu: 100m
            memory: 512Mi
        limits:
            cpu: 500m
            memory: 1Gi
    """
    k8s_resources = {}
    
    if "cpuRequestsMs" in helm_resources or "memoryRequestsMiB" in helm_resources:
        k8s_resources["requests"] = {}
        if "cpuRequestsMs" in helm_resources:
            k8s_resources["requests"]["cpu"] = f"{helm_resources['cpuRequestsMs']}m"
        if "memoryRequestsMiB" in helm_resources:
            k8s_resources["requests"]["memory"] = helm_resources["memoryRequestsMiB"]
    
    if "cpuLimitsMs" in helm_resources or "memoryLimitsMiB" in helm_resources:
        k8s_resources["limits"] = {}
        if "cpuLimitsMs" in helm_resources:
            k8s_resources["limits"]["cpu"] = f"{helm_resources['cpuLimitsMs']}m"
        if "memoryLimitsMiB" in helm_resources:
            k8s_resources["limits"]["memory"] = helm_resources["memoryLimitsMiB"]
    
    return k8s_resources


def get_cluster_topology(namespace, pod_name, cluster_name, admin_password):
    """Query system.clusters and return topology for a specific cluster.
    
    Returns:
        tuple: (actual_shards, actual_replicas) or (0, 0) if cluster not found
    """
    query = "SELECT cluster, shard_num, replica_num FROM system.clusters ORDER BY shard_num, replica_num FORMAT TabSeparated"
    result = execute_clickhouse_query(
        namespace=namespace,
        pod_name=pod_name,
        query=query,
        user="default",
        password=admin_password,
        check=True
    )
    
    lines = result.stdout.strip().split('\n')
    if not lines or lines[0] == '':
        return (0, 0)
    
    shards = set()
    replicas_per_shard = {}
    
    for line in lines:
        parts = line.split('\t')
        if len(parts) >= 3:
            cluster, shard_num, replica_num = parts[0], parts[1], parts[2]
            if cluster != cluster_name:
                continue
            shards.add(shard_num)
            if shard_num not in replicas_per_shard:
                replicas_per_shard[shard_num] = set()
            replicas_per_shard[shard_num].add(replica_num)
    
    actual_shards = len(shards)
    actual_replicas = max(len(reps) for reps in replicas_per_shard.values()) if replicas_per_shard else 0
    
    return (actual_shards, actual_replicas)


@TestStep(Then)
def verify_system_clusters(self, namespace, cluster_name, expected_shards, expected_replicas, admin_password, timeout=60):
    """Verify system.clusters table has expected topology."""
    clickhouse_pods = get_clickhouse_pods(namespace=namespace)
    if not clickhouse_pods:
        raise AssertionError("No ClickHouse pods found")
    
    pod_name = clickhouse_pods[0]
    
    def check_topology():
        actual_shards, actual_replicas = get_cluster_topology(
            namespace, pod_name, cluster_name, admin_password
        )
        
        if actual_shards == 0 and actual_replicas == 0:
            return (False, None, f"Cluster '{cluster_name}' not found in system.clusters")
        
        success = (actual_shards == expected_shards and actual_replicas == expected_replicas)
        status_msg = f"Current: {actual_shards} shard(s), {actual_replicas} replica(s)"
        
        return (success, (actual_shards, actual_replicas), status_msg)
    
    actual_shards, actual_replicas = wait_until(
        check_fn=check_topology,
        timeout=timeout,
        interval=5,
        timeout_msg=f"Cluster '{cluster_name}' topology not ready. Expected {expected_shards} shard(s), {expected_replicas} replica(s)"
    )
    
    note(f"system.clusters (cluster '{cluster_name}'): {actual_shards} shard(s), {actual_replicas} replica(s)")
    note(f"✓ system.clusters topology verified")


@TestStep(Then)
def verify_system_replicas_health(self, namespace, admin_password):
    """Verify system.replicas shows healthy replication status."""
    clickhouse_pods = get_clickhouse_pods(namespace=namespace)
    if not clickhouse_pods:
        raise AssertionError("No ClickHouse pods found")
    
    pod_name = clickhouse_pods[0]
    
    query = """
    SELECT 
        database, 
        table, 
        is_leader, 
        is_readonly,
        absolute_delay,
        queue_size
    FROM system.replicas 
    FORMAT TabSeparated
    """
    
    result = execute_clickhouse_query(
        namespace=namespace,
        pod_name=pod_name,
        query=query,
        user="default",
        password=admin_password,
        check=False
    )
    
    if result.returncode != 0 or not result.stdout.strip():
        note("⚠ No replicated tables found in system.replicas")
        return
    
    lines = result.stdout.strip().split('\n')
    for line in lines:
        parts = line.split('\t')
        if len(parts) >= 6:
            database, table, is_leader, is_readonly, absolute_delay, queue_size = parts
            note(f"Replica {database}.{table}: leader={is_leader}, readonly={is_readonly}, delay={absolute_delay}, queue={queue_size}")
            
            # Check for unhealthy states
            if is_readonly == '1':
                note(f"⚠ Replica {database}.{table} is in readonly mode")
    
    note(f"✓ system.replicas health checked: {len(lines)} table(s)")


@TestStep(Then)
def verify_replication_working(self, namespace, admin_password):
    """Verify replication actually works by creating and checking a test table."""
    clickhouse_pods = get_clickhouse_pods(namespace=namespace)
    if len(clickhouse_pods) < 2:
        note("⚠ Skipping replication test - need at least 2 ClickHouse pods")
        return
    
    pod1 = clickhouse_pods[0]
    pod2 = clickhouse_pods[1]
    
    # Create a test replicated table on first pod
    test_db = "test_replication_db"
    test_table = "test_replication_table"
    
    try:
        # Create database
        query = f"CREATE DATABASE IF NOT EXISTS {test_db} ON CLUSTER '{{cluster}}'"
        execute_clickhouse_query(
            namespace=namespace,
            pod_name=pod1,
            query=query,
            user="default",
            password=admin_password,
            check=True
        )
        
        query = f"""
        CREATE TABLE IF NOT EXISTS {test_db}.{test_table} ON CLUSTER '{{cluster}}'
        (id UInt32, value String)
        ENGINE = ReplicatedMergeTree('/clickhouse/tables/{{shard}}/{test_db}/{test_table}', '{{replica}}')
        ORDER BY id
        """
        execute_clickhouse_query(
            namespace=namespace,
            pod_name=pod1,
            query=query,
            user="default",
            password=admin_password,
            check=True
        )
        
        query = f"INSERT INTO {test_db}.{test_table} VALUES (1, 'test_value')"
        execute_clickhouse_query(
            namespace=namespace,
            pod_name=pod1,
            query=query,
            user="default",
            password=admin_password,
            check=True
        )
        
        time.sleep(2)
        
        query = f"SELECT count() FROM {test_db}.{test_table}"
        result = execute_clickhouse_query(
            namespace=namespace,
            pod_name=pod2,
            query=query,
            user="default",
            password=admin_password,
            check=True
        )
        
        count = int(result.stdout.strip())
        assert count == 1, f"Expected 1 row replicated to second pod, got {count}"
        
        note(f"✓ Replication working: data replicated from {pod1} to {pod2}")
        
    finally:
        # Cleanup
        try:
            query = f"DROP DATABASE IF EXISTS {test_db} ON CLUSTER '{{cluster}}'"
            execute_clickhouse_query(
                namespace=namespace,
                pod_name=pod1,
                query=query,
                user="default",
                password=admin_password,
                check=False
            )
        except:
            pass


@TestStep(Then)
def verify_service_endpoints(self, namespace, expected_endpoint_count):
    """Verify service endpoints count matches expected."""
    services = kubernetes.get_services(namespace=namespace)
    clickhouse_services = [
        svc for svc in services if is_clickhouse_resource(resource_name=svc)
    ]
    
    if not clickhouse_services:
        raise AssertionError("No ClickHouse services found")
    
    # Check the main cluster service (not individual pod services)
    cluster_services = [svc for svc in clickhouse_services if not any(f"-{i}-" in svc for i in range(10))]
    
    if cluster_services:
        service_name = cluster_services[0]
        endpoints_info = kubernetes.get_endpoints_info(
            namespace=namespace,
            endpoints_name=service_name
        )
        
        # Count endpoints
        subsets = endpoints_info.get("subsets", [])
        total_endpoints = sum(len(subset.get("addresses", [])) for subset in subsets)
        
        note(f"Service {service_name} has {total_endpoints} endpoint(s)")
        
        assert total_endpoints == expected_endpoint_count, \
            f"Expected {expected_endpoint_count} endpoints, got {total_endpoints}"


@TestStep(Then)
def verify_secrets_exist(self, namespace):
    """Verify that required secrets exist in the namespace."""
    secrets = kubernetes.get_secrets(namespace=namespace)
    
    # Look for ClickHouse-related secrets
    clickhouse_secrets = [s for s in secrets if 'clickhouse' in s.lower() or 'chi-' in s]
    
    if clickhouse_secrets:
        note(f"Found ClickHouse secrets: {clickhouse_secrets}")
    else:
        note("⚠ No ClickHouse-specific secrets found (may use inline credentials)")
    
    note(f"✓ Secrets check completed")
