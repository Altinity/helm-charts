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

        self.clickhouse_config = self.values.get("clickhouse", {})
        self.keeper_config = self.values.get("keeper", {})

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

    def verify_deployment(self, namespace):
        """Wait for and verify deployment is ready."""
        expected_total = self.get_expected_pod_count()
        expected_ch = self.get_expected_clickhouse_pod_count()
        expected_keeper = self.get_expected_keeper_count()

        note(
            f"Expected pods - Total: {expected_total}, ClickHouse: {expected_ch}, Keeper: {expected_keeper}"
        )

        wait_for_clickhouse_deployment(
            namespace=namespace,
            expected_pod_count=expected_total,
            expected_clickhouse_count=expected_ch,
        )

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

        clickhouse.verify_chi_cluster_topology(
            namespace=namespace,
            expected_replicas=expected_replicas,
            expected_shards=expected_shards,
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

        clickhouse.verify_persistence_configuration(
            namespace=namespace, expected_size=expected_size
        )

        clickhouse.verify_clickhouse_pvc_size(
            namespace=namespace, expected_size=expected_size
        )

        kubernetes.verify_pvc_access_mode(
            namespace=namespace,
            expected_access_mode=expected_access_mode,
            pvc_name_filter="data",
            resource_matcher=clickhouse.is_clickhouse_resource,
        )

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

            kubernetes.verify_pvc_access_mode(
                namespace=namespace,
                expected_access_mode=expected_access_mode,
                pvc_name_filter="logs",
                resource_matcher=clickhouse.is_clickhouse_resource,
            )

    def verify_extra_config(self, namespace):
        """Verify extraConfig custom ClickHouse configuration."""
        extra_config = self.clickhouse_config.get("extraConfig", "")
        admin_password = self.clickhouse_config.get("defaultUser", {}).get(
            "password", ""
        )

        if extra_config:
            config_keys = clickhouse.extract_extra_config_keys(
                extra_config_xml=extra_config
            )

            clickhouse.verify_extra_config(
                namespace=namespace, expected_config_keys=config_keys
            )

            config_values = clickhouse.parse_extra_config_values(
                extra_config_xml=extra_config
            )

            if config_values:
                clickhouse.verify_extra_config_values(
                    namespace=namespace,
                    expected_config_values=config_values,
                    admin_password=admin_password,
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
            expected_resources = clickhouse.convert_helm_resources_to_k8s(
                helm_resources=resources_config
            )

            if expected_resources:
                clickhouse.verify_keeper_resources(
                    namespace=namespace, expected_resources=expected_resources
                )
                note(f"✓ Keeper resources verified")

    def verify_extra_containers(self, namespace):
        """Verify extraContainers configuration that affects CHI pod templates."""
        extra_containers = self.clickhouse_config.get("extraContainers", []) or []
        if not extra_containers:
            return

        for c in extra_containers:
            clickhouse.verify_extra_container_spec(
                namespace=namespace,
                expected_container=c,
            )
            mounts = c.get("mounts") or {}
            if mounts.get("data") is True:
                container_name = c.get("name")
                assert container_name, "extraContainers entry with mounts.data=true must set name"
                # This matches exactly what Helm created: <release>-<nameOverride|clickhouse>-data
                clickhouse.verify_extra_container_data_mount(
                    namespace=namespace,
                    container_name=container_name,
                    expected_volume_name=None,
                )

    def verify_clickhouse_resources(self, namespace):
        """Verify ClickHouse container resources."""
        resources_config = self.clickhouse_config.get("resources") or {}
        if not resources_config:
            return

        clickhouse.verify_clickhouse_resources(
            namespace=namespace,
            expected_resources=resources_config,
        )

    def verify_profiles_and_user_settings(self, namespace):
        """Verify users, profiles, and settings render correctly in CHI."""
        users = self.clickhouse_config.get("users") or []
        profiles = self.clickhouse_config.get("profiles") or {}
        settings = self.clickhouse_config.get("settings") or {}

        if not users and not profiles and not settings:
            return

        clickhouse.verify_profiles_and_user_settings(
            namespace=namespace,
            expected_users=users,
            expected_profiles=profiles,
            expected_settings=settings,
        )

    def verify_replication_health(self, namespace):
        """Verify replication health through system tables."""
        admin_password = self.clickhouse_config.get("defaultUser", {}).get(
            "password", ""
        )
        expected_replicas = self.clickhouse_config.get("replicasCount", 1)
        expected_shards = self.clickhouse_config.get("shardsCount", 1)

        if expected_replicas > 1 or expected_shards > 1:
            # Cluster name equals namespace (which equals release_name in test setup)
            clickhouse.verify_system_clusters(
                namespace=namespace,
                cluster_name=namespace,
                expected_shards=expected_shards,
                expected_replicas=expected_replicas,
                admin_password=admin_password,
            )

            if expected_replicas > 1:
                clickhouse.verify_system_replicas_health(
                    namespace=namespace, admin_password=admin_password
                )

            note(f"✓ Replication health verified")

    def verify_replication_working(self, namespace):
        """Verify replication actually works by creating and replicating a test table."""
        admin_password = self.clickhouse_config.get("defaultUser", {}).get(
            "password", ""
        )
        expected_replicas = self.clickhouse_config.get("replicasCount", 1)

        if expected_replicas > 1:
            clickhouse.verify_replication_working(
                namespace=namespace, admin_password=admin_password
            )
            note(f"✓ Replication data test passed")

    def verify_service_endpoints(self, namespace):
        """Verify service endpoints count matches expected ClickHouse replicas."""
        expected_ch_count = self.get_expected_clickhouse_pod_count()

        clickhouse.verify_service_endpoints(
            namespace=namespace, expected_endpoint_count=expected_ch_count
        )
        note(f"✓ Service endpoints: {expected_ch_count}")

    def verify_secrets(self, namespace):
        """Verify Kubernetes secrets exist for credentials."""
        clickhouse.verify_secrets_exist(namespace=namespace)
        note(f"✓ Secrets verified")

    def verify_all(self, namespace):
        """Run all verification checks based on configuration.

        This is the main orchestrator - it decides which checks to run
        based on the Helm values configuration.
        """
        note(f"Verifying deployment state from: {self.values_file.name}")

        self.verify_deployment(namespace=namespace)
        self.verify_cluster_topology(namespace=namespace)

        expected_replicas = self.clickhouse_config.get("replicasCount", 1)
        expected_shards = self.clickhouse_config.get("shardsCount", 1)
        if expected_replicas > 1 or expected_shards > 1:
            self.verify_replication_health(namespace=namespace)

            if expected_replicas > 1:
                self.verify_replication_working(namespace=namespace)

        self.verify_service_endpoints(namespace=namespace)
        self.verify_secrets(namespace=namespace)

        if self.values.get("nameOverride"):
            self.verify_name_override(namespace=namespace)

        if self.clickhouse_config.get("persistence", {}).get("enabled"):
            self.verify_persistence(namespace=namespace)

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

        if self.clickhouse_config.get("extraContainers"):
            self.verify_extra_containers(namespace=namespace)

        if self.clickhouse_config.get("resources"):
            self.verify_clickhouse_resources(namespace=namespace)

        if (
            self.clickhouse_config.get("users")
            or self.clickhouse_config.get("profiles")
            or self.clickhouse_config.get("settings")
        ):
            self.verify_profiles_and_user_settings(namespace=namespace)

        if self.keeper_config.get("enabled"):
            self.verify_keeper(namespace=namespace)

            if self.keeper_config.get("localStorage", {}).get("size"):
                self.verify_keeper_storage(namespace=namespace)

            if self.keeper_config.get("podAnnotations"):
                self.verify_keeper_annotations(namespace=namespace)

            if self.keeper_config.get("resources"):
                self.verify_keeper_resources(namespace=namespace)

        if self.clickhouse_config.get("image", {}).get("tag"):
            self.verify_image(namespace=namespace)
