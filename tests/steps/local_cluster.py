from tests.steps.system import *
import tests.steps.orbstack as orbstack
import tests.steps.minikube as minikube
import os


def resolve_provider():
    LOCAL_K8S_PROVIDER = os.environ.get("LOCAL_K8S_PROVIDER", "minikube").lower()
    if LOCAL_K8S_PROVIDER not in (orbstack.CONTEXT_NAME, minikube.CONTEXT_NAME):
        raise ValueError(f"Unknown LOCAL_K8S_PROVIDER: {LOCAL_K8S_PROVIDER}. "
                         "Supported values: "
                         f"'{minikube.CONTEXT_NAME}', "
                         f"'{orbstack.CONTEXT_NAME}'")

    return LOCAL_K8S_PROVIDER


@TestStep(Given)
def setup_local_cluster(self):
    """Set up a local Kubernetes cluster."""
    provider = resolve_provider()
    note(f"Using local Kubernetes provider: {provider}")

    if provider == "minikube":
        minikube.setup_minikube_environment()
    elif provider == "orbstack":
        orbstack.setup_orbstack_environment()


def get_context_name():
    # This is okay since the provider is tightly-coupled to the context name
    return resolve_provider()
