

# keeper-sts

![Version: 0.1.2](https://img.shields.io/badge/Version-0.1.2-informational?style=flat-square) ![Type: application](https://img.shields.io/badge/Type-application-informational?style=flat-square) ![AppVersion: 1.16.0](https://img.shields.io/badge/AppVersion-1.16.0-informational?style=flat-square)

A Helm chart for setting up ClickHouse Keeper using StatefulSet

Since [Release 0.24.0](https://docs.altinity.com/releasenotes/altinity-kubernetes-operator-release-notes/#release-0240) keeper can be managed with a custom resource. This chart is deprecated and may not receive further updates:

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
