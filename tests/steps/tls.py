from tests.steps.system import *
from tests.steps.kubernetes import *
import json


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
def verify_openssl_config_in_chi(self, namespace, chi_name):
    """Verify openssl.xml is present in CHI spec."""
    chi_info = run(cmd=f"kubectl get chi {chi_name} -n {namespace} -o json")
    chi_data = json.loads(chi_info.stdout)
    
    files = chi_data.get("spec", {}).get("configuration", {}).get("files", {})
    
    assert "openssl.xml" in files, "openssl.xml not found in CHI"
    openssl_content = files["openssl.xml"]
    
    assert "<openSSL>" in openssl_content, "openssl.xml missing <openSSL> tag"
    assert "<server>" in openssl_content, "openssl.xml missing <server> tag"
    
    note(f"✓ openssl.xml present and valid")


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
