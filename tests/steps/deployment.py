"""
Deployment verification helper for ClickHouse Helm chart tests.

This module provides the HelmState class which acts as an orchestrator
to verify deployments match their expected configuration.
"""

from testflows.core import *
import tests.steps.kubernetes as kubernetes
import tests.steps.clickhouse as clickhouse
import yaml
from pathlib import Path


@TestStep(Then)
def wait_for_clickhouse_deployment(self, namespace: str, expected_pod_count: int = 2, expected_clickhouse_count: int = None):
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
        kubernetes.wait_for_pod_count(namespace=namespace, expected_count=expected_pod_count)

    with And("wait for all pods to be running"):
        pods = kubernetes.wait_for_pods_running(namespace=namespace)
        note(f"All {len(pods)} pods are now running and ready")

    with And("wait for ClickHouse pods to be running"):
        clickhouse_pods = clickhouse.wait_for_clickhouse_pods_running(
            namespace=namespace, 
            expected_count=expected_clickhouse_count
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
        with open(self.values_file, 'r') as f:
            self.values = yaml.safe_load(f)
        
        # Extract configuration for easy access
        self.clickhouse_config = self.values.get('clickhouse', {})
        self.keeper_config = self.values.get('keeper', {})
        
    # Configuration readers - simple data extraction
    
    def get_expected_pod_count(self):
        """Total pods = ClickHouse pods + Keeper pods."""
        ch_pods = self.get_expected_clickhouse_pod_count()
        keeper_pods = self.get_expected_keeper_count()
        return ch_pods + keeper_pods
    
    def get_expected_clickhouse_pod_count(self):
        """ClickHouse pods = replicas × shards."""
        replicas = self.clickhouse_config.get('replicasCount', 1)
        shards = self.clickhouse_config.get('shardsCount', 1)
        return replicas * shards
    
    def get_expected_keeper_count(self):
        """Keeper pod count (0 if not enabled)."""
        if not self.keeper_config.get('enabled', False):
            return 0
        return self.keeper_config.get('replicaCount', 0)
    
    # Verification methods - delegate to step functions
    
    def verify_deployment(self, namespace):
        """Wait for and verify deployment is ready."""
        expected_total = self.get_expected_pod_count()
        expected_ch = self.get_expected_clickhouse_pod_count()
        expected_keeper = self.get_expected_keeper_count()
        
        note(f"Expected pods - Total: {expected_total}, ClickHouse: {expected_ch}, Keeper: {expected_keeper}")
        
        # Wait for deployment to be ready
        wait_for_clickhouse_deployment(
            namespace=namespace,
            expected_pod_count=expected_total,
            expected_clickhouse_count=expected_ch
        )
        
        # Verify pod counts match expectations
        clickhouse.verify_clickhouse_pod_count(
            namespace=namespace,
            expected_count=expected_ch
        )
        
        if expected_keeper > 0:
            clickhouse.verify_keeper_pod_count(
                namespace=namespace,
                expected_count=expected_keeper
            )
    
    def verify_name_override(self, namespace):
        """Verify custom name is used in resources."""
        name_override = self.values.get('nameOverride')
        clickhouse.verify_custom_name_in_resources(
            namespace=namespace,
            custom_name=name_override
        )
        note(f"✓ nameOverride: {name_override}")
    
    def verify_persistence(self, namespace):
        """Verify persistence storage configuration."""
        persistence_config = self.clickhouse_config.get('persistence', {})
        expected_size = persistence_config.get('size')
        
        # Verify CHI has correct persistence config
        clickhouse.verify_persistence_configuration(
            namespace=namespace,
            expected_size=expected_size
        )
        
        # Verify PVCs exist with correct size
        clickhouse.verify_clickhouse_pvc_size(
            namespace=namespace,
            expected_size=expected_size
        )
    
    def verify_service(self, namespace):
        """Verify LoadBalancer service configuration."""
        lb_config = self.clickhouse_config.get('lbService', {})
        expected_ranges = lb_config.get('loadBalancerSourceRanges')
        
        kubernetes.verify_loadbalancer_service(
            namespace=namespace,
            expected_ranges=expected_ranges
        )
    
    def verify_users(self, namespace):
        """Verify user connectivity."""
        default_user = self.clickhouse_config.get('defaultUser')
        users = self.clickhouse_config.get('users')
        
        clickhouse.verify_users_configuration(
            namespace=namespace,
            default_user_config=default_user,
            users_config=users
        )
    
    def verify_keeper(self, namespace):
        """Verify Keeper pods are running."""
        expected_count = self.keeper_config.get('replicaCount', 0)
        
        clickhouse.verify_keeper_pods_running(
            namespace=namespace,
            expected_count=expected_count
        )
        note(f"✓ Keeper: {expected_count} pods running")
    
    def verify_image(self, namespace):
        """Verify pods use correct image tag."""
        image_config = self.clickhouse_config.get('image', {})
        expected_tag = image_config.get('tag')
        
        clickhouse.verify_image_tag(
            namespace=namespace,
            expected_tag=expected_tag
        )
    
    def verify_all(self, namespace):
        """Run all verification checks based on configuration.
        
        This is the main orchestrator - it decides which checks to run
        based on the Helm values configuration.
        """
        note(f"Verifying deployment state from: {self.values_file.name}")
        
        # Always verify deployment readiness
        self.verify_deployment(namespace=namespace)
        
        # Conditional verifications based on what's configured
        if self.values.get('nameOverride'):
            self.verify_name_override(namespace=namespace)
        
        if self.clickhouse_config.get('persistence', {}).get('enabled'):
            self.verify_persistence(namespace=namespace)
        
        if self.clickhouse_config.get('lbService', {}).get('enabled'):
            self.verify_service(namespace=namespace)
        
        if self.clickhouse_config.get('defaultUser') or self.clickhouse_config.get('users'):
            self.verify_users(namespace=namespace)
        
        if self.keeper_config.get('enabled'):
            self.verify_keeper(namespace=namespace)
        
        if self.clickhouse_config.get('image', {}).get('tag'):
            self.verify_image(namespace=namespace)
