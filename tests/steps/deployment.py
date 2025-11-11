"""
Deployment verification helper for ClickHouse Helm chart tests.

This module provides the HelmState class which acts as an orchestrator
to verify deployments match their expected configuration.
"""

from testflows.core import *
import tests.steps.kubernetes as kubernetes
import tests.steps.clickhouse as clickhouse
import tests.steps.users as users
import yaml
from pathlib import Path


@TestStep(Then)
def wait_for_clickhouse_deployment(
    self,
    namespace: str,
    expected_pod_count: int = 2,
    expected_clickhouse_count: int = None,
):
    """Wait for ClickHouse deployment to be ready with all pods running.

    This is a common pattern used across most test scenarios:
    1. Wait for expected number of pods to be created
    2. Wait for all pods to be running
    3. Wait for ClickHouse pods specifically to be running

    Args:
        namespace: Kubernetes namespace
        expected_pod_count: Total number of pods expected (default: 2)
        expected_clickhouse_count: Number of ClickHouse pods expected (default: same as total)
    """
    if expected_clickhouse_count is None:
        expected_clickhouse_count = expected_pod_count

    with When(f"wait for {expected_pod_count} pods to be created"):
        kubernetes.wait_for_pod_count(
            namespace=namespace, expected_count=expected_pod_count
        )

    with And("wait for all pods to be running"):
        pods = kubernetes.wait_for_pods_running(namespace=namespace)
        note(f"All {len(pods)} pods are now running and ready")

    with And("wait for ClickHouse pods to be running"):
        clickhouse_pods = clickhouse.wait_for_clickhouse_pods_running(
            namespace=namespace, expected_count=expected_clickhouse_count
        )
        note(f"ClickHouse pods running: {clickhouse_pods}")


