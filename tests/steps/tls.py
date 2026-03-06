import os
import xml.etree.ElementTree as ET
from datetime import datetime, timezone

from cryptography.hazmat.primitives.serialization import load_pem_parameters, load_pem_private_key
from cryptography.x509 import load_pem_x509_certificate
from cryptography.x509.oid import ExtensionOID, NameOID

from tests.steps.system import *
from tests.steps.kubernetes import *
import tests.steps.clickhouse as clickhouse


@TestStep(Then)
def verify_tls_files_in_chi(self, namespace):
    """Verify TLS files are present in CHI spec."""
    chi_data = clickhouse.get_chi_info(namespace=namespace)

    files = chi_data.get("spec", {}).get("configuration", {}).get("files", {})
    
    for expected_file in ["config.d/foo.crt", "bar.key", "dhparam.pem", "config.d/openssl.xml"]:
        assert expected_file in files, f"Expected TLS file '{expected_file}' not found in CHI"
        note(f"✓ TLS file present: {expected_file}")


@TestStep(Then)
def verify_tls_secret_references_in_chi(self, namespace):
    """Verify secret references are correct in CHI spec."""
    chi_data = clickhouse.get_chi_info(namespace=namespace)

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
def verify_settings_ports_in_chi(self, namespace, expected_https_port):
    """Verify settings block has correct port configuration in CHI spec."""
    chi_data = clickhouse.get_chi_info(namespace=namespace)

    settings = chi_data.get("spec", {}).get("configuration", {}).get("settings", {})
    assert settings.get("https_port") == expected_https_port, \
        f"Expected https_port: {expected_https_port}, got: {settings.get('https_port')!r}"
    assert "tcp_port_secure" not in settings, \
        f"Did not expect 'tcp_port_secure' in settings, but found: {settings.get('tcp_port_secure')!r}"
    note(f"✓ Settings block only has https_port as explicitly set: {expected_https_port}")


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


@TestStep(Then)
def verify_https_certificate(self, namespace, https_port):
    """Verify the HTTPS endpoint serves TLS with the correct certificate.

    Performs a TLS handshake against the ClickHouse HTTPS port from within
    the pod, then validates the served certificate against the configured one.
    """
    pod_name = clickhouse.get_ready_clickhouse_pod(namespace=namespace)

    result = run(
        cmd=f"kubectl exec -n {namespace} {pod_name} -- "
            f"sh -c 'openssl s_client -connect localhost:{https_port} "
            f"</dev/null 2>&1'",
        check=False,
    )

    served_cert = load_pem_x509_certificate(result.stdout.encode())
    note(f"✓ TLS handshake successful on port {https_port}")

    now = datetime.now(timezone.utc)
    assert served_cert.not_valid_before_utc <= now, \
        f"Certificate not yet valid (notBefore: {served_cert.not_valid_before_utc})"
    assert served_cert.not_valid_after_utc > now, \
        f"Certificate has expired (notAfter: {served_cert.not_valid_after_utc})"
    note(
        f"✓ Certificate valid: "
        f"{served_cert.not_valid_before_utc.date()} to "
        f"{served_cert.not_valid_after_utc.date()}"
    )

    cn_attrs = served_cert.subject.get_attributes_for_oid(NameOID.COMMON_NAME)
    assert cn_attrs, "Certificate has no CN"
    cn = cn_attrs[0].value
    note(f"✓ Certificate CN: {cn}")

    # The cryptography library has no get-by-name accessor for X.509
    # extensions, so we iterate all extensions and match by OID to find
    # the Subject Alternative Name extension.
    san_names = []
    for ext in served_cert.extensions:
        if ext.oid == ExtensionOID.SUBJECT_ALTERNATIVE_NAME:
            san_names = [str(name.value) for name in ext.value]
            break

    assert san_names, "Certificate has no SANs"
    assert any(cn in san for san in san_names), \
        f"CN '{cn}' not found as substring of any SAN: {san_names}"
    note(f"✓ CN is substring of SAN (SANs: {san_names})")

    configured_cert_pem = get_file_contents_from_pod(
        namespace=namespace,
        pod_name=pod_name,
        file_path="/etc/clickhouse-server/config.d/foo.crt",
    )
    configured_cert = load_pem_x509_certificate(configured_cert_pem.encode())

    assert served_cert == configured_cert, \
        f"Served cert (serial {served_cert.serial_number:#x}) " \
        f"!= configured cert (serial {configured_cert.serial_number:#x})"
    note(f"✓ Served certificate matches configured (serial {served_cert.serial_number:#x})")


@TestStep(When)
def create_tls_secret(self, namespace):
    """Create a Kubernetes secret with TLS files from ../fixtures/tls/."""
    
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
