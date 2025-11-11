from tests.steps.system import *


@TestStep(Given)
def install(
    self,
    namespace,
    release_name,
    values=None,
    values_file=None,
    local=True,
    clean_up=True,
):
    """Install ClickHouse Operator using Altinity Helm charts with optional custom values.

    Args:
        namespace: Kubernetes namespace
        release_name: Helm release name
        values: Dictionary of values to use (will be converted to temp file)
        values_file: Path to values file (relative to tests/ directory)
        local: Whether to use local chart or remote
    """

    chart_path = self.context.local_chart_path if local else "altinity/clickhouse"

    if not local:
        with Given("Altinity Helm repo"):
            run(cmd=f"helm repo add altinity {self.context.altinity_repo} || true")
            run(cmd="helm repo update")

    cmd = f"helm install {release_name} {chart_path} --namespace {namespace} --create-namespace"
    cmd += values_argument(values=values, values_file=values_file)

    with When("install ClickHouse Operator"):
        r = run(cmd=cmd, check=True)

    yield r

    if clean_up:
        with Finally("uninstall ClickHouse Operator"):
            uninstall(namespace=namespace, release_name=release_name)


@TestStep(Finally)
def uninstall(self, namespace, release_name):
    """Uninstall ClickHouse Operator."""

    run(cmd=f"helm uninstall {release_name} -n {namespace}", check=False)


@TestStep(When)
def upgrade(self, namespace, release_name, values=None, values_file=None, local=True):
    """Upgrade an existing Helm release with optional custom values.

    Args:
        namespace: Kubernetes namespace
        release_name: Helm release name
        values: Dictionary of values to use (will be converted to temp file)
        values_file: Path to values file (relative to tests/ directory)
        local: Whether to use local chart or remote
    """

    chart_path = self.context.local_chart_path if local else "altinity/clickhouse"

    cmd = f"helm upgrade {release_name} {chart_path} --namespace {namespace}"
    cmd += values_argument(values=values, values_file=values_file)

    r = run(cmd=cmd)

    return r
