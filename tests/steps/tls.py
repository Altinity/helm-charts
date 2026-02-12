from tests.steps.system import *
from tests.steps.kubernetes import *
import tests.steps.clickhouse as clickhouse
import json
import xml.etree.ElementTree as ET


@TestStep(Then)
def verify_tls_files_in_chi(self, namespace, chi_name):
    """Verify TLS files are present in CHI spec."""
    chi_info = run(cmd=f"kubectl get chi {chi_name} -n {namespace} -o json")
    chi_data = json.loads(chi_info.stdout)
    
    files = chi_data.get("spec", {}).get("configuration", {}).get("files", {})
    
    for expected_file in ["config.d/foo.crt", "bar.key", "dhparam.pem", "openssl.xml"]:
        assert expected_file in files, f"Expected TLS file '{expected_file}' not found in CHI"
        note(f"✓ TLS file present: {expected_file}")


@TestStep(Then)
def verify_tls_secret_references_in_chi(self, namespace, chi_name):
    """Verify secret references are correct in CHI spec."""
    chi_info = run(cmd=f"kubectl get chi {chi_name} -n {namespace} -o json")
    chi_data = json.loads(chi_info.stdout)
    
    files = chi_data.get("spec", {}).get("configuration", {}).get("files", {})
    
    expected_secrets = {
        "bar.key": "clickhouse-certs",
        "dhparam.pem": "clickhouse-certs",
    }
    
    for file_key, expected_secret_name in expected_secrets.items():
        assert file_key in files, f"File '{file_key}' not found in CHI"
        file_config = files[file_key]
        
        assert isinstance(file_config, dict), f"Expected dict for secret ref in '{file_key}'"
        assert "valueFrom" in file_config, f"No valueFrom in '{file_key}'"
        
        secret_ref = file_config["valueFrom"]["secretKeyRef"]
        actual_secret_name = secret_ref["name"]
        
        assert actual_secret_name == expected_secret_name, \
            f"Expected secret '{expected_secret_name}' for '{file_key}', got '{actual_secret_name}'"
        
        note(f"✓ Secret reference correct: {file_key} → {actual_secret_name}")


@TestStep(Then)
def verify_openssl_config_on_pod(self, namespace):
    """Verify openssl.xml format on the ClickHouse pod."""
    pod_name = clickhouse.get_ready_clickhouse_pod(namespace=namespace)

    content = get_file_contents_from_pod(
        namespace=namespace,
        pod_name=pod_name,
        file_path="/etc/clickhouse-server/config.d/openssl.xml",
    )

    try:
        root = ET.fromstring(content)
    except ET.ParseError as e:
        raise AssertionError(f"openssl.xml is not valid XML: {e}")

    server_node = root.find(".//openSSL/server")
    assert server_node is not None, "openssl.xml missing <openSSL><server> node"

    note(f"✓ openssl.xml present and valid on pod at /etc/clickhouse-server/config.d/openssl.xml")


@TestStep(When)
def create_tls_secret(self, namespace):
    """Create a Kubernetes secret in the namespace with TLS files from fixtures.
    """
    import os
    
    tests_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    certs_dir = os.path.join(tests_dir, "fixtures", "tls")
    
    cert_file = os.path.join(certs_dir, "server.crt")
    key_file = os.path.join(certs_dir, "test-server.key")
    dhparam_file = os.path.join(certs_dir, "dhparam.pem")
    
    # At time of secret creation, the namespace might not exist
    run(cmd=f"kubectl create namespace {namespace}", check=False)
    # Optimistically delete secret in case it already exists for idempotency
    run(cmd=f"kubectl delete secret clickhouse-certs -n {namespace}", check=False)
    run(cmd=f"kubectl create secret generic clickhouse-certs -n {namespace} "
        f"--from-file=server.crt={cert_file} "
        f"--from-file=server.key={key_file} "
        f"--from-file=dhparam.pem={dhparam_file}")
    
    note(f"✓ Created TLS secret: clickhouse-certs")