class HelmState:
    """Orchestrator for verifying Helm deployment state.

    This class reads a Helm values file and decides which verification checks
    to run based on the configuration. All actual verification logic is delegated
    to appropriate step functions in kubernetes.py and clickhouse.py.
    """

    def __init__(self, values_file_path):
        """Initialize HelmState with a values file.

        Args:
            values_file_path: Path to the Helm values YAML file
        """
        self.values_file = Path(values_file_path)
        with open(self.values_file, "r") as f:
            self.values = yaml.safe_load(f)

        # Extract configuration for easy access
        self.clickhouse_config = self.values.get("clickhouse", {})
        self.keeper_config = self.values.get("keeper", {})

    # Configuration readers - simple data extraction

    def get_expected_pod_count(self):
        """Total pods = ClickHouse pods + Keeper pods."""
        ch_pods = self.get_expected_clickhouse_pod_count()
        keeper_pods = self.get_expected_keeper_count()
        return ch_pods + keeper_pods

    def get_expected_clickhouse_pod_count(self):
        """ClickHouse pods = replicas × shards."""
        replicas = self.clickhouse_config.get("replicasCount", 1)
        shards = self.clickhouse_config.get("shardsCount", 1)
        return replicas * shards

    def get_expected_keeper_count(self):
        """Keeper pod count (0 if not enabled)."""
        if not self.keeper_config.get("enabled", False):
            return 0
        return self.keeper_config.get("replicaCount", 0)

    # Verification methods - delegate to step functions

    def verify_deployment(self, namespace):
        """Wait for and verify deployment is ready."""
        expected_total = self.get_expected_pod_count()
        expected_ch = self.get_expected_clickhouse_pod_count()
        expected_keeper = self.get_expected_keeper_count()

        note(
            f"Expected pods - Total: {expected_total}, ClickHouse: {expected_ch}, Keeper: {expected_keeper}"
        )

        # Wait for deployment to be ready
        wait_for_clickhouse_deployment(
            namespace=namespace,
            expected_pod_count=expected_total,
            expected_clickhouse_count=expected_ch,
        )

        # Verify pod counts match expectations
        clickhouse.verify_clickhouse_pod_count(
            namespace=namespace, expected_count=expected_ch
        )

        if expected_keeper > 0:
            clickhouse.verify_keeper_pod_count(
                namespace=namespace, expected_count=expected_keeper
            )

    def verify_cluster_topology(self, namespace):
        """Verify replicas and shards counts match configuration."""
        expected_replicas = self.clickhouse_config.get("replicasCount", 1)
        expected_shards = self.clickhouse_config.get("shardsCount", 1)

        # Get actual cluster topology from CHI
        chi_info = clickhouse.get_chi_info(namespace=namespace)
        assert chi_info is not None, "ClickHouseInstallation not found"

        clusters = chi_info.get("spec", {}).get("configuration", {}).get("clusters", [])
        assert len(clusters) > 0, "No clusters found in CHI"

        cluster = clusters[0]
        layout = cluster.get("layout", {})

        actual_replicas = layout.get("replicasCount")
        actual_shards = layout.get("shardsCount")

        assert (
            actual_replicas == expected_replicas
        ), f"Expected {expected_replicas} replicas, got {actual_replicas}"
        assert (
            actual_shards == expected_shards
        ), f"Expected {expected_shards} shards, got {actual_shards}"

        note(
            f"✓ Cluster topology: {expected_replicas} replicas, {expected_shards} shards"
        )

    def verify_name_override(self, namespace):
        """Verify custom name is used in resources."""
        name_override = self.values.get("nameOverride")
        clickhouse.verify_custom_name_in_resources(
            namespace=namespace, custom_name=name_override
        )
        note(f"✓ nameOverride: {name_override}")

    def verify_persistence(self, namespace):
        """Verify persistence storage configuration."""
        persistence_config = self.clickhouse_config.get("persistence", {})
        expected_size = persistence_config.get("size")
        expected_access_mode = persistence_config.get("accessMode", "ReadWriteOnce")

        # Verify CHI has correct persistence config
        clickhouse.verify_persistence_configuration(
            namespace=namespace, expected_size=expected_size
        )

        # Verify PVCs exist with correct size and access mode
        clickhouse.verify_clickhouse_pvc_size(
            namespace=namespace, expected_size=expected_size
        )

        # Verify PVC access mode
        self.verify_pvc_access_mode(
            namespace=namespace,
            expected_access_mode=expected_access_mode,
            pvc_type="data",
        )

    def verify_pvc_access_mode(self, namespace, expected_access_mode, pvc_type="data"):
        """Verify PVC access mode."""
        pvcs = kubernetes.get_pvcs(namespace=namespace)

        # Find ClickHouse PVCs by type
        for pvc in pvcs:
            if pvc_type in pvc.lower() and clickhouse.is_clickhouse_resource(
                resource_name=pvc
            ):
                pvc_info = kubernetes.get_pvc_info(namespace=namespace, pvc_name=pvc)
                access_modes = pvc_info.get("spec", {}).get("accessModes", [])

                assert (
                    expected_access_mode in access_modes
                ), f"Expected accessMode {expected_access_mode} in PVC {pvc}, got {access_modes}"

                note(f"✓ PVC {pvc_type} accessMode: {expected_access_mode}")
                return

        raise AssertionError(f"No {pvc_type} PVC found for verification")

    def verify_service(self, namespace):
        """Verify LoadBalancer service configuration."""
        lb_config = self.clickhouse_config.get("lbService", {})
        expected_ranges = lb_config.get("loadBalancerSourceRanges")

        kubernetes.verify_loadbalancer_service(
            namespace=namespace, expected_ranges=expected_ranges
        )

    def verify_users(self, namespace):
        """Verify comprehensive user configuration including permissions and grants."""
        default_user = self.clickhouse_config.get("defaultUser", {})
        user_configs = self.clickhouse_config.get("users")

        users.verify_all_users(
            namespace=namespace,
            default_user_config=default_user,
            users_config=user_configs,
        )

        # Verify default user hostIP if configured
        if default_user.get("hostIP"):
            users.verify_user_host_ip(
                namespace=namespace,
                user="default",
                expected_host_ip=default_user["hostIP"],
            )

        note(f"✓ All users verified")

    def verify_keeper(self, namespace):
        """Verify Keeper pods are running."""
        expected_count = self.keeper_config.get("replicaCount", 0)

        clickhouse.verify_keeper_pods_running(
            namespace=namespace, expected_count=expected_count
        )
        note(f"✓ Keeper: {expected_count} pods running")

    def verify_image(self, namespace):
        """Verify pods use correct image tag."""
        image_config = self.clickhouse_config.get("image", {})
        expected_tag = image_config.get("tag")

        clickhouse.verify_image_tag(namespace=namespace, expected_tag=expected_tag)

    def verify_pod_annotations(self, namespace):
        """Verify pod annotations configuration."""
        pod_annotations = self.clickhouse_config.get("podAnnotations", {})

        clickhouse.verify_pod_annotations(
            namespace=namespace, expected_annotations=pod_annotations
        )
        note(f"✓ Pod annotations: {len(pod_annotations)} verified")

    def verify_pod_labels(self, namespace):
        """Verify pod labels configuration."""
        pod_labels = self.clickhouse_config.get("podLabels", {})

        clickhouse.verify_pod_labels(namespace=namespace, expected_labels=pod_labels)
        note(f"✓ Pod labels: {len(pod_labels)} verified")

    def verify_service_annotations(self, namespace):
        """Verify service annotations configuration."""
        service_config = self.clickhouse_config.get("service", {})
        service_annotations = service_config.get("serviceAnnotations", {})
        service_type = service_config.get("type", "ClusterIP")

        clickhouse.verify_service_annotations(
            namespace=namespace,
            expected_annotations=service_annotations,
            service_type=service_type,
        )
        note(f"✓ Service annotations: {len(service_annotations)} verified")

    def verify_service_labels(self, namespace):
        """Verify service labels configuration."""
        service_config = self.clickhouse_config.get("service", {})
        service_labels = service_config.get("serviceLabels", {})
        service_type = service_config.get("type", "ClusterIP")

        clickhouse.verify_service_labels(
            namespace=namespace,
            expected_labels=service_labels,
            service_type=service_type,
        )
        note(f"✓ Service labels: {len(service_labels)} verified")

    def verify_log_persistence(self, namespace):
        """Verify log persistence volumes configuration."""
        persistence_config = self.clickhouse_config.get("persistence", {})
        logs_config = persistence_config.get("logs", {})

        if logs_config.get("enabled"):
            expected_log_size = logs_config.get("size")
            expected_access_mode = logs_config.get("accessMode", "ReadWriteOnce")

            clickhouse.verify_log_persistence(
                namespace=namespace, expected_log_size=expected_log_size
            )
            note(f"✓ Log persistence: {expected_log_size}")

            # Verify log PVC access mode
            self.verify_pvc_access_mode(
                namespace=namespace,
                expected_access_mode=expected_access_mode,
                pvc_type="logs",
            )

    def verify_extra_config(self, namespace):
        """Verify extraConfig custom ClickHouse configuration."""
        extra_config = self.clickhouse_config.get("extraConfig", "")

        if extra_config:
            # Extract key configuration items to verify
            config_keys = []
            if "max_connections" in extra_config:
                config_keys.append("max_connections")
            if "max_concurrent_queries" in extra_config:
                config_keys.append("max_concurrent_queries")
            if "logger" in extra_config:
                config_keys.append("logger")
            if "max_table_size_to_drop" in extra_config:
                config_keys.append("max_table_size_to_drop")

            clickhouse.verify_extra_config(
                namespace=namespace, expected_config_keys=config_keys
            )
            note(f"✓ ExtraConfig verified")

    def verify_keeper_storage(self, namespace):
        """Verify Keeper storage configuration."""
        local_storage = self.keeper_config.get("localStorage", {})
        storage_size = local_storage.get("size")

        if storage_size:
            clickhouse.verify_keeper_storage(
                namespace=namespace, expected_storage_size=storage_size
            )
            note(f"✓ Keeper storage: {storage_size}")

    def verify_keeper_annotations(self, namespace):
        """Verify Keeper pod annotations."""
        keeper_annotations = self.keeper_config.get("podAnnotations", {})

        if keeper_annotations:
            clickhouse.verify_keeper_annotations(
                namespace=namespace, expected_annotations=keeper_annotations
            )
            note(f"✓ Keeper annotations: {len(keeper_annotations)} verified")

    def verify_keeper_resources(self, namespace):
        """Verify Keeper resource requests and limits."""
        resources_config = self.keeper_config.get("resources", {})

        if resources_config:
            # Convert from the Helm chart format to standard Kubernetes format
            expected_resources = {}

            # Handle requests
            if (
                "cpuRequestsMs" in resources_config
                or "memoryRequestsMiB" in resources_config
            ):
                expected_resources["requests"] = {}
                if "cpuRequestsMs" in resources_config:
                    cpu_ms = resources_config["cpuRequestsMs"]
                    expected_resources["requests"]["cpu"] = f"{cpu_ms}m"
                if "memoryRequestsMiB" in resources_config:
                    memory = resources_config["memoryRequestsMiB"]
                    expected_resources["requests"]["memory"] = memory

            # Handle limits
            if (
                "cpuLimitsMs" in resources_config
                or "memoryLimitsMiB" in resources_config
            ):
                expected_resources["limits"] = {}
                if "cpuLimitsMs" in resources_config:
                    cpu_ms = resources_config["cpuLimitsMs"]
                    expected_resources["limits"]["cpu"] = f"{cpu_ms}m"
                if "memoryLimitsMiB" in resources_config:
                    memory = resources_config["memoryLimitsMiB"]
                    expected_resources["limits"]["memory"] = memory

            if expected_resources:
                clickhouse.verify_keeper_resources(
                    namespace=namespace, expected_resources=expected_resources
                )
                note(f"✓ Keeper resources verified")

    def verify_all(self, namespace):
        """Run all verification checks based on configuration.

        This is the main orchestrator - it decides which checks to run
        based on the Helm values configuration.
        """
        note(f"Verifying deployment state from: {self.values_file.name}")

        # Always verify deployment readiness
        self.verify_deployment(namespace=namespace)

        # Verify cluster topology (replicas/shards)
        self.verify_cluster_topology(namespace=namespace)

        # Conditional verifications based on what's configured
        if self.values.get("nameOverride"):
            self.verify_name_override(namespace=namespace)

        if self.clickhouse_config.get("persistence", {}).get("enabled"):
            self.verify_persistence(namespace=namespace)
            # Check for separate log persistence
            if (
                self.clickhouse_config.get("persistence", {})
                .get("logs", {})
                .get("enabled")
            ):
                self.verify_log_persistence(namespace=namespace)

        if self.clickhouse_config.get("lbService", {}).get("enabled"):
            self.verify_service(namespace=namespace)

        if self.clickhouse_config.get("defaultUser") or self.clickhouse_config.get(
            "users"
        ):
            self.verify_users(namespace=namespace)

        if self.clickhouse_config.get("podAnnotations"):
            self.verify_pod_annotations(namespace=namespace)

        if self.clickhouse_config.get("podLabels"):
            self.verify_pod_labels(namespace=namespace)

        if self.clickhouse_config.get("service", {}).get("serviceAnnotations"):
            self.verify_service_annotations(namespace=namespace)

        if self.clickhouse_config.get("service", {}).get("serviceLabels"):
            self.verify_service_labels(namespace=namespace)

        if self.clickhouse_config.get("extraConfig"):
            self.verify_extra_config(namespace=namespace)

        if self.keeper_config.get("enabled"):
            self.verify_keeper(namespace=namespace)

            # Verify Keeper-specific configurations
            if self.keeper_config.get("localStorage", {}).get("size"):
                self.verify_keeper_storage(namespace=namespace)

            if self.keeper_config.get("podAnnotations"):
                self.verify_keeper_annotations(namespace=namespace)

            if self.keeper_config.get("resources"):
                self.verify_keeper_resources(namespace=namespace)

        if self.clickhouse_config.get("image", {}).get("tag"):
            self.verify_image(namespace=namespace)
