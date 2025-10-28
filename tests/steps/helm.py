from tests.steps.system import *
import yaml
import tempfile
import os


@TestStep(Given)
def install_altinity(self, namespace, release_name, local=True):
    """Install ClickHouse Operator using Altinity Helm charts."""

    if local:
        # Use local chart from charts/clickhouse directory
        chart_path = os.path.join(os.getcwd(), "charts", "clickhouse")
        run(
            cmd=f"helm install {release_name} {chart_path} "
            f"--namespace {namespace} --create-namespace"
        )
    else:
        # Use remote repository
        run(cmd=f"helm repo add altinity {self.context.altinity_repo} || true")
        run(cmd="helm repo update")

        run(
            cmd=f"helm install {release_name} altinity/clickhouse "
            f"--namespace {namespace} --create-namespace"
        )


@TestStep(Finally)
def uninstall(self, namespace, release_name):
    """Uninstall ClickHouse Operator."""

    run(cmd=f"helm uninstall {release_name} -n {namespace}", check=False)


@TestStep(When)
def install_with_values(self, namespace, release_name, values, expect_failure=False, local=True):
    """Install ClickHouse with custom values."""

    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        yaml.dump(values, f)
        values_file = f.name

    try:
        if local:
            # Use local chart from charts/clickhouse directory
            chart_path = os.path.join(os.getcwd(), "charts", "clickhouse")
            cmd = (
                f"helm install {release_name} {chart_path} "
                f"--namespace {namespace} --create-namespace "
                f"--values {values_file}"
            )
        else:
            # Use remote repository
            cmd = (
                f"helm install {release_name} altinity/clickhouse "
                f"--namespace {namespace} --create-namespace "
                f"--values {values_file}"
            )

        if expect_failure:
            result = run(cmd=cmd, check=False)
            return result
        else:
            result = run(cmd=cmd)
            return result
    finally:
        # Clean up temporary file
        os.unlink(values_file)


@TestStep(Given)
def setup_helm_release(self, namespace, release_name, values=None, clean_up=True, local=True):
    """Set up a Helm release with optional custom values."""

    if values:
        install_with_values(
            namespace=namespace, release_name=release_name, values=values, local=local
        )
    else:
        install_altinity(namespace=namespace, release_name=release_name, local=local)

    yield

    if clean_up:
        uninstall(namespace=namespace, release_name=release_name)
