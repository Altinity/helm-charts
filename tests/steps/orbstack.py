from tests.steps.system import *
from tests.steps.kubernetes import use_context


CONTEXT_NAME = "orbstack"


@TestStep(Given)
def orbstack_start(self):
    """Start OrbStack."""

    if orbstack_status():
        return

    run(cmd="orbctl start")


@TestStep(When)
def orbstack_status(self):
    """Check if OrbStack is running."""

    try:
        result = run(cmd="orbctl status", check=False)
        return result.returncode == 0 and "Running" in result.stdout
    except:
        return False


@TestStep(Given)
def setup_orbstack_environment(self, clean_up=True):
    """Set up OrbStack environment with context."""

    orbstack_start()

    use_context(context_name=CONTEXT_NAME)

    yield

    if clean_up:
        cleanup_orbstack_environment()


@TestStep(Finally)
def cleanup_orbstack_environment(self):
    """Clean up OrbStack environment."""

    note("OrbStack environment lifecycle is managed outside of this framework.")
