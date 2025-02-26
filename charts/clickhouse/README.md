

# clickhouse

![Version: 0.1.5](https://img.shields.io/badge/Version-0.1.5-informational?style=flat-square) ![Type: application](https://img.shields.io/badge/Type-application-informational?style=flat-square) ![AppVersion: 23.8.8.21](https://img.shields.io/badge/AppVersion-23.8.8.21-informational?style=flat-square)

A Helm chart for creating a ClickHouse Cluster with the Altinity Operator for ClickHouse

## Requirements

| Repository | Name | Version |
|------------|------|---------|
| https://docs.altinity.com/clickhouse-operator | operator(altinity-clickhouse-operator) | 0.24.3 |

## Installing the Chart

```sh
# add the kubernetes-blueprints-for-clickhouse chart repository
helm repo add altinity https://helm.altinity.com

# use this command to install clickhouse chart (it will also create a `clickhouse` namespace)
helm install clickhouse-dev --create-namespace --namespace clickhouse altinity/clickhouse  --set keeper.enabled=true --set clickhouse.replicasCount=2
```

> Use `-f` flag to override default values: `helm install -f newvalues.yaml`

## Uninstalling the Chart

```sh
# uninstall using the release name (`ch`)
helm uninstall clickhouse-dev --namespace clickhouse
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
| clickhouse.antiAffinity | bool | `false` |  |
| clickhouse.defaultUser.allowExternalAccess | bool | `false` | Allow the default user to access ClickHouse from any IP. If set, will override `hostIP` to always be `0.0.0.0/0`. |
| clickhouse.defaultUser.hostIP | string | `"127.0.0.1/32"` |  |
| clickhouse.defaultUser.password | string | `""` |  |
| clickhouse.image.pullPolicy | string | `"IfNotPresent"` |  |
| clickhouse.image.repository | string | `"altinity/clickhouse-server"` |  |
| clickhouse.image.tag | string | `"24.3.12.76.altinitystable"` | Override the image tag for a specific version |
| clickhouse.keeper | object | `{"host":"","port":2181}` | Keeper connection settings for ClickHouse instances. |
| clickhouse.keeper.host | string | `""` | Specify a keeper host. Should be left empty if `clickhouse-keeper.enabled` is `true`. Will override the defaults set from `clickhouse-keeper.enabled`. |
| clickhouse.keeper.port | int | `2181` | Override the default keeper port |
| clickhouse.persistence.accessMode | string | `"ReadWriteOnce"` |  |
| clickhouse.persistence.enabled | bool | `true` | enable storage |
| clickhouse.persistence.logs.accessMode | string | `"ReadWriteOnce"` |  |
| clickhouse.persistence.logs.enabled | bool | `false` | enable pvc for logs |
| clickhouse.persistence.logs.size | string | `"10Gi"` | size for logs pvc |
| clickhouse.persistence.size | string | `"10Gi"` | volume size (per replica) |
| clickhouse.persistence.storageClass | string | `""` |  |
| clickhouse.podAnnotations | object | `{}` |  |
| clickhouse.podLabels | object | `{}` |  |
| clickhouse.replicasCount | int | `1` | number of replicas. If greater than 1, keeper must be enabled or a keeper host should be provided under clickhouse.keeper.host.  Will be ignored if `zones` is set. |
| clickhouse.service.type | string | `"ClusterIP"` |  |
| clickhouse.service.lbService.enable | bool | `false` | additional cluster LB service |
| clickhouse.service.lbService.serviceAnnotations | object | `""` | annotations for the LB service |
| clickhouse.zones | list | `[]` |  |
| keeper.enabled | bool | `false` | Whether to enable Keeper. Required for replicated tables. |
| keeper.replicaCount | int | `3` | Number of keeper replicas. Must be an odd number. !! DO NOT CHANGE AFTER INITIAL DEPLOYMENT |
| keeper.image | string | `"altinity/clickhouse-keeper"` |  |
| keeper.tag | string | `"24.3.12.76.altinitystable"` |  |
| keeper.settings | object | `[]` | `clickhouse-keeper` global config, for example: `prometheus/port: "7000"` |
| keeper.localStorage.size | string | `"5Gi"` | size for keeper PV |
| keeper.localStorage.storageClass | string | `""` | storage class for keeper PV |
| keeper.nodeSelector | object | `{}` |  |
| keeper.tolerations | object | `{}` |  |
| keeper.zoneSpread | bool | `false` | topologySpreadConstraints over `zone`, by deafult there is only podAntiAffinity by hostname |
| keeper.metricsPort | string | `""` | add metrics port to the service and pod |
| keeper.resources.cpuRequestsMs | string | `"250m"` |  |
| keeper.resources.memoryRequestsMiB | string | `"128Mi"` |  |
| keeper.resources.cpuLimitsMs | string | `"500m"` |  |
| keeper.resources.memoryLimitsMiB | string | `"128Mi"` |  |
| operator.enabled | bool | `true` | Whether to enabled the Altinity Operator for ClickHouse. Disable if you already have the Operator installed cluster-wide. |
