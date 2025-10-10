import subprocess
import sys
from testflows.core import *


@TestStep(When)
def run(self, cmd, check=True):
    """Execute a shell command."""
    note(f"> {cmd}")
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)

    if check and result.returncode != 0:
        note(result.stderr)
        sys.exit(result.returncode)

    return result

