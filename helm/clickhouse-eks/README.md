

# clickhouse-eks

![Version: 0.1.0](https://img.shields.io/badge/Version-0.1.0-informational?style=flat-square) ![Type: application](https://img.shields.io/badge/Type-application-informational?style=flat-square) ![AppVersion: 1.16.0](https://img.shields.io/badge/AppVersion-1.16.0-informational?style=flat-square)

A Helm chart for ClickHouse running on AWS EKS across AZs using a nodeSelector to pin resources to run on specific VMs types

## Install

```sh
# add the kubernetes-blueprints-for-clickhouse chart repository
helm repo add kubernetes-blueprints-for-clickhouse https://altinity.github.io/kubernetes-blueprints-for-clickhouse

# use this command to install any of the avaiable charts
helm install ch kubernetes-blueprints-for-clickhouse/clickhouse-eks
```

> Use `-f` flag to override default values: `helm install -f newvalues.yaml`

## Upgrade
```
# upgrade to a newer version using the release name (`ch`)
helm upgrade ch kubernetes-blueprints-for-clickhouse/clickhouse-eks
```

## Uninstall

```sh
# uninstall using the release name (`ch`)
helm uninstall ch
```

## Values

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| all.metadata.labels.application_group | string | `"eks"` |  |
| clickhouse.cluster | string | `"dev"` | Cluster name |
| clickhouse.image | string | `"altinity/clickhouse-server:23.8.8.21.altinitystable"` |  |
| clickhouse.keeper_name | string | `"keeper-eks"` | Name of the keeper cluster |
| clickhouse.name | string | `"eks"` | Metadata name |
| clickhouse.node_selector | string | `"m6i.large"` | AWS instance type |
| clickhouse.password | string | `nil` | - ClickHouse user password |
| clickhouse.service_type | string | `"cluster-ip"` | Possible service types are `cluster-ip`, `internal-loadbalancer` and `external-loadbalancer` |
| clickhouse.storage | string | `"50Gi"` |  |
| clickhouse.storage_class_name | string | `"gp2"` |  |
| clickhouse.user | string | `"default"` | - ClickHouse user name |
| clickhouse.zones | list | `["us-east-1a","us-east-1a","us-east-1c"]` | AWS availability zones for creating replicas |
