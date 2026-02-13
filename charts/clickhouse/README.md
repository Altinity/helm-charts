# clickhouse
![Version: 0.3.9](https://img.shields.io/badge/Version-0.3.9-informational?style=flat-square) ![Type: application](https://img.shields.io/badge/Type-application-informational?style=flat-square) ![AppVersion: 25.3.6.10034](https://img.shields.io/badge/AppVersion-25.3.6.10034-informational?style=flat-square)

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
| https://helm.altinity.com | operator(altinity-clickhouse-operator) | 0.25.6 |

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
helm repo add altinity https://helm.altinity.com/

# create the namespace
kubectl create namespace clickhouse

# install operator into namespace
helm install clickhouse-operator altinity/altinity-clickhouse-operator \
--namespace clickhouse

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
| clickhouse.antiAffinityScope | string | ClickHouseInstallation | Scope for anti-affinity policy when antiAffinity is enabled. Determines the level at which pod distribution is enforced. Available scopes:   - ClickHouseInstallation: Pods from the same installation won't run on the same node (default)   - Shard: Pods from the same shard won't run on the same node   - Replica: Pods from the same replica won't run on the same node   - Cluster: Pods from the same cluster won't run on the same node   - Namespace: Pods from the same namespace won't run on the same node |
| clickhouse.clusterSecret | object | `{"auto":true,"enabled":false,"secure":false,"value":"","valueFrom":{"secretKeyRef":{"key":"secret","name":""}}}` | Cluster secret configuration for secure inter-node communication |
| clickhouse.clusterSecret.auto | bool | `true` | Auto-generate cluster secret (recommended for security) |
| clickhouse.clusterSecret.enabled | bool | `false` | Whether to enable secret-based cluster communication |
| clickhouse.clusterSecret.secure | bool | `false` | Whether to secure this behind the SSL port |
| clickhouse.clusterSecret.value | string | `""` | Plaintext cluster secret value (not recommended for production) |
| clickhouse.clusterSecret.valueFrom | object | `{"secretKeyRef":{"key":"secret","name":""}}` | Reference to an existing Kubernetes secret containing the cluster secret |
| clickhouse.clusterSecret.valueFrom.secretKeyRef.key | string | `"secret"` | Key in the secret that contains the cluster secret value |
| clickhouse.clusterSecret.valueFrom.secretKeyRef.name | string | `""` | Name of the secret containing the cluster secret |
| clickhouse.defaultUser.allowExternalAccess | bool | `false` | Allow the default user to access ClickHouse from any IP. If set, will override `hostIP` to always be `0.0.0.0/0`. |
| clickhouse.defaultUser.hostIP | string | `"127.0.0.1/32"` |  |
| clickhouse.defaultUser.password | string | `""` |  |
| clickhouse.defaultUser.password_secret_name | string | `""` | Name of an existing Kubernetes secret containing the default user password. If set, the password will be read from the secret instead of using the password field. The secret should contain a key named 'password'. |
| clickhouse.extraConfig | string | `"<clickhouse>\n</clickhouse>\n"` | Miscellanous config for ClickHouse (in xml format) |
| clickhouse.extraContainers | list | `[]` | Extra containers for clickhouse pods |
| clickhouse.extraPorts | list | `[]` | Additional ports to expose in the ClickHouse container Example: extraPorts:   - name: custom-port     containerPort: 8080 |
| clickhouse.extraUsers | string | `"<clickhouse>\n</clickhouse>\n"` | Additional users config for ClickHouse (in xml format) |
| clickhouse.extraVolumes | list | `[]` | Extra volumes for clickhouse pods |
| clickhouse.image.pullPolicy | string | `"IfNotPresent"` |  |
| clickhouse.image.repository | string | `"altinity/clickhouse-server"` |  |
| clickhouse.image.tag | string | `"25.3.6.10034.altinitystable"` | Override the image tag for a specific version |
| clickhouse.initScripts | object | `{"alwaysRun":true,"configMapName":"","enabled":false}` | Init scripts ConfigMap configuration |
| clickhouse.initScripts.alwaysRun | bool | `true` | Set to true to always run init scripts on container startup |
| clickhouse.initScripts.configMapName | string | `""` | Name of an existing ConfigMap containing init scripts The scripts will be mounted at /docker-entrypoint-initdb.d/ |
| clickhouse.initScripts.enabled | bool | `false` | Set to true to enable init scripts feature |
| clickhouse.keeper | object | `{"host":"","port":2181}` | Keeper connection settings for ClickHouse instances. |
| clickhouse.keeper.host | string | `""` | Specify a keeper host. Should be left empty if `clickhouse-keeper.enabled` is `true`. Will override the defaults set from `clickhouse-keeper.enabled`. |
| clickhouse.keeper.port | int | `2181` | Override the default keeper port |
| clickhouse.lbService.enabled | bool | `false` |  |
| clickhouse.lbService.loadBalancerSourceRanges | list | `[]` | Specify source IP ranges to the LoadBalancer service. If supported by the platform, this will restrict traffic through the cloud-provider load-balancer to the specified client IPs. This is ignored if the cloud-provider does not support the feature. |
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
| clickhouse.profiles | object | `{}` |  |
| clickhouse.replicasCount | int | `1` | number of replicas. If greater than 1, keeper must be enabled or a keeper host should be provided under clickhouse.keeper.host. Will be ignored if `zones` is set. |
| clickhouse.resources | object | `{}` |  |
| clickhouse.service.serviceAnnotations | object | `{}` |  |
| clickhouse.service.serviceLabels | object | `{}` |  |
| clickhouse.service.type | string | `"ClusterIP"` |  |
| clickhouse.serviceAccount.annotations | object | `{}` | Annotations to add to the service account |
| clickhouse.serviceAccount.create | bool | `false` | Specifies whether a service account should be created |
| clickhouse.serviceAccount.name | string | `""` | The name of the service account to use. If not set and create is true, a name is generated using the fullname template |
| clickhouse.settings | object | `{}` |  |
| clickhouse.shardsCount | int | `1` | number of shards. |
| clickhouse.users | list | `[]` | Configure additional ClickHouse users and per-user settings. |
| clickhouse.tls | object | | TLS certificate configuration for HTTPS/TLS connections. See [examples/values-tls.yaml](examples/values-tls.yaml) for a concrete example. |
| clickhouse.tls.enabled | bool | `false` | Enable TLS. When true, adds `https_port` and `tcp_port_secure` to ClickHouse settings and exposes secure ports on Service resources. Requires `clickhouse.extraPorts` to declare the corresponding container ports on the pod template. |
| clickhouse.tls.httpsPort | int | `8443` | HTTPS port for secure HTTP connections. |
| clickhouse.tls.secureTcpPort | int | `9440` | Secure native TCP port for encrypted client connections. |
| clickhouse.tls.certificateFile | object | | Server X509 certificate file. Requires `configFileName` and exactly one of `inlineFileContent` or `secretReference`. |
| clickhouse.tls.certificateFile.configFileName | string | | Part of the destination filepath within the ClickHouse pod. Inline content is placed under `config.d/`; secret reference is placed under `secrets.d/`. See [here](https://github.com/Altinity/clickhouse-operator/blob/release-0.25.6/docs/security_hardening.md?plain=1#L428-L429) for the exact filepath format. |
| clickhouse.tls.certificateFile.inlineFileContent | string | | Certificate content embedded directly in the CHI spec. Mutually exclusive with `secretReference`. |
| clickhouse.tls.certificateFile.secretReference | object | | Reference to a Kubernetes secret containing the certificate. Mutually exclusive with `inlineFileContent`. |
| clickhouse.tls.certificateFile.secretReference.name | string | | Name of the Kubernetes secret. |
| clickhouse.tls.certificateFile.secretReference.key | string | | Key within the secret that holds the certificate data. |
| clickhouse.tls.privateKeyFile | object | | Private key file. Same structure as `certificateFile`. |
| clickhouse.tls.privateKeyFile.configFileName | string | | See `certificateFile.configFileName`. |
| clickhouse.tls.privateKeyFile.inlineFileContent | string | | See `certificateFile.inlineFileContent`. |
| clickhouse.tls.privateKeyFile.secretReference | object | | See `certificateFile.secretReference`. |
| clickhouse.tls.privateKeyFile.secretReference.name | string | | See `certificateFile.secretReference.name`. |
| clickhouse.tls.privateKeyFile.secretReference.key | string | | See `certificateFile.secretReference.key`. |
| clickhouse.tls.dhParamsFile | object | | Diffie-Hellman parameters file. Same structure as `certificateFile`. |
| clickhouse.tls.dhParamsFile.configFileName | string | | See `certificateFile.configFileName`. |
| clickhouse.tls.dhParamsFile.inlineFileContent | string | | See `certificateFile.inlineFileContent`. |
| clickhouse.tls.dhParamsFile.secretReference | object | | See `certificateFile.secretReference`. |
| clickhouse.tls.dhParamsFile.secretReference.name | string | | See `certificateFile.secretReference.name`. |
| clickhouse.tls.dhParamsFile.secretReference.key | string | | See `certificateFile.secretReference.key`. |
| clickhouse.tls.opensslConfig | string | | OpenSSL configuration XML rendered as `openssl.xml` in the ClickHouse pod. Must include the full `<clickhouse><openSSL><server>` structure with file paths matching your certificate, key, and DH params locations. See [here](https://docs.altinity.com/operationsguide/security/#generate-files) for another sample of the full structure. |
| clickhouse.users | list | `[]` | Configure additional ClickHouse users. |
| clickhouse.zones | list | `[]` |  |
| keeper.enabled | bool | `false` | Whether to enable Keeper. Required for replicated tables. |
| keeper.image | string | `"altinity/clickhouse-keeper"` |  |
| keeper.localStorage.size | string | `"5Gi"` |  |
| keeper.localStorage.storageClass | string | `""` |  |
| keeper.metricsPort | string | `""` |  |
| keeper.nodeSelector | object | `{}` |  |
| keeper.podAnnotations | object | `{}` |  |
| keeper.replicaCount | int | `3` | Number of keeper replicas. Must be an odd number. !! DO NOT CHANGE AFTER INITIAL DEPLOYMENT |
| keeper.resources.cpuLimitsMs | int | `500` |  |
| keeper.resources.cpuRequestsMs | int | `100` |  |
| keeper.resources.memoryLimitsMiB | string | `"1Gi"` |  |
| keeper.resources.memoryRequestsMiB | string | `"512Mi"` |  |
| keeper.settings | object | `{}` |  |
| keeper.tag | string | `"25.3.6.10034.altinitystable"` |  |
| keeper.tolerations | list | `[]` |  |
| keeper.volumeClaimAnnotations | object | `{}` |  |
| keeper.zoneSpread | bool | `false` |  |
| namespaceDomainPattern | string | `""` | Custom domain pattern used for DNS names of `Service` and `Pod` resources. Typically defined by the custom cluster domain of the Kubernetes cluster. The pattern follows the `%s` C-style printf format, e.g. '%s.svc.my.test'. If not specified, the default namespace domain suffix is `.svc.cluster.local`. |
| operator.enabled | bool | `true` | Whether to enable the Altinity Operator for ClickHouse. Disable if you already have the Operator installed cluster-wide. |
