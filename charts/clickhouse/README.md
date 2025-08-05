# clickhouse

![Version: 0.3.0-dev](https://img.shields.io/badge/Version-0.3.0--dev-informational?style=flat-square) ![Type: application](https://img.shields.io/badge/Type-application-informational?style=flat-square) ![AppVersion: 24.8.14.10459](https://img.shields.io/badge/AppVersion-24.8.14.10459-informational?style=flat-square)

A Helm chart for creating a ClickHouse® Cluster with the Altinity Operator for ClickHouse

## Features

- Single-node or multi-node ClickHouse clusters
- Sharding and replication
- ClickHouse Keeper integration
- Persistent storage configuration
- Init scripts

## Requirements

| Repository | Name | Version |
|------------|------|---------|
| https://docs.altinity.com/clickhouse-operator | operator(altinity-clickhouse-operator) | 0.25.2 |

## Installing the Chart

```sh
# add the altinity chart repository
helm repo add altinity https://helm.altinity.com

# use this command to install clickhouse chart (it will also create a `clickhouse` namespace)
helm install release-name altinity/clickhouse --namespace clickhouse --create-namespace
```

Note that by default the chart includes the Altinity Operator. For most production use cases you will want to disable this and install the operator explicitly from its own helm chart.

```sh
# add the altinity operator chart repository
helm repo add altinity-operator https://docs.altinity.com/clickhouse-operator

# create the namespace
kubectl create namespace clickhouse

# install operator into namespace
helm install clickhouse-operator altinity-docs/altinity-clickhouse-operator \
--namespace clickhouse

# add the altinity chart repository
helm repo add altinity https://helm.altinity.com

# install the clickhouse chart without the operator
helm install release-name altinity/clickhouse --namespace clickhouse \
--set operator.enabled=false
```

> Yes, we're aware that the domains for the helm repos are a bit odd. We're working on it.

## Upgrading the Chart

### Upgrading from 0.2.x to 0.3.0

**IMPORTANT**: Version 0.3.0 introduces a change that improves reconciliation timing by embedding templates directly in the ClickHouseInstallation resource instead of using separate ClickHouseInstallationTemplate resources.

After upgrading, delete the old ClickHouseInstallationTemplate resources that were created by version 0.2.x:

```sh
# List all ClickHouseInstallationTemplate resources
kubectl get clickhouseinstallationtemplates -n clickhouse

# Delete them (replace <release-name> with your actual release name)
kubectl delete clickhouseinstallationtemplates -n clickhouse \
  <release-name>-clickhouse-pod \
  <release-name>-clickhouse-service \
  <release-name>-clickhouse-service-lb \
  <release-name>-clickhouse-data \
  <release-name>-clickhouse-logs
```

The ClickHouseInstallation will be updated automatically with embedded templates, resulting in faster reconciliation.

### Standard Upgrade Process
```sh
# get latest repository versions
helm repo update

# upgrade to a newer version using the release name (`clickhouse`)
helm upgrade clickhouse altinity/clickhouse --namespace clickhouse
```

## Uninstalling the Chart

```sh
# uninstall using the release name (`clickhouse`)
helm uninstall clickhouse --namespace clickhouse
```

**Note:** If you installed the Altinity Operator with this chart, your ClickHouse Installations will hang because the Operator will be deleted before their finalizers complete. To resolve this you must manually edit each `chi` resource and remove the finalizer.

PVCs created by this helm chart will not be automatically deleted and must be deleted manually. An easy way to do this is to delete the namespace:

```sh
kubectl delete namespace clickhouse
```

> This command removes all the Kubernetes components associated with the chart and deletes the release.

## Connecting to your ClickHouse Cluster

```sh
# list your pods
kubectl get pods --namespace clickhouse

# pick any of your available pods and connect through the clickhouse-client
kubectl exec -it chi-clickhouse-0-0-0 --namespace clickhouse -- clickhouse-client
```

> Use `kubectl port forward` to access your ClickHouse cluster from outside: `kubectl port-forward service clickhouse-eks 9000:9000 & clickhouse-client`

## Using Init Scripts with ConfigMap

The chart allows mounting a ConfigMap containing initialization scripts that will be executed during the ClickHouse container startup.

### How to use:

1. Create a ConfigMap containing your initialization scripts:

```bash
kubectl create configmap my-init-scripts --from-file=01_create_database.sh --from-file=02_create_tables.sh
```

2. Enable the initScripts feature in your Helm values:

```yaml
clickhouse:
  initScripts:
    enabled: true
    configMapName: my-init-scripts
    alwaysRun: true  # Set to true to always run scripts on container restart
```

The scripts will be mounted at `/docker-entrypoint-initdb.d/` in the ClickHouse container and executed in alphabetical order during startup.

### Example Script Format

```bash
#!/bin/bash
set -e
clickhouse client -n <<-EOSQL
  CREATE DATABASE IF NOT EXISTS my_database;
  CREATE TABLE IF NOT EXISTS my_database.my_table (
    id UInt64,
    data String
  ) ENGINE = MergeTree()
  ORDER BY id;
EOSQL
```

## Values

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| clickhouse.antiAffinity | bool | `false` |  |
| clickhouse.clusterSecret | object | `{"auto":true,"enabled":false,"value":"","valueFrom":{"secretKeyRef":{"key":"secret","name":""}}}` | Cluster secret configuration for secure inter-node communication |
| clickhouse.clusterSecret.auto | bool | `true` | Auto-generate cluster secret (recommended for security) |
| clickhouse.clusterSecret.enabled | bool | `false` | Whether to enable secure cluster communication |
| clickhouse.clusterSecret.value | string | `""` | Plaintext cluster secret value (not recommended for production) |
| clickhouse.clusterSecret.valueFrom | object | `{"secretKeyRef":{"key":"secret","name":""}}` | Reference to an existing Kubernetes secret containing the cluster secret |
| clickhouse.clusterSecret.valueFrom.secretKeyRef.key | string | `"secret"` | Key in the secret that contains the cluster secret value |
| clickhouse.clusterSecret.valueFrom.secretKeyRef.name | string | `""` | Name of the secret containing the cluster secret |
| clickhouse.defaultUser.allowExternalAccess | bool | `false` | Allow the default user to access ClickHouse from any IP. If set, will override `hostIP` to always be `0.0.0.0/0`. |
| clickhouse.defaultUser.hostIP | string | `"127.0.0.1/32"` |  |
| clickhouse.defaultUser.password | string | `""` |  |
| clickhouse.extraConfig | string | `"<clickhouse>\n</clickhouse>\n"` | Miscellanous config for ClickHouse (in xml format) |
| clickhouse.image.pullPolicy | string | `"IfNotPresent"` |  |
| clickhouse.image.repository | string | `"altinity/clickhouse-server"` |  |
| clickhouse.image.tag | string | `"24.3.12.76.altinitystable"` | Override the image tag for a specific version |
| clickhouse.initScripts | object | `{"alwaysRun":true,"configMapName":"","enabled":false}` | Init scripts ConfigMap configuration |
| clickhouse.initScripts.alwaysRun | bool | `true` | Set to true to always run init scripts on container startup |
| clickhouse.initScripts.configMapName | string | `""` | Name of an existing ConfigMap containing init scripts The scripts will be mounted at /docker-entrypoint-initdb.d/ |
| clickhouse.initScripts.enabled | bool | `false` | Set to true to enable init scripts feature |
| clickhouse.keeper | object | `{"host":"","port":2181}` | Keeper connection settings for ClickHouse instances. |
| clickhouse.keeper.host | string | `""` | Specify a keeper host. Should be left empty if `clickhouse-keeper.enabled` is `true`. Will override the defaults set from `clickhouse-keeper.enabled`. |
| clickhouse.keeper.port | int | `2181` | Override the default keeper port |
| clickhouse.lbService.enable | bool | `false` |  |
| clickhouse.lbService.serviceAnnotations | object | `{}` |  |
| clickhouse.lbService.serviceLabels | object | `{}` |  |
| clickhouse.persistence.accessMode | string | `"ReadWriteOnce"` |  |
| clickhouse.persistence.enabled | bool | `true` | enable storage |
| clickhouse.persistence.logs.accessMode | string | `"ReadWriteOnce"` |  |
| clickhouse.persistence.logs.enabled | bool | `false` | enable pvc for logs |
| clickhouse.persistence.logs.size | string | `"10Gi"` | size for logs pvc |
| clickhouse.persistence.size | string | `"10Gi"` | volume size (per replica) |
| clickhouse.persistence.storageClass | string | `""` |  |
| clickhouse.podAnnotations | object | `{}` |  |
| clickhouse.podLabels | object | `{}` |  |
| clickhouse.replicasCount | int | `1` | number of replicas. If greater than 1, keeper must be enabled or a keeper host should be provided under clickhouse.keeper.host. Will be ignored if `zones` is set. |
| clickhouse.service.serviceAnnotations | object | `{}` |  |
| clickhouse.service.serviceLabels | object | `{}` |  |
| clickhouse.service.type | string | `"ClusterIP"` |  |
| clickhouse.serviceAccount.annotations | object | `{}` | Annotations to add to the service account |
| clickhouse.serviceAccount.create | bool | `false` | Specifies whether a service account should be created |
| clickhouse.serviceAccount.name | string | `""` | The name of the service account to use. If not set and create is true, a name is generated using the fullname template |
| clickhouse.shardsCount | int | `1` | number of shards. |
| clickhouse.zones | list | `[]` |  |
| keeper.enabled | bool | `false` | Whether to enable Keeper. Required for replicated tables. |
| keeper.image | string | `"altinity/clickhouse-keeper"` |  |
| keeper.localStorage.size | string | `"5Gi"` |  |
| keeper.localStorage.storageClass | string | `""` |  |
| keeper.metricsPort | string | `""` |  |
| keeper.nodeSelector | object | `{}` |  |
| keeper.podAnnotations | object | `{}` |  |
| keeper.replicaCount | int | `3` | Number of keeper replicas. Must be an odd number. !! DO NOT CHANGE AFTER INITIAL DEPLOYMENT |
| keeper.resources.cpuLimitsMs | int | `3` |  |
| keeper.resources.cpuRequestsMs | int | `2` |  |
| keeper.resources.memoryLimitsMiB | string | `"3Gi"` |  |
| keeper.resources.memoryRequestsMiB | string | `"3Gi"` |  |
| keeper.settings | object | `{}` |  |
| keeper.tag | string | `"24.8.14.10459.altinitystable"` |  |
| keeper.tolerations | list | `[]` |  |
| keeper.zoneSpread | bool | `false` |  |
| operator.enabled | bool | `true` | Whether to enabled the Altinity Operator for ClickHouse. Disable if you already have the Operator installed cluster-wide. |
