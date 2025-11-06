import subprocess
import sys
import yaml
import tempfile
from pathlib import Path
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

@TestStep(Given)
def get_values_file(self, values):
    """Create a temporary values file for Helm."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        yaml.dump(values, f)
        temp_file = Path(f.name)

    yield str(temp_file)

    temp_file.unlink(missing_ok=True)


@TestStep(When)
def values_argument(self, values=None, values_file=None):
    """Get Helm command arguments for values file or dict.

    Args:
        values: Dictionary of values to use (will be converted to temp file)
        values_file: Path to values file (relative to tests/ directory)

    Returns:
        String with --values argument for helm command, or empty string if no values
    """
    if not values and not values_file:
        return ""
    
    if values_file:
        tests_dir = Path(__file__).parent.parent
        full_path = tests_dir / values_file
        return f" --values {full_path}"
    
    # values dict case - create temp file
    temp_values_file = get_values_file(values=values)
    return f" --values {temp_values_file}"