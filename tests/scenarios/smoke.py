from testflows.core import *

import os
import tests.steps.kubernetes as kubernetes
import tests.steps.minikube as minikube
import tests.steps.helm as helm
import tests.steps.clickhouse as clickhouse
from tests.steps.deployment import HelmState


FIXTURES = [
    "fixtures/01-minimal-single-node.yaml",
    "fixtures/02-replicated-with-users.yaml",
    # "fixtures/03-sharded-advanced.yaml",
    # "fixtures/04-external-keeper.yaml",
    # "fixtures/05-persistence-disabled.yaml",
]

UPGRADE_SCENARIOS = [
    ("fixtures/upgrade/initial.yaml", "fixtures/upgrade/upgrade.yaml"),
]


@TestScenario
def check_deployment(self, fixture_file, skip_external_keeper=True):
    """Test a single ClickHouse deployment configuration.

    Args:
        fixture_file: Path to the fixture YAML file
        skip_external_keeper: Skip if fixture requires external keeper
    """
    fixture_name = os.path.basename(fixture_file).replace(".yaml", "")
    # Keep release name and namespace under 11 chars to avoid Kubernetes naming issues
    short_name = f"t{fixture_name[:9]}"
    release_name = short_name
    namespace = short_name

    with Given("paths to fixture file"):
        tests_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        values_path = os.path.join(tests_dir, fixture_file)

    with And("load fixture configuration"):
        state = HelmState(values_path)
        note(f"Testing fixture: {fixture_file}")
        note(f"Expected pods: {state.get_expected_pod_count()}")

    if skip_external_keeper and "external-keeper" in fixture_name:
        skip("Skipping external keeper test (requires pre-existing keeper)")
        return

    with When("install ClickHouse with fixture configuration"):
        kubernetes.use_context(context_name="minikube")
        helm.install(
            namespace=namespace, release_name=release_name, values_file=fixture_file
        )

    with Then("verify deployment state"):
        state.verify_all(namespace=namespace)

    # Add Keeper HA test for replicated deployments with 3+ keepers
    if "replicated" in fixture_name:
        with And("test Keeper high availability (chaos test)"):
            admin_password = state.clickhouse_config.get("defaultUser", {}).get(
                "password", ""
            )
            clickhouse.test_keeper_high_availability(
                namespace=namespace, admin_password=admin_password
            )

    # Verify metrics endpoint is accessible
    with And("verify metrics endpoint"):
        clickhouse.verify_metrics_endpoint(namespace=namespace)

    with Finally("cleanup deployment"):
        helm.uninstall(namespace=namespace, release_name=release_name)
        kubernetes.delete_namespace(namespace=namespace)


@TestScenario
def check_upgrade(self, initial_fixture, upgrade_fixture):
    """Test ClickHouse Operator upgrade process.

    Args:
        initial_fixture: Path to initial configuration YAML
        upgrade_fixture: Path to upgraded configuration YAML
    """
    release_name = f"upgrade"
    namespace = f"upgrade"

    with Given("paths to fixture files"):
        tests_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        initial_values_path = os.path.join(tests_dir, initial_fixture)
        upgrade_values_path = os.path.join(tests_dir, upgrade_fixture)

    with And("define Helm states for initial and upgraded configurations"):
        initial_state = HelmState(initial_values_path)
        upgrade_state = HelmState(upgrade_values_path)
        note(f"Initial pods: {initial_state.get_expected_pod_count()}")
        note(f"Upgraded pods: {upgrade_state.get_expected_pod_count()}")

    with When("install ClickHouse with initial configuration"):
        kubernetes.use_context(context_name="minikube")
        helm.install(
            namespace=namespace, release_name=release_name, values_file=initial_fixture
        )

    with Then("verify initial deployment state"):
        initial_state.verify_all(namespace=namespace)

    # Only test data survival if nameOverride stays the same (in-place upgrade)
    initial_name = initial_state.values.get("nameOverride", "")
    upgrade_name = upgrade_state.values.get("nameOverride", "")
    is_inplace_upgrade = initial_name == upgrade_name

    if is_inplace_upgrade:
        with And("create test data for upgrade survival verification"):
            admin_password = initial_state.clickhouse_config.get("defaultUser", {}).get(
                "password", ""
            )
            clickhouse.create_test_data(
                namespace=namespace,
                admin_password=admin_password,
                table_name="pre_upgrade_data",
                test_value=f"upgrade_survival_{namespace}",
            )
    else:
        note(
            f"Skipping data survival test: nameOverride changed from '{initial_name}' to '{upgrade_name}' (cluster replacement scenario)"
        )

    with When("upgrade ClickHouse to new configuration"):
        helm.upgrade(
            namespace=namespace, release_name=release_name, values_file=upgrade_fixture
        )

    with Then("verify upgraded deployment state"):
        upgrade_state.verify_all(namespace=namespace)

    if is_inplace_upgrade:
        with And("verify data survived the upgrade"):
            admin_password = upgrade_state.clickhouse_config.get("defaultUser", {}).get(
                "password", ""
            )
            clickhouse.verify_data_survival(
                namespace=namespace,
                admin_password=admin_password,
                table_name="pre_upgrade_data",
                expected_value=f"upgrade_survival_{namespace}",
            )
    else:
        note(f"Data survival verification skipped for cluster replacement scenario")

    with And("verify metrics endpoint"):
        clickhouse.verify_metrics_endpoint(namespace=namespace)

    with Finally("cleanup deployment"):
        helm.uninstall(namespace=namespace, release_name=release_name)
        kubernetes.delete_namespace(namespace=namespace)


@TestFeature
def check_all_fixtures(self):
    """Test all fixture configurations."""

    for fixture in FIXTURES:
        Scenario(
            test=check_deployment,
            name=f"deploy_{os.path.basename(fixture).replace('.yaml', '')}",
        )(fixture_file=fixture, skip_external_keeper=True)


@TestFeature
def check_all_upgrades(self):
    """Test all upgrade scenarios."""

    for initial, upgraded in UPGRADE_SCENARIOS:
        scenario_name = f"{os.path.basename(initial).replace('.yaml', '')}_to_{os.path.basename(upgraded).replace('.yaml', '')}"
        Scenario(
            test=check_upgrade,
            name=f"upgrade_{scenario_name}",
        )(initial_fixture=initial, upgrade_fixture=upgraded)


@TestFeature
@Name("comprehensive")
def feature(self):
    """Run all comprehensive smoke tests."""

    with Given("minikube environment"):
        minikube.setup_minikube_environment()
        kubernetes.use_context(context_name="minikube")

    Feature(run=check_all_fixtures)

    Feature(run=check_all_upgrades)
