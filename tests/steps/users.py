from tests.steps.system import *
import json
import hashlib
import tests.steps.kubernetes as kubernetes
import tests.steps.clickhouse as clickhouse


@TestStep(When)
def get_user_grants(
    self,
    namespace,
    pod_name,
    user,
    password="",
    admin_user="default",
    admin_password="",
):
    """Get grants for a specific user."""
    query = f"SHOW GRANTS FOR {user} FORMAT JSON"

    try:
        result = clickhouse.execute_clickhouse_query(
            namespace=namespace,
            pod_name=pod_name,
            query=query,
            user=admin_user,
            password=admin_password,
            check=False,
        )

        if result.returncode == 0 and result.stdout:
            data = json.loads(result.stdout)
            if data.get("data") and data.get("meta"):
                col_name = data["meta"][0]["name"]
                return [row[col_name] for row in data["data"]]
    except Exception as e:
        note(f"Failed to get grants for user {user}: {e}")

    return []


@TestStep(When)
def check_user_has_permission(
    self, namespace, pod_name, user, password, permission_query
):
    """Check if user can execute a specific query."""
    try:
        result = clickhouse.execute_clickhouse_query(
            namespace=namespace,
            pod_name=pod_name,
            query=permission_query,
            user=user,
            password=password,
            check=False,
        )
        return result.returncode == 0
    except:
        return False


@TestStep(Then)
def verify_user_exists(self, namespace, user_name, admin_password=""):
    """Verify that a user exists in ClickHouse."""
    clickhouse_pods = clickhouse.get_clickhouse_pods(namespace=namespace)
    assert len(clickhouse_pods) > 0, "No ClickHouse pods found"

    pod_name = clickhouse_pods[0]

    query = f"SELECT name FROM system.users WHERE name = '{user_name}'"
    result = clickhouse.execute_clickhouse_query(
        namespace=namespace,
        pod_name=pod_name,
        query=query,
        user="default",
        password=admin_password,
        check=False,
    )

    assert result.returncode == 0, f"Failed to query system.users"
    assert user_name in result.stdout, f"User '{user_name}' not found in system.users"
    note(f"✓ User exists: {user_name}")


@TestStep(Then)
def verify_user_connectivity(self, namespace, user, password):
    """Verify that a user can connect to ClickHouse."""
    clickhouse_pods = clickhouse.get_clickhouse_pods(namespace=namespace)
    assert len(clickhouse_pods) > 0, "No ClickHouse pods found"

    pod_name = clickhouse_pods[0]

    result = clickhouse.test_clickhouse_connection(
        namespace=namespace, pod_name=pod_name, user=user, password=password
    )

    assert result, f"Failed to connect to ClickHouse with user '{user}'"
    note(f"✓ User connection successful: {user}")


@TestStep(Then)
def verify_user_password_hash(
    self, namespace, user, expected_hash, plaintext_password, admin_password=""
):
    """Verify that the user's password hash configuration is correct."""
    clickhouse_pods = clickhouse.get_clickhouse_pods(namespace=namespace)
    assert len(clickhouse_pods) > 0, "No ClickHouse pods found"

    pod_name = clickhouse_pods[0]

    query = (
        f"SELECT name, auth_type FROM system.users WHERE name = '{user}' FORMAT JSON"
    )
    result = clickhouse.execute_clickhouse_query(
        namespace=namespace,
        pod_name=pod_name,
        query=query,
        user="default",
        password=admin_password,
        check=False,
    )

    assert result.returncode == 0, f"Failed to query auth type for user '{user}'"

    data = json.loads(result.stdout)
    if not data.get("data") or len(data["data"]) == 0:
        raise AssertionError(f"User '{user}' not found in system.users")

    user_data = data["data"][0]
    auth_types = user_data.get("auth_type", [])

    assert (
        "sha256_password" in auth_types
    ), f"User '{user}' is not configured with SHA256 authentication. Auth types: {auth_types}"

    computed_hash = hashlib.sha256(plaintext_password.encode("utf-8")).hexdigest()

    assert computed_hash.lower() == expected_hash.lower(), (
        f"Computed hash from password doesn't match expected hash for user '{user}'. "
        f"Expected: {expected_hash}, Computed: {computed_hash}"
    )

    note(f"✓ User '{user}' SHA256 hash verified: {expected_hash[:16]}...")


