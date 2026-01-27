#!/usr/bin/env python3
"""
Validation Tests for ClickHouse Helm Chart

Tests that Helm chart validation checks work correctly by verifying
that helm template fails with appropriate error messages for invalid
configurations.

Run with: python3 ./tests/run/validation.py
"""

import subprocess
import sys
import os

# Chart path relative to repo root
CHART_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "charts", "clickhouse")


def run_helm_template(set_values: list[str]) -> tuple[int, str, str]:
    """Run helm template with given --set values and return exit code, stdout, stderr."""
    cmd = ["helm", "template", "test", CHART_PATH]
    for val in set_values:
        cmd.extend(["--set", val])

    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.returncode, result.stdout, result.stderr


def test_keeper_required_validation():
    """Test that keeper is required when replicasCount > 1."""
    print("Testing: keeper required when replicasCount > 1...")

    # Should fail: replicasCount=2 without keeper
    exit_code, stdout, stderr = run_helm_template([
        "clickhouse.replicasCount=2",
        "keeper.enabled=false",
    ])

    assert exit_code != 0, "Expected helm template to fail"
    assert "keeper.enabled" in stderr, f"Expected error about keeper.enabled, got: {stderr}"
    assert "replicasCount" in stderr or "clickhouse.zones" in stderr, f"Expected mention of replicasCount or zones: {stderr}"

    print("  ✓ Correctly fails when replicasCount > 1 without keeper")

    # Should pass: replicasCount=2 with keeper enabled
    exit_code, stdout, stderr = run_helm_template([
        "clickhouse.replicasCount=2",
        "keeper.enabled=true",
        "keeper.replicaCount=3",
    ])

    assert exit_code == 0, f"Expected helm template to succeed, got: {stderr}"
    print("  ✓ Correctly passes when replicasCount > 1 with keeper enabled")

    # Should pass: replicasCount=2 with external keeper host
    exit_code, stdout, stderr = run_helm_template([
        "clickhouse.replicasCount=2",
        "keeper.enabled=false",
        "clickhouse.keeper.host=external-keeper",
    ])

    assert exit_code == 0, f"Expected helm template to succeed, got: {stderr}"
    print("  ✓ Correctly passes when using external keeper host")


def test_keeper_odd_replicas_validation():
    """Test that keeper replicaCount must be odd."""
    print("Testing: keeper replicaCount must be odd...")

    # Should fail: even replica count
    exit_code, stdout, stderr = run_helm_template([
        "keeper.enabled=true",
        "keeper.replicaCount=2",
    ])

    assert exit_code != 0, "Expected helm template to fail"
    assert "odd" in stderr.lower(), f"Expected error about odd number, got: {stderr}"
    assert "2" in stderr, f"Expected current value in error: {stderr}"

    print("  ✓ Correctly fails with even replicaCount (2)")

    # Should fail: another even number
    exit_code, stdout, stderr = run_helm_template([
        "keeper.enabled=true",
        "keeper.replicaCount=4",
    ])

    assert exit_code != 0, "Expected helm template to fail"
    print("  ✓ Correctly fails with even replicaCount (4)")

    # Should pass: odd replica count
    for count in [1, 3, 5]:
        exit_code, stdout, stderr = run_helm_template([
            "keeper.enabled=true",
            f"keeper.replicaCount={count}",
        ])

        assert exit_code == 0, f"Expected helm template to succeed with replicaCount={count}, got: {stderr}"
        print(f"  ✓ Correctly passes with odd replicaCount ({count})")


def test_aggregated_errors():
    """Test that multiple validation errors are shown together."""
    print("Testing: aggregated error messages...")

    # Trigger multiple errors at once
    exit_code, stdout, stderr = run_helm_template([
        "clickhouse.replicasCount=2",
        "keeper.enabled=true",
        "keeper.replicaCount=2",  # Even number - error
        "clickhouse.keeper.host=",  # No external keeper
    ])

    assert exit_code != 0, "Expected helm template to fail"
    # Should show odd replicas error (keeper required is satisfied since keeper.enabled=true)
    assert "odd" in stderr.lower(), f"Expected odd replicas error: {stderr}"

    print("  ✓ Shows validation errors in aggregated format")


def main():
    """Run all validation tests."""
    print("=" * 60)
    print("ClickHouse Helm Chart Validation Tests")
    print("=" * 60)
    print()

    # Verify helm is available
    result = subprocess.run(["helm", "version", "--short"], capture_output=True, text=True)
    if result.returncode != 0:
        print("ERROR: helm is not installed or not in PATH")
        sys.exit(1)
    print(f"Using Helm: {result.stdout.strip()}")
    print()

    # Verify chart exists
    if not os.path.exists(CHART_PATH):
        print(f"ERROR: Chart not found at {CHART_PATH}")
        sys.exit(1)

    tests = [
        test_keeper_required_validation,
        test_keeper_odd_replicas_validation,
        test_aggregated_errors,
    ]

    failed = 0
    for test in tests:
        try:
            test()
            print()
        except AssertionError as e:
            print(f"  ✗ FAILED: {e}")
            print()
            failed += 1
        except Exception as e:
            print(f"  ✗ ERROR: {e}")
            print()
            failed += 1

    print("=" * 60)
    if failed == 0:
        print(f"All {len(tests)} tests passed! ✓")
        sys.exit(0)
    else:
        print(f"{failed}/{len(tests)} tests failed ✗")
        sys.exit(1)


if __name__ == "__main__":
    main()
