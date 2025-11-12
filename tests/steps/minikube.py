from tests.steps.system import *
from tests.steps.kubernetes import use_context


@TestStep(Given)
def minikube_start(self, cpus, memory):
    """Start minikube."""

    run(cmd=f"minikube start --driver=docker --cpus={cpus} --memory={memory}")


@TestStep(Given)
def minikube_delete(self):
    """Delete minikube."""

    run(cmd="minikube delete")


@TestStep(When)
def minikube_status(self):
    """Check if minikube is running."""

    try:
        result = run(cmd="minikube status", check=False)
        return result.returncode == 0 and "Running" in result.stdout
    except:
        return False


@TestStep(When)
def minikube_stop(self):
    """Stop minikube."""

    run(cmd="minikube stop")


@TestStep(Given)
def setup_minikube_environment(self, cpus=4, memory="6g", clean_up=True):
    """Set up minikube environment with context."""

    # Check if minikube is already running and stop it if it is
    if minikube_status():
        minikube_stop()

    minikube_start(cpus=cpus, memory=memory)

    use_context(context_name="minikube")

    yield

    if clean_up:
        cleanup_minikube_environment()


@TestStep(Finally)
def cleanup_minikube_environment(self):
    """Clean up minikube environment."""

    minikube_delete()
