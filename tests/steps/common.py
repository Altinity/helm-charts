"""
Common helper functions for ClickHouse Helm chart tests.

This module provides simple helper functions to reduce code duplication
in test scenarios.
"""

from testflows.core import *
import tests.steps.kubernetes as kubernetes
import tests.steps.clickhouse as clickhouse


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