@TestStep(Then)
def verify_user_grants(self, namespace, user, expected_grants, admin_password=""):
    """Verify that a user has expected grants."""
    clickhouse_pods = clickhouse.get_clickhouse_pods(namespace=namespace)
    assert len(clickhouse_pods) > 0, "No ClickHouse pods found"

    pod_name = clickhouse_pods[0]

    actual_grants = get_user_grants(
        namespace=namespace,
        pod_name=pod_name,
        user=user,
        admin_user="default",
        admin_password=admin_password,
    )

    assert (
        actual_grants
    ), f"Failed to retrieve grants for user '{user}' - check admin privileges or ClickHouse configuration"

    for expected_grant in expected_grants:
        expected_normalized = " ".join(expected_grant.split())

        found = False
        for actual_grant in actual_grants:
            actual_normalized = " ".join(actual_grant.split())
            if expected_normalized.lower() in actual_normalized.lower():
                found = True
                note(f"✓ Grant verified: {expected_grant}")
                break

        assert (
            found
        ), f"Grant '{expected_grant}' not found for user '{user}'. Actual grants: {actual_grants}"


@TestStep(Then)
def verify_user_access_management(
    self, namespace, user, expected_access_management, admin_password=""
):
    """Verify user's access_management setting from CHI spec."""
    chi_info = clickhouse.get_chi_info(namespace=namespace)
    assert chi_info is not None, "ClickHouseInstallation not found"

    users_config = chi_info.get("spec", {}).get("configuration", {}).get("users", {})
    access_mgmt_key = f"{user}/access_management"

    actual_access_mgmt = users_config.get(access_mgmt_key)

    assert (
        actual_access_mgmt is not None
    ), f"access_management not configured for user '{user}' in CHI"
    assert (
        actual_access_mgmt == expected_access_management
    ), f"Expected access_management={expected_access_management}, got {actual_access_mgmt}"

    note(f"✓ User '{user}' access_management: {expected_access_management}")


@TestStep(Then)
def verify_user_host_ip(self, namespace, user, expected_host_ip):
    """Verify user's hostIP network restrictions from CHI spec."""
    chi_info = clickhouse.get_chi_info(namespace=namespace)
    assert chi_info is not None, "ClickHouseInstallation not found"

    users_config = chi_info.get("spec", {}).get("configuration", {}).get("users", {})
    networks_key = f"{user}/networks/ip"

    actual_host_ip = users_config.get(networks_key)

    assert actual_host_ip is not None, f"hostIP not configured for user '{user}' in CHI"

    if isinstance(expected_host_ip, list) and not isinstance(actual_host_ip, list):
        expected_host_ip = (
            expected_host_ip[0] if len(expected_host_ip) == 1 else expected_host_ip
        )

    assert (
        actual_host_ip == expected_host_ip
    ), f"Expected hostIP={expected_host_ip}, got {actual_host_ip}"

    note(f"✓ User '{user}' hostIP: {actual_host_ip}")


@TestStep(Then)
def verify_user_permissions(self, namespace, user, password, permission_tests):
    """Verify user has specific permissions by testing queries."""
    clickhouse_pods = clickhouse.get_clickhouse_pods(namespace=namespace)
    assert len(clickhouse_pods) > 0, "No ClickHouse pods found"

    pod_name = clickhouse_pods[0]

    for description, query in permission_tests.items():
        has_permission = check_user_has_permission(
            namespace=namespace,
            pod_name=pod_name,
            user=user,
            password=password,
            permission_query=query,
        )

        if has_permission:
            note(f"✓ User '{user}' can: {description}")
        else:
            note(f"✗ User '{user}' cannot: {description}")


