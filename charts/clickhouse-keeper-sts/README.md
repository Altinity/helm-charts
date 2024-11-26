

# clickhouse-keeper-sts

![Version: 0.1.5](https://img.shields.io/badge/Version-0.1.5-informational?style=flat-square) ![Type: application](https://img.shields.io/badge/Type-application-informational?style=flat-square) ![AppVersion: 24.3.6.48](https://img.shields.io/badge/AppVersion-24.3.6.48-informational?style=flat-square)

A ClickHouse Keeper chart for Kubernetes

## Installing the Chart

```sh
# add the kubernetes-blueprints-for-clickhouse chart repository
helm repo add kubernetes-blueprints-for-clickhouse https://altinity.github.io/kubernetes-blueprints-for-clickhouse

# use this command to install clickhouse-keeper-sts chart (it will also create a `clickhouse` namespace)
helm install ch kubernetes-blueprints-for-clickhouse/clickhouse-keeper-sts --namespace clickhouse --create-namespace
```

> Use `-f` flag to override default values: `helm install -f newvalues.yaml`

## Upgrading the Chart
```sh
# get latest repository versions
helm repo update

# upgrade to a newer version using the release name (`ch`)
helm upgrade ch kubernetes-blueprints-for-clickhouse/clickhouse-keeper-sts --namespace clickhouse
```

## Uninstalling the Chart

```sh
# uninstall using the release name (`ch`)
helm uninstall ch --namespace clickhouse
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
| affinity | object | `{}` |  |
| command | string | `"HOST=`hostname -s` &&\nDOMAIN=`hostname -d` &&\nif [[ $HOST =~ (.*)-([0-9]+)$ ]]; then\n    NAME=${BASH_REMATCH[1]}\n    ORD=${BASH_REMATCH[2]}\nelse\n    echo \"Failed to parse name and ordinal of Pod\"\n    exit 1\nfi &&\nexport MY_ID=$((ORD+1)) &&\nmkdir -p /tmp/clickhouse-keeper/config.d/ &&\n{\n  echo \"<yandex><keeper_server>\"\n  echo \"<server_id>${MY_ID}</server_id>\"\n  echo \"<raft_configuration>\"\n  for (( i=1; i<=$SERVERS; i++ )); do\n      echo \"<server><id>${i}</id><hostname>$NAME-$((i-1)).${DOMAIN}</hostname><port>${RAFT_PORT}</port></server>\"\n  done\n  echo \"</raft_configuration>\"\n  echo \"</keeper_server></yandex>\"\n} > /tmp/clickhouse-keeper/config.d/generated-keeper-settings.xml &&\ncat /tmp/clickhouse-keeper/config.d/generated-keeper-settings.xml &&\nif [[ \"1\" == \"$MY_ID\" ]]; then\n  clickhouse-keeper --config-file=/etc/clickhouse-keeper/keeper_config.xml --force-recovery\nelse\n  clickhouse-keeper --config-file=/etc/clickhouse-keeper/keeper_config.xml\nfi\n"` |  |
| fullnameOverride | string | `""` |  |
| image.pullPolicy | string | `"IfNotPresent"` |  |
| image.repository | string | `"clickhouse/clickhouse-keeper"` |  |
| image.tag | string | `"24.3.6.48-alpine"` |  |
| imagePullSecrets | list | `[]` |  |
| ingress.annotations | object | `{}` |  |
| ingress.className | string | `""` |  |
| ingress.enabled | bool | `false` |  |
| ingress.hosts[0].host | string | `"chart-example.local"` |  |
| ingress.hosts[0].paths[0].path | string | `"/"` |  |
| ingress.hosts[0].paths[0].pathType | string | `"ImplementationSpecific"` |  |
| ingress.tls | list | `[]` |  |
| keeperConfig | string | `"<clickhouse>\n    <include_from>/tmp/clickhouse-keeper/config.d/generated-keeper-settings.xml</include_from>\n    <path>/var/lib/clickhouse-keeper</path>\n    <logger>\n        <level>trace</level>\n        <console>true</console>\n    </logger>\n    <listen_host>0.0.0.0</listen_host>\n    <keeper_server incl=\"keeper_server\">\n        <tcp_port>2181</tcp_port>\n        <four_letter_word_white_list>*</four_letter_word_white_list>\n        <coordination_settings>\n            <raft_logs_level>information</raft_logs_level>\n        </coordination_settings>\n    </keeper_server>\n    <prometheus>\n        <endpoint>/metrics</endpoint>\n        <port>7000</port>\n        <metrics>true</metrics>\n        <events>true</events>\n        <asynchronous_metrics>true</asynchronous_metrics>\n        <!-- https://github.com/ClickHouse/ClickHouse/issues/46136 -->\n        <status_info>false</status_info>\n    </prometheus>\n</clickhouse>\n"` |  |
| livenessProbe.exec.command[0] | string | `"bash"` |  |
| livenessProbe.exec.command[1] | string | `"-xc"` |  |
| livenessProbe.exec.command[2] | string | `"date && OK=$(exec 3<>/dev/tcp/127.0.0.1/2181 ; printf \"ruok\" >&3 ; IFS=; tee <&3; exec 3<&- ;); if [[ \"$OK\" == \"imok\" ]]; then exit 0; else exit 1; fi"` |  |
| livenessProbe.initialDelaySeconds | int | `20` |  |
| livenessProbe.timeoutSeconds | int | `15` |  |
| nameOverride | string | `""` |  |
| nodeSelector | object | `{}` |  |
| persistence.accessMode | string | `"ReadWriteOnce"` |  |
| persistence.enabled | bool | `true` |  |
| persistence.size | string | `"10Gi"` |  |
| persistence.storageClass | string | `""` |  |
| podAnnotations | object | `{}` |  |
| podLabels | object | `{}` |  |
| podSecurityContext.fsGroup | int | `101` |  |
| podSecurityContext.runAsGroup | int | `101` |  |
| podSecurityContext.runAsUser | int | `101` |  |
| replicaCount | int | `1` |  |
| resources | object | `{}` |  |
| securityContext | object | `{}` |  |
| service.port | int | `7000` |  |
| service.type | string | `"ClusterIP"` |  |
| tolerations | list | `[]` |  |
| volumeMounts | list | `[]` |  |
| volumes | list | `[]` |  |
