

# keeper-ss

![Version: 0.1.0](https://img.shields.io/badge/Version-0.1.0-informational?style=flat-square) ![Type: application](https://img.shields.io/badge/Type-application-informational?style=flat-square) ![AppVersion: 1.16.0](https://img.shields.io/badge/AppVersion-1.16.0-informational?style=flat-square)

A Helm chart for setting up ClickHouse Keeper using StatefulSet

## Installing the Chart

```sh
# add the kubernetes-blueprints-for-clickhouse chart repository
helm repo add kubernetes-blueprints-for-clickhouse https://altinity.github.io/kubernetes-blueprints-for-clickhouse

# use this command to install keeper-ss chart (it will also create a `clickhouse` namespace)
helm install ch kubernetes-blueprints-for-clickhouse/keeper-ss --namespace clickhouse --create-namespace
```

> Use `-f` flag to override default values: `helm install -f newvalues.yaml`

## Upgrading the Chart
```sh
# get latest repository versions
helm repo update

# upgrade to a newer version using the release name (`ch`)
helm upgrade ch kubernetes-blueprints-for-clickhouse/keeper-ss --namespace clickhouse
```

## Uninstalling the Chart

```sh
# uninstall using the release name (`ch`)
helm uninstall ch --namespace clickhouse
```

> This command removes all the Kubernetes components associated with the chart and deletes the release.

## Values

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| all.metadata.labels.application_group | string | `"keeper"` | The name of the application group |
| keeper.image | string | `"altinity/clickhouse-keeper:23.8.8.21.altinitystable"` | ClickHouse ClickHouse Keeper image |
| keeper.listen_host | string | `"0.0.0.0"` | ClickHouse Keeper host IP |
| keeper.name | string | `"keeper"` | Name of the ClickHouse Keeper cluster |
| keeper.replicas | int | `1` | Number of ClickHouse Keeper replicas |
| keeper.storage | string | `"25Gi"` | Storage disk size for ClickHouse Keeper |
| keeper.tcp_port | int | `2181` | ClickHouse Keeper TCP port |
