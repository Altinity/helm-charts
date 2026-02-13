import json
import xml.etree.ElementTree as ET

from cryptography.hazmat.primitives.serialization import load_pem_parameters, load_pem_private_key
from cryptography.x509 import load_pem_x509_certificate

from tests.steps.system import *
from tests.steps.kubernetes import *
import tests.steps.clickhouse as clickhouse


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
def verify_settings_ports_in_chi(self, namespace, chi_name):
    """Verify settings block has correct port configuration in CHI spec."""
    chi_info = run(cmd=f"kubectl get chi {chi_name} -n {namespace} -o json")
    chi_data = json.loads(chi_info.stdout)

    settings = chi_data.get("spec", {}).get("configuration", {}).get("settings", {})
    expected_https_port = 8444;
    expected_tcp_secure_port = 9441;
    assert settings.get("tcp_port") == 9000, \
        f"Expected tcp_port: 9000, got: {settings.get('tcp_port')!r}"
    assert settings.get("https_port") == expected_https_port, \
        f"Expected https_port: {expected_https_port}, got: {settings.get('https_port')!r}"
    assert settings.get("tcp_port_secure") == expected_tcp_secure_port, \
        f"Expected tcp_port_secure: {expected_tcp_secure_port}, got: {settings.get('tcp_port_secure')!r}"
    note(f"✓ Settings block has tcp_port: 9000, https_port: {expected_https_port}, and tcp_port_secure: {expected_tcp_secure_port}")


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


@TestStep(Then)
def verify_tls_files_on_pod(self, namespace):
    """Verify TLS file contents on the ClickHouse pod."""

    pod_name = clickhouse.get_ready_clickhouse_pod(namespace=namespace)

    cert_pem = get_file_contents_from_pod(
        namespace=namespace,
        pod_name=pod_name,
        file_path="/etc/clickhouse-server/config.d/foo.crt",
    )

    key_pem = get_file_contents_from_pod(
        namespace=namespace,
        pod_name=pod_name,
        file_path="/etc/clickhouse-server/secrets.d/bar.key/clickhouse-certs/server.key",
    )

    cert = load_pem_x509_certificate(cert_pem.encode())
    key = load_pem_private_key(key_pem.encode(), password=None)

    cert_modulus = cert.public_key().public_numbers().n
    key_modulus = key.public_key().public_numbers().n

    assert cert_modulus == key_modulus, "Certificate and private key moduli do not match"
    note("✓ Certificate and private key moduli match")

    dh_pem = get_file_contents_from_pod(
        namespace=namespace,
        pod_name=pod_name,
        file_path="/etc/clickhouse-server/secrets.d/dhparam.pem/clickhouse-certs/dhparam.pem",
    )

    dh_params = load_pem_parameters(dh_pem.encode())
    assert dh_params.parameter_numbers().g == 2, \
        f"Expected DH params generator g=2, got g={dh_params.parameter_numbers().g}"
    note("✓ DH params valid (g=2)")


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
