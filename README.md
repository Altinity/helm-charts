# Altinity Helm Charts for ClickHouse®

> Helm charts for getting started with ClickHouse® and ClickHouse Keeper.

These samples demonstrate straightforward Helm charts that can be used to deploy ClickHouse and ClickHouse Keeper. The examples are intended as starting points for more complex configurations and do not cover all possible uses cases.

For more complex configurations, consider applying your own `ClickHouseInstallation` and `ClickHouseKeeperInstallation` resources. The [cluster settings documentation](https://docs.altinity.com/altinitykubernetesoperator/kubernetesoperatorguide/kubernetesconfigurationguide/clustersettings/) is a good starting point.

## Prerequisites

To get started, you'll need to:

* Get administrative access to Kubernetes. For testing, [Minikube](https://minikube.sigs.k8s.io/docs/start/) will do the job.
* Install [kubectl](https://kubernetes.io/docs/tasks/tools/)
* Install [helm](https://helm.sh/docs/intro/install/)
* (Optional) Use helm to install the [clickhouse-operator](https://github.com/Altinity/clickhouse-operator/tree/master/deploy/helm) using the commands shown below.

**Installing the Operator first provides better control when uninstalling clusters.**

```sh
helm repo add clickhouse-operator https://docs.altinity.com/clickhouse-operator/
helm install clickhouse-operator clickhouse-operator/altinity-clickhouse-operator --namespace kube-system
```

> Please refer to the Altinity Operator project instructions for details on operator upgrade with Helm, including running custom resource definition files independently.

## Helm Charts

- **[clickhouse](./charts/clickhouse/)**: All-in-one chart to deploy a ClickHouse cluster (and optionally Keeper and the Altinity Operator)
- **[clickhouse-eks](./charts/clickhouse-eks/)**: An EKS-specific chart for high-availability ClickHouse clusters. 

### Deprecated Charts

Since [Release 0.24.0](https://docs.altinity.com/releasenotes/altinity-kubernetes-operator-release-notes/#release-0240) keeper can be managed with a custom resource. These charts are deprecated and may not receive further updates:

- **[clickhouse-keeper-sts](./charts/clickhouse-keeper-sts/)**: Deploys ClickHouse Keeper using StatefulSets for better data persistence.
- **[keeper-sts](./charts/clickhouse-keeper-sts/)**: Deploys ClickHouse Keeper using StatefulSets for better data persistence.

### How to Install a Chart

```sh
# add the kubernetes-blueprints-for-clickhouse chart repository
helm repo add altinity https://helm.altinity.com

# use this command to install any of the avaiable charts
helm install release-name altinity/[chart-name] --namespace clickhouse --create-namespace

# check chart release status
helm status release-name --namespace clickhouse
```

### Using Examples

There are several [examples](./charts/clickhouse/examples) available. You can use them with a command like:


```sh
helm install release-name --namespace clickhouse --create-namespace -f path/to/examples/values-simple.yaml altinity/clickhouse
```

> Please refer to any of helm charts `README` file for detailed instructions about each of the them.

## Contributing
We welcome contributions from the community! If you encounter issues or have improvements to suggest, please log an issue or submit a PR.

## Legal
All code, unless specified otherwise, is licensed under the [Apache-2.0](LICENSE) license.
Copyright (c) 2025 Altinity, Inc.
