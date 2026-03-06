<img align="right" style="width: 5em;" src="https://github.com/user-attachments/assets/1e97270f-7925-4cc2-8791-8d0cc77fe512">


# Regression Tests for Altinity ClickHouse Helm Charts

Comprehensive regression test suite for Altinity ClickHouse Helm charts, ensuring proper deployment and configuration of ClickHouse clusters in Kubernetes environments using the [TestFlows](https://testflows.com/) framework.

## 📋 Table of Contents

* [Overview](#-overview)
  * [Test Architecture](#test-architecture)
  * [Test Flow](#test-flow)
* [Directory Structure](#-directory-structure)
* [Test Coverage](#-test-coverage)
  * [What's Covered](#whats-covered)
  * [Test Scenarios](#test-scenarios)
  * [Coverage Gaps](#coverage-gaps)
* [Supported Environment](#-supported-environment)
* [Prerequisites](#-prerequisites)
  * [Kubernetes Cluster](#kubernetes-cluster)
  * [Helm](#helm)
  * [Python Modules](#python-modules)
* [How to Run Tests](#-how-to-run-tests)
  * [Running All Tests](#running-all-tests)
  * [Running Specific Fixtures](#running-specific-fixtures)
  * [Custom Configuration](#custom-configuration)
* [Contributing](#-contributing)
  * [Adding New Test Fixtures](#adding-new-test-fixtures)
  * [Adding New Test Steps](#adding-new-test-steps)
  * [Best Practices](#best-practices)
* [Troubleshooting](#-troubleshooting)
* [Additional Resources](#-additional-resources)

---

## 🏗 Overview

### Test Architecture

The test suite follows a **layered architecture** built on TestFlows:

```
┌─────────────────────────────────────────────────┐
│          run/smoke.py (Entry Point)             │
│  Defines test configuration and runs features   │
└─────────────────┬───────────────────────────────┘
                  │
┌─────────────────▼───────────────────────────────┐
│      scenarios/smoke.py (Test Scenarios)        │
│  Orchestrates test flows and fixture execution  │
└─────────────────┬───────────────────────────────┘
                  │
┌─────────────────▼───────────────────────────────┐
│    steps/ (Reusable Test Operations)            │
│  • clickhouse.py - ClickHouse operations        │
│  • kubernetes.py - K8s resource management      │
│  • helm.py - Helm chart operations              │
│  • users.py - User & permission verification    │
│  • deployment.py - HelmState orchestrator       │
│  • minikube.py - Local cluster management       │
│  • system.py - System utilities                 │
└─────────────────┬───────────────────────────────┘
                  │
┌─────────────────▼───────────────────────────────┐
│         fixtures/ (Test Data)                   │
│  YAML configurations for different deployments  │
└─────────────────────────────────────────────────┘
```

### Test Flow

Each test scenario follows this sequence:

1. **Setup Phase**
   - Configure minikube environment (optional)
   - Set kubectl context
   - Build Helm dependencies

2. **Deployment Phase**
   - Install/upgrade ClickHouse using Helm with fixture values
   - Wait for pods to be created and running

3. **Verification Phase**
   - **HelmState Orchestrator** (`deployment.py`) reads fixture and determines checks
   - Delegates verification to specialized step functions:
     - Pod count and status
     - Cluster topology (shards/replicas)
     - Replication health and functionality
     - User authentication and permissions
     - Persistence (PVCs, storage sizes)
     - Service endpoints and load balancers
     - Pod/service annotations and labels
     - Custom ClickHouse configuration (extraConfig)
     - Keeper availability and storage
     - Resource limits and requests
     - Metrics endpoint accessibility

4. **Chaos Testing** (for replicated setups)
   - Keeper high availability tests
   - Pod failure recovery

5. **Cleanup Phase**
   - Uninstall Helm release
   - Delete namespace
   - Clean up test resources

---

## 📁 Directory Structure

```
tests/
├── README.md                    # This file
├── requirements.txt             # Python dependencies
│
├── run/                         # Test entry points
│   ├── __init__.py
│   └── smoke.py                 # Main test runner (starts here!)
│
├── scenarios/                   # Test orchestration
│   ├── __init__.py
│   └── smoke.py                 # Smoke test scenarios (fixtures + upgrades)
│
├── steps/                       # Reusable test operations
│   ├── __init__.py
│   ├── clickhouse.py            # ClickHouse-specific operations (1383 lines)
│   ├── kubernetes.py            # Kubernetes resource management
│   ├── helm.py                  # Helm install/upgrade/uninstall
│   ├── deployment.py            # HelmState orchestrator
│   ├── users.py                 # User verification and permissions
│   ├── minikube.py              # Local cluster setup
│   └── system.py                # Shell command utilities
│
├── fixtures/                    # Test configurations (YAML)
│   ├── 01-minimal-single-node.yaml          # Baseline: 1 node
│   ├── 02-replicated-with-users.yaml        # 3 replicas + 3 keepers + users
│   ├── 03-sharded-advanced.yaml             # 3 shards × 2 replicas + 5 keepers
│   ├── 04-external-keeper.yaml              # External keeper (commented out)
│   ├── 05-persistence-disabled.yaml         # Ephemeral storage
│   ├── 06-eks-multi-zone-production.yaml    # Production-like EKS config
│   ├── 07-eks-io-optimized.yaml             # I/O optimized EKS config
│   └── upgrade/
│       ├── initial.yaml                     # Pre-upgrade state
│       └── upgrade.yaml                     # Post-upgrade state
│
├── helpers/                     # Test utilities
│   ├── __init__.py
│   └── argparser.py             # Command-line argument parser
│
└── requirements/                # Requirement definitions
    ├── __init__.py
    ├── helm.py                  # Helm requirement checks
    └── helm.md                  # Helm requirement documentation
```

---

## ✅ Test Coverage

### What's Covered

The test suite provides comprehensive coverage across multiple dimensions:

#### **1. Deployment Configurations**
- ✅ Single-node minimal deployment
- ✅ Multi-replica deployments (2-3 replicas)
- ✅ Sharded clusters (up to 3 shards × 2 replicas)
- ✅ Keeper integration (3-5 replicas)
- ✅ External keeper configurations
- ✅ Persistence (enabled/disabled)
- ✅ Ephemeral storage deployments

#### **2. ClickHouse Functionality**
- ✅ Version verification
- ✅ Connection testing
- ✅ Server-side TLS/SSL and HTTPS
- ✅ Query execution
- ✅ Cluster topology (system.clusters)
- ✅ Replication health (system.replicas)
- ✅ Data replication verification (create + replicate test tables)
- ✅ Metrics endpoint accessibility
- ✅ Custom configuration (extraConfig XML)
- ✅ Keeper high availability (chaos tests)

#### **3. User Management**
- ✅ Default user authentication
- ✅ Multiple user creation
- ✅ SHA256 password hashing
- ✅ User grants and permissions
- ✅ Access management settings
- ✅ Host IP restrictions (network policies)
- ✅ Read-only user verification

#### **4. Kubernetes Resources**
- ✅ Pod creation and readiness
- ✅ Service endpoints
- ✅ Persistent Volume Claims (PVCs)
- ✅ Storage size verification
- ✅ Access modes (ReadWriteOnce, etc.)
- ✅ Pod annotations and labels
- ✅ Service annotations and labels
- ✅ LoadBalancer services with source ranges
- ✅ Service accounts
- ✅ Secrets management

#### **5. Advanced Features**
- ✅ Anti-affinity configurations
- ✅ Node selectors
- ✅ Tolerations
- ✅ Topology spread constraints
- ✅ Resource limits and requests (CPU, memory)
- ✅ Log persistence (separate volumes)
- ✅ Custom namespace domain patterns
- ✅ Cluster secrets
- ✅ Custom names (nameOverride)

#### **6. Upgrade Scenarios**
- ✅ Helm chart upgrades
- ✅ Configuration changes
- ✅ Data survival verification
- ✅ In-place vs. cluster replacement upgrades
- ✅ Topology changes during upgrade

### Test Scenarios

Currently implemented test scenarios:

| Scenario | Fixture | Pods | Description |
|----------|---------|------|-------------|
| **Minimal Deployment** | `01-minimal-single-node.yaml` | 1 | Baseline test: single ClickHouse node, no keeper |
| **Replicated + Users** | `02-replicated-with-users.yaml` | 6 | 3 replicas + 3 keepers, comprehensive user setup |
| **Sharded Advanced** | `03-sharded-advanced.yaml` | 11 | 3 shards × 2 replicas + 5 keepers, advanced K8s features |
| **External Keeper** | `04-external-keeper.yaml` | 4 | Uses external keeper (currently disabled in tests) |
| **Ephemeral Storage** | `05-persistence-disabled.yaml` | 5 | No persistent volumes, 2 replicas + 3 keepers |
| **EKS Multi-Zone** | `06-eks-multi-zone-production.yaml` | TBD | Production-like EKS configuration |
| **EKS I/O Optimized** | `07-eks-io-optimized.yaml` | TBD | I/O optimized EKS configuration |
| **Upgrade Test** | `upgrade/initial.yaml` → `upgrade/upgrade.yaml` | Variable | Tests upgrade path and data survival |

**Currently Active Tests**: Fixtures 01, 02, and upgrade scenario  
**Commented Out**: Fixtures 03, 04, 05 (TODO)

### Coverage Gaps

Areas that **need additional testing or are not fully covered**:

#### **1. Missing Test Coverage**
- ❌ **Backup and restore** - No automated backup/restore testing
- ❌ **Disaster recovery** - No full cluster failure scenarios
- ❌ **Network policies** - Limited testing of K8s network restrictions
- ❌ **Monitoring integration** - Prometheus scraping tested only via annotations
- ❌ **Logging integration** - No FluentD/ElasticSearch integration tests
- ❌ **Multi-cluster** - No federation or distributed query tests
- ❌ **Horizontal scaling** - No dynamic scale-up/scale-down tests
- ❌ **Performance benchmarks** - No load testing or performance metrics
- ❌ **Cloud-specific features** - AWS EKS, GKE, AKS specific integrations
- ❌ **Storage classes** - Limited testing of different storage backends
- ❌ **Resource quotas** - No namespace quota testing
- ❌ **RBAC** - Limited Kubernetes RBAC testing
- ❌ **Init containers** - No custom init container testing
- ❌ **Sidecar containers** - No sidecar pattern testing

#### **2. Partial Coverage**
- ⚠️ **Metrics** - Only endpoint accessibility tested, not actual metric values
- ⚠️ **Keeper HA** - Basic chaos test exists, but limited scenarios
- ⚠️ **Upgrade paths** - Only one upgrade scenario tested
- ⚠️ **Configuration drift** - No testing of manual changes vs. Helm state
- ⚠️ **Resource exhaustion** - No OOM or disk full scenarios
- ⚠️ **Long-running stability** - Tests are short-lived (minutes, not hours/days)


---

## 🌍 Supported Environment

- **Operating System**: [Ubuntu](https://ubuntu.com/) 22.04 / 24.04
- **Python**: >= 3.10.12, <= 3.12 (3.13+ has `lzma` package that is incompatible with the test framework)
- **Kubernetes**: >= 1.24
- **Helm**: >= 3.8.0
- **Minikube**: >= 1.28.0 (for local testing)
- **Docker**: Required as Minikube driver
  - (alternatively) **OrbStack**: >= 2.0
- **kubectl**: Latest stable version

---

## 📦 Prerequisites

### Kubernetes Cluster

You need access to a Kubernetes cluster. For **local testing**, two providers are supported:

#### Option 1: Minikube (default)

```bash
# Install Minikube
curl -LO https://storage.googleapis.com/minikube/releases/latest/minikube-linux-amd64
sudo install minikube-linux-amd64 /usr/local/bin/minikube

# Verify installation
minikube version
```

#### Option 2: OrbStack (account required, may need license)

1. Install OrbStack by following the [_Quick start_ guide \(docs.orbstack.dev\)](
   https://docs.orbstack.dev/quick-start#installation).
2. Enable Kubernetes in OrbStack:
    1. Open the OrbStack app
    2. Go to Settings... (`Cmd ⌘ + ,`) → Kubernetes
    3. Toggle the `Enable Kubernetes cluster` option
    4. Click the `Apply and Restart` button
3. Verify that OrbStack is running.
    ```sh
    $ orb status
    # Running
    ```
4. Verify the Kubernetes context.
    ```sh
    $ kubectl config get-contexts orbstack
    # CURRENT   NAME       CLUSTER    AUTHINFO   NAMESPACE
    # *         orbstack   orbstack   orbstack
    ```

### Helm

Install Helm 3:

```bash
# Install Helm
curl https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash

# Verify installation
helm version
```

### Python Modules

Install required Python dependencies:

```bash
# From the repository root
pip3 install -r tests/requirements.txt
```

**Dependencies**:
- `testflows==2.4.13` - Test framework
- `testflows.texts==2.0.211217.1011222` - Text utilities
- `PyYAML==6.0.1` - YAML parsing
- `requests==2.32.3` - HTTP requests
- `cryptography==46.0.5` - TLS validation

---

## 🚀 How to Run Tests

### Running All Tests

To run the complete test suite (all active fixtures + upgrades):

```bash
# From the repository root
# With Minikube (default)
python3 ./tests/run/smoke.py

# With OrbStack
LOCAL_K8S_PROVIDER=orbstack python3 ./tests/run/smoke.py
```

This will:
1. \[Minikube only\] Start/restart Minikube with 4 CPUs and 6GB memory
2. Run all enabled fixture deployments
3. Run upgrade scenarios
4. \[Minikube only\] Clean up and delete Minikube

**Expected Duration**: 10 minutes 

### Running Specific Fixtures

To run tests for a specific configuration, modify `tests/scenarios/smoke.py`:

```python
# Edit FIXTURES list to include only desired fixtures
FIXTURES = [
    "fixtures/01-minimal-single-node.yaml",  # Only run minimal test
]
```

Or comment out the upgrade tests:

```python
@TestFeature
@Name("comprehensive")
def feature(self):
    """Run all comprehensive smoke tests."""
    
    with Given("minikube environment"):
        minikube.setup_minikube_environment()
        kubernetes.use_context(context_name="minikube")
    
    Feature(run=check_all_fixtures)
    
    # Feature(run=check_all_upgrades)  # Commented out
```

### Custom Configuration

You can override test settings by modifying `tests/run/smoke.py`:

```python
@TestModule
@Name("smoke")
@ArgumentParser(argparser)
def regression(self, feature):
    """Execute smoke tests."""
    
    # Use remote chart instead of local
    self.context.altinity_repo = "https://helm.altinity.com"
    self.context.version = "25.3.6.10034.altinitystable"
    
    # Or use local chart (default)
    self.context.local_chart_path = os.path.join(os.getcwd(), "charts", "clickhouse")
    
    Feature(run=load(f"tests.scenarios.smoke", "feature"))
```

**Minikube resource customization** in `tests/steps/minikube.py`:

```python
def setup_minikube_environment(self, cpus=4, memory="6g", clean_up=True):
    # Increase resources for larger deployments
    # cpus=8, memory="12g"
```

---

## 🤝 Contributing

### Adding New Test Fixtures

Test fixtures define Helm values for different deployment scenarios.

**1. Create a new fixture file**:

```bash
# Create a new fixture
touch tests/fixtures/08-my-custom-config.yaml
```

**2. Define the configuration**:

```yaml
---
# tests/fixtures/08-my-custom-config.yaml
# Custom configuration for testing feature X
# Expected pods: 2 ClickHouse + 3 Keeper = 5 total
nameOverride: "custom"

clickhouse:
  replicasCount: 2
  shardsCount: 1
  
  defaultUser:
    password: "CustomPassword123"
  
  persistence:
    enabled: true
    size: 5Gi
  
  # Add your custom configuration here
  service:
    type: LoadBalancer

keeper:
  enabled: true
  replicaCount: 3

operator:
  enabled: true
```

**3. Add fixture to test scenarios**:

```python
# Edit tests/scenarios/smoke.py
FIXTURES = [
    "fixtures/01-minimal-single-node.yaml",
    "fixtures/02-replicated-with-users.yaml",
    "fixtures/08-my-custom-config.yaml",  # Add your fixture
]
```
**4. Add missing verification steps in HelmState and step files if needed**.

**5. Run the test**:

```bash
python3 ./tests/run/smoke.py
```

### Adding New Test Steps

Test steps are reusable operations in the `tests/steps/` directory.

**Example: Adding a new ClickHouse verification step**:

```python
# In tests/steps/clickhouse.py

@TestStep(Then)
def verify_custom_setting(self, namespace, expected_value, admin_password=""):
    """Verify a custom ClickHouse setting."""
    clickhouse_pods = get_clickhouse_pods(namespace=namespace)
    assert len(clickhouse_pods) > 0, "No ClickHouse pods found"
    
    pod_name = clickhouse_pods[0]
    
    query = "SELECT value FROM system.settings WHERE name = 'custom_setting'"
    result = execute_clickhouse_query(
        namespace=namespace,
        pod_name=pod_name,
        query=query,
        user="default",
        password=admin_password,
        check=True
    )
    
    actual_value = result.stdout.strip()
    assert actual_value == expected_value, \
        f"Expected custom_setting={expected_value}, got {actual_value}"
    
    note(f"✓ Custom setting verified: {expected_value}")
```

**Using the new step in HelmState** (`tests/steps/deployment.py`):

```python
class HelmState:
    # ... existing code ...
    
    def verify_custom_config(self, namespace):
        """Verify custom configuration."""
        custom_value = self.clickhouse_config.get("customSetting")
        
        if custom_value:
            admin_password = self.clickhouse_config.get("defaultUser", {}).get("password", "")
            clickhouse.verify_custom_setting(
                namespace=namespace,
                expected_value=custom_value,
                admin_password=admin_password
            )
            note(f"✓ Custom config verified")
    
    def verify_all(self, namespace):
        # ... existing checks ...
        
        if self.clickhouse_config.get("customSetting"):
            self.verify_custom_config(namespace=namespace)
```

### Best Practices

When contributing tests, follow these guidelines:

#### **1. Test Independence**
- ✅ Tests should be **idempotent** (can run multiple times)
- ✅ Always **clean up** resources in `Finally` blocks
- ✅ Don't rely on state from previous tests
- ✅ Use unique namespaces per test

#### **2. Error Handling**
- ✅ Add proper **assertions** with descriptive messages
- ✅ Use **timeouts** to prevent hanging tests
- ✅ Log detailed **debugging info** on failures
- ✅ Handle edge cases (e.g., missing pods, failed queries)

#### **3. Code Organization**
- ✅ Keep **steps** reusable and atomic
- ✅ Put orchestration logic in **scenarios**
- ✅ Store configuration in **fixtures**
- ✅ Use descriptive function and variable names

#### **4. Documentation**
- ✅ Add **docstrings** to all functions
- ✅ Include **comments** explaining complex logic
- ✅ Document **expected behavior** in fixtures
- ✅ Update this README when adding major features

#### **5. TestFlows Conventions**
- ✅ Use `@TestStep` decorators with appropriate levels:
  - `@TestStep(Given)` - Setup operations
  - `@TestStep(When)` - Actions
  - `@TestStep(Then)` - Assertions
  - `@TestStep(Finally)` - Cleanup
- ✅ Use `note()` for informational messages
- ✅ Use `with Given/When/Then/And/Finally` blocks for clarity
- ✅ Leverage context variables (`self.context`) for shared state

---

## 🔧 Troubleshooting


### Manual Testing

To manually replicate a test:

```bash
# Start Minikube
minikube start --driver=docker --cpus=4 --memory=6g

# Set context
kubectl config use-context minikube

# Install chart with fixture
helm install test-deploy ./charts/clickhouse \
  --namespace test-ns \
  --create-namespace \
  --values tests/fixtures/01-minimal-single-node.yaml

# Wait and verify
kubectl get pods -n test-ns -w

# Cleanup
helm uninstall test-deploy -n test-ns
kubectl delete namespace test-ns
```



---

## 📚 Additional Resources

- **TestFlows Documentation**: https://testflows.com/
- **Helm Charts Repository**: https://github.com/Altinity/clickhouse-operator
- **ClickHouse Documentation**: https://clickhouse.com/docs/
- **Kubernetes Documentation**: https://kubernetes.io/docs/

---

## 📝 License

This test suite is part of the Altinity ClickHouse Helm Charts repository and follows the same license.

---

**Happy Testing! 🚀**

For questions or issues, please open an issue in the GitHub repository.
