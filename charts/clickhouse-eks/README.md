# clickhouse-eks

![Version: 0.1.8](https://img.shields.io/badge/Version-0.1.8-informational?style=flat-square) ![Type: application](https://img.shields.io/badge/Type-application-informational?style=flat-square) ![AppVersion: 1.16.0](https://img.shields.io/badge/AppVersion-1.16.0-informational?style=flat-square)

A Helm chart for ClickHouse running on AWS EKS across AZs using a nodeSelector to pin resources to run on specific VMs types

## Installing the Chart

```sh
# add the altinity chart repository
helm repo add altinity https://helm.altinity.com

# use this command to install clickhouse-eks chart (it will also create a `clickhouse` namespace)
helm install clickhouse altinity/clickhouse-eks --namespace clickhouse --create-namespace
```

> Use `-f` flag to override default values: `helm install -f newvalues.yaml`

## Upgrading the Chart
```sh
# get latest repository versions
helm repo update

# upgrade to a newer version using the release name (`clickhouse`)
helm upgrade clickhouse altinity/clickhouse-eks --namespace clickhouse
```

## Uninstalling the Chart

```sh
# uninstall using the release name (`clickhouse`)
helm uninstall clickhouse --namespace clickhouse
```

> This command removes all the Kubernetes components associated with the chart and deletes the release.

## Connecting to your ClickHouse Cluster

```sh
# list your pods
kubectl get pods --namespace clickhouse

# pick any of your available pods and connect through the clickhouse-client
kubectl exec -it chi-eks-dev-0-0-0 --namespace clickhouse -- clickhouse-client
```

> Use `kubectl port forward` to access your ClickHouse cluster from outside: `kubectl port-forward service clickhouse-eks 9000:9000 & clickhouse-client`

## Values

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| all.metadata.labels.application_group | string | `"eks"` | The name of the application group |
| clickhouse.cluster | string | `"dev"` | Cluster name |
| clickhouse.extraContainers | object | `{}` | Extra containers for clickhouse pods |
| clickhouse.extraVolumes | object | `{}` | Extra volumes for clickhouse pods |
| clickhouse.image | string | `"altinity/clickhouse-server:24.3.12.76.altinitystable"` | ClickHouse server image |
| clickhouse.keeper_name | string | `"keeper-eks"` | Name of the keeper cluster |
| clickhouse.name | string | `"eks"` | Metadata name |
| clickhouse.node_selector | string | `"m6i.large"` | AWS instance type |
| clickhouse.password | string | `nil` | ClickHouse user password |
| clickhouse.service_type | string | `"cluster-ip"` | Possible service types are `cluster-ip`, `internal-loadbalancer` and `external-loadbalancer` |
| clickhouse.storage | string | `"50Gi"` | Storage size for ClickHouse data |
| clickhouse.storage_class_name | string | `"gp2"` | Storage class for ClickHouse data |
| clickhouse.user | string | `"default"` | ClickHouse user name |
| clickhouse.zones | list | `["us-east-1a","us-east-1a","us-east-1c"]` | AWS availability zones for creating replicas |