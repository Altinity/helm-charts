from testflows.core import *


import json
import tests.steps.kubernetes as kubernetes
import tests.steps.clickhouse as clickhouse
import tests.steps.minikube as minikube
import tests.steps.helm as helm


@TestScenario
def check_version(self):
    """Smoke test for ClickHouse Helm chart."""
    release_name = "my-clickhouse"
    namespace = "check-version"
    expected_version = self.context.version

    with When("install Altinity ClickHouse chart"):
        helm.setup_helm_release(namespace=namespace, release_name=release_name)

    with Then("wait for 2 pods to be created"):
        kubernetes.wait_for_pod_count(namespace=namespace, expected_count=2)

    with And("wait for ClickHouse pods to be running"):
        clickhouse.wait_for_clickhouse_pods_running(namespace=namespace)

    with When("verify ClickHouse version"):
        clickhouse.verify_clickhouse_version(namespace=namespace, expected_version=expected_version)



@TestScenario
def check_basic_configuration(self):
    """Test basic Helm chart configuration options."""
    release_name = "config-test"
    namespace = "check-basic-config"
    custom_name = "custom-clickhouse"

    with When("install ClickHouse with nameOverride"):
        helm.setup_helm_release(
            namespace=namespace,
            release_name=release_name,
            values={"nameOverride": custom_name}
        )

    with Then("wait for ClickHouse pods to be created"):
        kubernetes.wait_for_pod_count(namespace=namespace, expected_count=2)

    with And("verify custom name is used"):
        clickhouse.verify_custom_name_in_resources(namespace=namespace, custom_name=custom_name)



@TestScenario
def check_replicas_and_shards(self):
    """Test ClickHouse replicas and shards configuration."""
    release_name = "replicas-test"
    namespace = "check-replicas-shards"

    with When("install ClickHouse with 2 replicas and 2 shards"):
        helm.setup_helm_release(
            namespace=namespace,
            release_name=release_name,
            values={
                "clickhouse": {
                    "replicasCount": 2,
                    "shardsCount": 2
                },
                "keeper": {
                    "enabled": True
                }
            }
        )

    with Then("wait for expected number of pods"):
        # 2 ClickHouse replicas + 3 Keeper replicas = 5 pods
        kubernetes.wait_for_pod_count(namespace=namespace, expected_count=5)

    with And("wait for all pods to be running"):
        pods = kubernetes.wait_for_pods_running(namespace=namespace)
        note(f"All {len(pods)} pods are now running and ready")



@TestScenario
def check_persistence_configuration(self):
    """Test ClickHouse persistence configuration."""
    release_name = "persistence"
    namespace = "check-persistence"
    expected_storage_size = "10Gi"

    with When("install ClickHouse with persistence enabled"):
        helm.setup_helm_release(
            namespace=namespace,
            release_name=release_name,
            values={
                "clickhouse": {
                    "persistence": {
                        "enabled": True,
                        "size": expected_storage_size,
                        "accessMode": "ReadWriteOnce"
                    }
                }
            }
        )

    with Then("wait for ClickHouse pods to be created"):
        kubernetes.wait_for_pod_count(namespace=namespace, expected_count=2)

    with And("wait for ClickHouse pods to be running"):
        clickhouse.wait_for_clickhouse_pods_running(namespace=namespace)

    with And("verify persistence configuration in ClickHouseInstallation"):
        clickhouse.verify_persistence_configuration(
            namespace=namespace, 
            expected_size=expected_storage_size
        )

    with And("verify PVCs are created with correct size"):
        pvcs = kubernetes.get_pvcs(namespace=namespace)
        assert len(pvcs) > 0, "No PVCs found for persistence"
        note(f"Created PVCs: {pvcs}")
        
        # Verify at least one PVC has the expected size
        for pvc in pvcs:
            pvc_info = kubernetes.run(cmd=f"kubectl get pvc {pvc} -n {namespace} -o json")
            pvc_data = json.loads(pvc_info.stdout)
            storage_size = pvc_data.get("spec", {}).get("resources", {}).get("requests", {}).get("storage")
            if storage_size == expected_storage_size:
                note(f"✅ PVC {pvc} has correct storage size: {storage_size}")
                break
        else:
            raise AssertionError(f"No PVC found with expected storage size {expected_storage_size}")


@TestScenario
def check_service_configuration(self):
    """Test ClickHouse service configuration."""
    release_name = "service-test"
    namespace = "service"


    with When("install ClickHouse with LoadBalancer service"):
        kubernetes.use_context(context_name="minikube")
        helm.setup_helm_release(
            namespace=namespace,
            release_name=release_name,
            values={
                "clickhouse": {
                    "lbService": {
                        "enabled": True,
                        "loadBalancerSourceRanges": ["0.0.0.0/0"]
                    }
                }
            }
        )

    with Then("wait for pods to be created"):
        kubernetes.wait_for_pod_count(namespace=namespace, expected_count=2)

    with And("verify LoadBalancer service is created"):
        services = kubernetes.get_services(namespace=namespace)
        lb_services = [s for s in services if kubernetes.get_service_type(service_name=s, namespace=namespace) == "LoadBalancer"]
        assert len(lb_services) > 0, "LoadBalancer service not found"

    with And("verify LoadBalancer service has correct source ranges"):
        lb_service_name = lb_services[0]
        service_info = kubernetes.get_service_info(service_name=lb_service_name, namespace=namespace)
        source_ranges = service_info["spec"].get("loadBalancerSourceRanges", [])
        assert source_ranges == ["0.0.0.0/0"], f"Expected source ranges ['0.0.0.0/0'], got {source_ranges}"

    with And("verify LoadBalancer service has correct ports"):
        ports = service_info["spec"]["ports"]
        port_names = [p["name"] for p in ports]
        assert "http" in port_names and "tcp" in port_names, f"Expected http and tcp ports, got {port_names}"
        
        for port in ports:
            if port["name"] == "http":
                assert port["port"] == 8123, f"Expected HTTP port 8123, got {port['port']}"
            elif port["name"] == "tcp":
                assert port["port"] == 9000, f"Expected TCP port 9000, got {port['port']}"

    

@TestFeature
@Name("smoke")
def feature(self):
    """Run the smoke test feature."""

    with Given("minikube environment"):
        minikube.setup_minikube_environment()


    Scenario(run=check_version)
    Scenario(run=check_basic_configuration)
    Scenario(run=check_replicas_and_shards)
    Scenario(run=check_persistence_configuration)
    Scenario(run=check_service_configuration)

