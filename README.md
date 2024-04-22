# Kubernetes Blueprints for ClickHouse

> Collection of samples to getting started with ClickHouse and ClickHouse Keeper

These samples demonstrate straightforward Helm charts that can be used to deploy ClickHouse and ClickHouse Keeper. The examples are intended as starting points for more complex configurations and do not cover all possible uses cases.

**⚠️ Important notes:**

1. ClickHouse Keeper resources (CHK) are not stable yet and should not be used in production environments.
2. Connections are unencrypted. Avoid using them for sensitive data.
3. Selecting the external `LoadBalancer` service type in `values.yaml` will expose one or more ports to the Internet, which can pose security risks.

## Prerequisites

To get started, you'll need to:

* Get administrative access to Kubernetes. For testing, [Minikube](https://minikube.sigs.k8s.io/docs/start/) will do the job.
* Install [kubectl](https://kubernetes.io/docs/tasks/tools/)
* Install [helm](https://helm.sh/docs/intro/install/)
* Use helm to install the [clickhouse-operator](https://github.com/Altinity/clickhouse-operator/tree/master/deploy/helm) using the commands shown below.


```sh
helm repo add clickhouse-operator https://docs.altinity.com/clickhouse-operator/
helm install clickhouse-operator clickhouse-operator/altinity-clickhouse-operator
```

> Please refer to the Altinity Operator project instructions for details on operator upgrade with Helm, including running custom resource definition files independently.

## Helm Charts

- **[clickhouse-eks](./helm/clickhouse-eks/)**: Deploys ClickHouse optimized for AWS EKS.
- **[keeper-sts](./helm/keeper-sts/)**: Deploys ClickHouse Keeper using StatefulSets for better data persistence.

### How to Install a Chart

```sh
# add the kubernetes-blueprints-for-clickhouse chart repository
helm repo add kubernetes-blueprints-for-clickhouse https://altinity.github.io/kubernetes-blueprints-for-clickhouse

# use this command to install any of the avaiable charts
helm install ch kubernetes-blueprints-for-clickhouse/[chart-name] --namespace clickhouse --create-namespace

# check chart release status
helm status ch ---namespace clickhouse
```

> Please refer to any of helm charts `README` file for detailed instructions about each of the them.

## Contributing
We welcome contributions from the community! If you encounter issues or have improvements to suggest, please log an issue or submit a PR.

## Legal
All code, unless specified otherwise, is licensed under the [Apache-2.0](LICENSE) license.
Copyright (c) 2024 Altinity, Inc.