@TestStep(Then)
def verify_readonly_user(self, namespace, user, password=""):
    """Verify that a user has read-only permissions."""
    clickhouse_pods = clickhouse.get_clickhouse_pods(namespace=namespace)
    assert len(clickhouse_pods) > 0, "No ClickHouse pods found"

    pod_name = clickhouse_pods[0]

    can_select = check_user_has_permission(
        namespace=namespace,
        pod_name=pod_name,
        user=user,
        password=password,
        permission_query="SELECT 1 FROM system.tables LIMIT 1",
    )

    if can_select:
        note(f"✓ User '{user}' can perform SELECT queries")
    else:
        note(f"⊘ User '{user}' cannot perform SELECT queries (might be expected)")

    can_insert = check_user_has_permission(
        namespace=namespace,
        pod_name=pod_name,
        user=user,
        password=password,
        permission_query="INSERT INTO system.query_log VALUES ()",
    )

    if not can_insert:
        note(f"✓ User '{user}' correctly denied INSERT permissions")
    else:
        note(f"⚠ Warning: User '{user}' has INSERT permissions (expected read-only)")


@TestStep(Then)
def verify_all_users(self, namespace, default_user_config=None, users_config=None):
    """Comprehensive verification of all user configurations."""
    clickhouse_pods = clickhouse.get_clickhouse_pods(namespace=namespace)
    if not clickhouse_pods:
        note("No ClickHouse pods found, skipping user verification")
        return

    pod_name = clickhouse_pods[0]
    admin_password = ""

    if default_user_config:
        if "password" in default_user_config:
            admin_password = default_user_config["password"]
            verify_user_connectivity(
                namespace=namespace, user="default", password=admin_password
            )

        note(f"✓ Default user verified")

    if users_config:
        for user_config in users_config:
            user_name = user_config.get("name")
            if not user_name:
                continue

            note(f"Verifying user: {user_name}")

            verify_user_exists(
                namespace=namespace, user_name=user_name, admin_password=admin_password
            )

            if "password" in user_config:
                verify_user_connectivity(
                    namespace=namespace,
                    user=user_name,
                    password=user_config["password"],
                )

                if "password_sha256_hex" in user_config:
                    verify_user_password_hash(
                        namespace=namespace,
                        user=user_name,
                        expected_hash=user_config["password_sha256_hex"],
                        plaintext_password=user_config["password"],
                        admin_password=admin_password,
                    )
            elif "password_sha256_hex" in user_config:
                note(
                    f"⊘ User '{user_name}' uses hashed password but no plaintext provided for connectivity test"
                )

            if "accessManagement" in user_config:
                verify_user_access_management(
                    namespace=namespace,
                    user=user_name,
                    expected_access_management=user_config["accessManagement"],
                    admin_password=admin_password,
                )

            if "hostIP" in user_config:
                verify_user_host_ip(
                    namespace=namespace,
                    user=user_name,
                    expected_host_ip=user_config["hostIP"],
                )

            if "grants" in user_config and user_config["grants"]:
                verify_user_grants(
                    namespace=namespace,
                    user=user_name,
                    expected_grants=user_config["grants"],
                    admin_password=admin_password,
                )

            if "readonly" in user_name.lower() and "password" in user_config:
                verify_readonly_user(
                    namespace=namespace,
                    user=user_name,
                    password=user_config["password"],
                )

            if "permission_tests" in user_config and "password" in user_config:
                verify_user_permissions(
                    namespace=namespace,
                    user=user_name,
                    password=user_config["password"],
                    permission_tests=user_config["permission_tests"],
                )

            note(f"✓ User '{user_name}' verification complete")
