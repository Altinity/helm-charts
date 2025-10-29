# These requirements were auto generated
# from software requirements specification (SRS)
# document by TestFlows v2.0.231215.1221232.
# Do not edit by hand but re-generate instead
# using 'tfs requirements generate' command.
from testflows.core import Specification
from testflows.core import Requirement

Heading = Specification.Heading

RQ_SRS_Helm = Requirement(
    name="RQ.SRS.Helm",
    version="1.0",
    priority=None,
    group=None,
    type=None,
    uid=None,
    description=(
        "The [Helm Chart] SHALL allow users to deploy and configure ClickHouse environments in [Kubernetes] clusters.\n"
        "\n"
    ),
    link=None,
    level=1,
    num="3",
)

RQ_SRS_Helm_Chart_Values = Requirement(
    name="RQ.SRS.Helm.Chart.Values",
    version="1.0",
    priority=None,
    group=None,
    type=None,
    uid=None,
    description=(
        "The Helm chart SHALL provide a `values.yaml` file where users define their desired environment configuration.\n"
        "\n"
        "```yaml\n"
        "clickhouse:\n"
        "  replicasCount: 3\n"
        "  shardsCount: 2\n"
        "  antiAffinity: true\n"
        "  persistence:\n"
        "    enabled: true\n"
        "    size: 100Gi\n"
        "  service:\n"
        "    type: ClusterIP\n"
        "```\n"
        "\n"
        "---\n"
        "\n"
    ),
    link=None,
    level=2,
    num="4.1",
)

RQ_SRS_Helm_Metadata_NameOverride = Requirement(
    name="RQ.SRS.Helm.Metadata.NameOverride",
    version="1.0",
    priority=None,
    group=None,
    type=None,
    uid=None,
    description=(
        "The `values.yaml` SHALL support `nameOverride` to override the chart name.\n"
        "\n"
        "```yaml\n"
        'nameOverride: "custom-clickhouse"\n'
        "```\n"
        "\n"
        "If invalid characters are used (e.g., spaces, special characters), Helm SHALL raise a template rendering error.\n"
        "\n"
    ),
    link=None,
    level=3,
    num="5.1.1",
)

RQ_SRS_Helm_Metadata_FullnameOverride = Requirement(
    name="RQ.SRS.Helm.Metadata.FullnameOverride",
    version="1.0",
    priority=None,
    group=None,
    type=None,
    uid=None,
    description=(
        "The `values.yaml` SHALL support `fullnameOverride` to override the full release name.\n"
        "\n"
        "```yaml\n"
        'fullnameOverride: "acme-clickhouse-prod"\n'
        "```\n"
        "\n"
    ),
    link=None,
    level=3,
    num="5.2.1",
)

RQ_SRS_Helm_Metadata_NamespaceDomainPattern = Requirement(
    name="RQ.SRS.Helm.Metadata.NamespaceDomainPattern",
    version="1.0",
    priority=None,
    group=None,
    type=None,
    uid=None,
    description=(
        "The `values.yaml` SHALL support `namespaceDomainPattern` for specifying a custom Kubernetes cluster domain.\n"
        "\n"
        "```yaml\n"
        'namespaceDomainPattern: "acme.k8s.cluster.local"\n'
        "```\n"
        "\n"
        "If empty, the default `cluster.local` SHALL be used.\n"
        "\n"
        "---\n"
        "\n"
    ),
    link=None,
    level=3,
    num="5.3.1",
)

RQ_SRS_Helm_ClickHouse_DefaultUser = Requirement(
    name="RQ.SRS.Helm.ClickHouse.DefaultUser",
    version="1.0",
    priority=None,
    group=None,
    type=None,
    uid=None,
    description=(
        "The chart SHALL configure a default ClickHouse user.\n"
        "\n"
        "```yaml\n"
        "clickhouse:\n"
        "  defaultUser:\n"
        '    password: "SuperSecret"\n'
        "    allowExternalAccess: true\n"
        '    hostIP: "0.0.0.0/0"\n'
        "```\n"
        "\n"
        "Error Handling:\n"
        "\n"
        '* If `password` is empty → Helm SHALL reject with: *"defaultUser.password is required"*.\n'
        "* If `hostIP` is invalid → Helm SHALL raise an error during CRD validation.\n"
        "\n"
    ),
    link=None,
    level=3,
    num="6.1.1",
)

RQ_SRS_Helm_ClickHouse_Users = Requirement(
    name="RQ.SRS.Helm.ClickHouse.Users",
    version="1.0",
    priority=None,
    group=None,
    type=None,
    uid=None,
    description=(
        "The chart SHALL allow defining additional users.\n"
        "\n"
        "```yaml\n"
        "clickhouse:\n"
        "  users:\n"
        "    - name: analytics\n"
        "      password_secret_name: analytics-secret\n"
        "      grants:\n"
        '        - "GRANT SELECT ON default.*"\n'
        "```\n"
        "\n"
        "* `name` MUST match regex `^[a-zA-Z0-9]+$`.\n"
        '* If invalid → Helm SHALL raise: *"Invalid username format"*.\n'
        "* Either `password_secret_name` OR `password_sha256_hex` SHALL be required.\n"
        "\n"
    ),
    link=None,
    level=3,
    num="6.2.1",
)

RQ_SRS_Helm_ClickHouse_ReplicasCount = Requirement(
    name="RQ.SRS.Helm.ClickHouse.ReplicasCount",
    version="1.0",
    priority=None,
    group=None,
    type=None,
    uid=None,
    description=(
        "The `replicasCount` SHALL define number of ClickHouse replicas.\n"
        "\n"
        "```yaml\n"
        "clickhouse:\n"
        "  replicasCount: 3\n"
        "```\n"
        "\n"
        "* If greater than 1, `keeper.enabled` MUST be `true` or `keeper.host` MUST be provided.\n"
        "\n"
        "Error Handling:\n"
        "\n"
        '* If `replicasCount > 1` but Keeper not enabled → Helm SHALL raise: *"Keeper required for replicasCount > 1"*.\n'
        "\n"
    ),
    link=None,
    level=3,
    num="6.3.1",
)

RQ_SRS_Helm_ClickHouse_ShardsCount = Requirement(
    name="RQ.SRS.Helm.ClickHouse.ShardsCount",
    version="1.0",
    priority=None,
    group=None,
    type=None,
    uid=None,
    description=(
        "The `shardsCount` SHALL define number of shards.\n"
        "\n"
        "```yaml\n"
        "clickhouse:\n"
        "  shardsCount: 2\n"
        "```\n"
        "\n"
        'If set to 0 → Helm SHALL raise: *"shardsCount must be at least 1"*.\n'
        "\n"
    ),
    link=None,
    level=3,
    num="6.4.1",
)

RQ_SRS_Helm_ClickHouse_Zones = Requirement(
    name="RQ.SRS.Helm.ClickHouse.Zones",
    version="1.0",
    priority=None,
    group=None,
    type=None,
    uid=None,
    description=(
        "The `zones` SHALL define Kubernetes zones.\n"
        "\n"
        "```yaml\n"
        "clickhouse:\n"
        '  zones: ["zone-a", "zone-b"]\n'
        "```\n"
        "\n"
        "If zone list does not match cluster topology → scheduling SHALL fail.\n"
        "\n"
    ),
    link=None,
    level=3,
    num="6.5.1",
)

RQ_SRS_Helm_ClickHouse_AntiAffinity = Requirement(
    name="RQ.SRS.Helm.ClickHouse.AntiAffinity",
    version="1.0",
    priority=None,
    group=None,
    type=None,
    uid=None,
    description=(
        "The `antiAffinity` flag SHALL enforce pod anti-affinity.\n"
        "\n"
        "```yaml\n"
        "clickhouse:\n"
        "  antiAffinity: true\n"
        "```\n"
        "\n"
        "If enabled, ClickHouse pods SHALL not run on the same node.\n"
        "\n"
    ),
    link=None,
    level=3,
    num="6.6.1",
)

RQ_SRS_Helm_ClickHouse_Keeper = Requirement(
    name="RQ.SRS.Helm.ClickHouse.Keeper",
    version="1.0",
    priority=None,
    group=None,
    type=None,
    uid=None,
    description=(
        "The chart SHALL allow external or embedded Keeper.\n"
        "\n"
        "```yaml\n"
        "clickhouse:\n"
        "  keeper:\n"
        '    host: "keeper-service"\n'
        "    port: 2181\n"
        "```\n"
        "\n"
        "If `replicasCount > 1` but Keeper is not configured, Helm SHALL raise an error.\n"
        "\n"
    ),
    link=None,
    level=3,
    num="6.7.1",
)

RQ_SRS_Helm_ClickHouse_Persistence = Requirement(
    name="RQ.SRS.Helm.ClickHouse.Persistence",
    version="1.0",
    priority=None,
    group=None,
    type=None,
    uid=None,
    description=(
        "The chart SHALL support persistent volumes.\n"
        "\n"
        "```yaml\n"
        "clickhouse:\n"
        "  persistence:\n"
        "    enabled: true\n"
        "    size: 100Gi\n"
        "    accessMode: ReadWriteOnce\n"
        "```\n"
        "\n"
        "Error Handling:\n"
        "\n"
        '* If `enabled: true` but `size` missing → Helm SHALL raise: *"persistence.size required"*.\n'
        "\n"
    ),
    link=None,
    level=3,
    num="6.8.1",
)

RQ_SRS_Helm_ClickHouse_Image = Requirement(
    name="RQ.SRS.Helm.ClickHouse.Image",
    version="1.0",
    priority=None,
    group=None,
    type=None,
    uid=None,
    description=(
        "The chart SHALL support custom image repo, tag, and pullPolicy.\n"
        "\n"
        "```yaml\n"
        "clickhouse:\n"
        "  image:\n"
        "    repository: altinity/clickhouse-server\n"
        '    tag: "24.3"\n'
        "    pullPolicy: IfNotPresent\n"
        "```\n"
        "\n"
    ),
    link=None,
    level=3,
    num="6.9.1",
)

RQ_SRS_Helm_ClickHouse_Service = Requirement(
    name="RQ.SRS.Helm.ClickHouse.Service",
    version="1.0",
    priority=None,
    group=None,
    type=None,
    uid=None,
    description=(
        "The chart SHALL configure a Kubernetes service.\n"
        "\n"
        "```yaml\n"
        "clickhouse:\n"
        "  service:\n"
        "    type: ClusterIP\n"
        "```\n"
        "\n"
        'If invalid type is specified → Helm SHALL raise: *"Invalid service type"*.\n'
        "\n"
    ),
    link=None,
    level=3,
    num="6.10.1",
)

RQ_SRS_Helm_ClickHouse_LbService = Requirement(
    name="RQ.SRS.Helm.ClickHouse.LbService",
    version="1.0",
    priority=None,
    group=None,
    type=None,
    uid=None,
    description=(
        "The chart SHALL support LoadBalancer service.\n"
        "\n"
        "```yaml\n"
        "clickhouse:\n"
        "  lbService:\n"
        "    enabled: true\n"
        '    loadBalancerSourceRanges: ["0.0.0.0/0"]\n'
        "```\n"
        "\n"
        "If `enabled: true` without ranges → default SHALL be `0.0.0.0/0`.\n"
        "\n"
    ),
    link=None,
    level=3,
    num="6.11.1",
)

RQ_SRS_Helm_ClickHouse_PodSettings = Requirement(
    name="RQ.SRS.Helm.ClickHouse.PodSettings",
    version="1.0",
    priority=None,
    group=None,
    type=None,
    uid=None,
    description=(
        "The chart SHALL support pod annotations, labels, security context, tolerations, etc.\n"
        "\n"
        "```yaml\n"
        "clickhouse:\n"
        "  podLabels:\n"
        "    app: clickhouse\n"
        "```\n"
        "\n"
    ),
    link=None,
    level=3,
    num="6.12.1",
)

RQ_SRS_Helm_ClickHouse_ExtraConfig = Requirement(
    name="RQ.SRS.Helm.ClickHouse.ExtraConfig",
    version="1.0",
    priority=None,
    group=None,
    type=None,
    uid=None,
    description=(
        "The chart SHALL allow XML config overrides.\n"
        "\n"
        "```yaml\n"
        "clickhouse:\n"
        "  extraConfig: |\n"
        "    <yandex>\n"
        "      <merge_tree>\n"
        "        <parts_to_throw_insert>300</parts_to_throw_insert>\n"
        "      </merge_tree>\n"
        "    </yandex>\n"
        "```\n"
        "\n"
    ),
    link=None,
    level=3,
    num="6.13.1",
)

RQ_SRS_Helm_ClickHouse_InitScripts = Requirement(
    name="RQ.SRS.Helm.ClickHouse.InitScripts",
    version="1.0",
    priority=None,
    group=None,
    type=None,
    uid=None,
    description=(
        "The chart SHALL allow init scripts.\n"
        "\n"
        "```yaml\n"
        "clickhouse:\n"
        "  initScripts:\n"
        "    enabled: true\n"
        '    configMapName: "ch-init-scripts"\n'
        "```\n"
        "\n"
        'If enabled without configMapName → Helm SHALL raise: *"initScripts.configMapName required"*.\n'
        "\n"
        "---\n"
        "\n"
    ),
    link=None,
    level=3,
    num="6.14.1",
)

RQ_SRS_Helm_Keeper_Enabled = Requirement(
    name="RQ.SRS.Helm.Keeper.Enabled",
    version="1.0",
    priority=None,
    group=None,
    type=None,
    uid=None,
    description=("```yaml\n" "keeper:\n" "  enabled: true\n" "```\n" "\n"),
    link=None,
    level=3,
    num="7.1.1",
)

RQ_SRS_Helm_Keeper_ReplicaCount = Requirement(
    name="RQ.SRS.Helm.Keeper.ReplicaCount",
    version="1.0",
    priority=None,
    group=None,
    type=None,
    uid=None,
    description=(
        "The `replicaCount` MUST be odd.\n"
        "\n"
        "```yaml\n"
        "keeper:\n"
        "  replicaCount: 3\n"
        "```\n"
        "\n"
        'If even → Helm SHALL raise: *"Keeper replicaCount must be odd"*.\n'
        "\n"
    ),
    link=None,
    level=3,
    num="7.2.1",
)

RQ_SRS_Helm_Keeper_Image = Requirement(
    name="RQ.SRS.Helm.Keeper.Image",
    version="1.0",
    priority=None,
    group=None,
    type=None,
    uid=None,
    description=("The chart SHALL allow Keeper image repo/tag.\n" "\n"),
    link=None,
    level=3,
    num="7.3.1",
)

RQ_SRS_Helm_Keeper_Storage = Requirement(
    name="RQ.SRS.Helm.Keeper.Storage",
    version="1.0",
    priority=None,
    group=None,
    type=None,
    uid=None,
    description=(
        "The chart SHALL allow persistent storage for Keeper.\n"
        "\n"
        "```yaml\n"
        "keeper:\n"
        "  localStorage:\n"
        "    size: 20Gi\n"
        "    storageClass: fast-ssd\n"
        "```\n"
        "\n"
    ),
    link=None,
    level=3,
    num="7.4.1",
)

RQ_SRS_Helm_Keeper_Resources = Requirement(
    name="RQ.SRS.Helm.Keeper.Resources",
    version="1.0",
    priority=None,
    group=None,
    type=None,
    uid=None,
    description=(
        "The chart SHALL allow CPU/memory requests and limits.\n"
        "\n"
        "```yaml\n"
        "keeper:\n"
        "  resources:\n"
        "    cpuRequestsMs: 500\n"
        '    memoryRequestsMiB: "512Mi"\n'
        "```\n"
        "\n"
        "---\n"
        "\n"
    ),
    link=None,
    level=3,
    num="7.5.1",
)

RQ_SRS_Helm_Operator_Enabled = Requirement(
    name="RQ.SRS.Helm.Operator.Enabled",
    version="1.0",
    priority=None,
    group=None,
    type=None,
    uid=None,
    description=(
        "The chart SHALL allow enabling the Altinity Operator.\n"
        "\n"
        "```yaml\n"
        "operator:\n"
        "  enabled: true\n"
        "```\n"
        "\n"
        "---\n"
        "\n"
    ),
    link=None,
    level=3,
    num="8.1.1",
)

QA_SRS_Altinity_Cloud_Anywhere_Helm_Charts = Specification(
    name="QA-SRS Altinity.Cloud Anywhere Helm Charts",
    description=None,
    author=None,
    date=None,
    status=None,
    approved_by=None,
    approved_date=None,
    approved_version=None,
    version=None,
    group=None,
    type=None,
    link=None,
    uid=None,
    parent=None,
    children=None,
    headings=(
        Heading(name="Software Requirements Specification for Helm", level=0, num=""),
        Heading(name="Table of Contents", level=1, num="1"),
        Heading(name="Introduction", level=1, num="2"),
        Heading(name="RQ.SRS.Helm", level=1, num="3"),
        Heading(name="Helm Chart Example", level=1, num="4"),
        Heading(name="RQ.SRS.Helm.Chart.Values", level=2, num="4.1"),
        Heading(name="Chart Metadata", level=1, num="5"),
        Heading(name="Name Override", level=2, num="5.1"),
        Heading(name="RQ.SRS.Helm.Metadata.NameOverride", level=3, num="5.1.1"),
        Heading(name="Fullname Override", level=2, num="5.2"),
        Heading(name="RQ.SRS.Helm.Metadata.FullnameOverride", level=3, num="5.2.1"),
        Heading(name="Namespace Domain Pattern", level=2, num="5.3"),
        Heading(
            name="RQ.SRS.Helm.Metadata.NamespaceDomainPattern", level=3, num="5.3.1"
        ),
        Heading(name="ClickHouse Configuration", level=1, num="6"),
        Heading(name="Default User", level=2, num="6.1"),
        Heading(name="RQ.SRS.Helm.ClickHouse.DefaultUser", level=3, num="6.1.1"),
        Heading(name="Users", level=2, num="6.2"),
        Heading(name="RQ.SRS.Helm.ClickHouse.Users", level=3, num="6.2.1"),
        Heading(name="Replicas Count", level=2, num="6.3"),
        Heading(name="RQ.SRS.Helm.ClickHouse.ReplicasCount", level=3, num="6.3.1"),
        Heading(name="Shards Count", level=2, num="6.4"),
        Heading(name="RQ.SRS.Helm.ClickHouse.ShardsCount", level=3, num="6.4.1"),
        Heading(name="Zones", level=2, num="6.5"),
        Heading(name="RQ.SRS.Helm.ClickHouse.Zones", level=3, num="6.5.1"),
        Heading(name="Anti Affinity", level=2, num="6.6"),
        Heading(name="RQ.SRS.Helm.ClickHouse.AntiAffinity", level=3, num="6.6.1"),
        Heading(name="Keeper", level=2, num="6.7"),
        Heading(name="RQ.SRS.Helm.ClickHouse.Keeper", level=3, num="6.7.1"),
        Heading(name="Persistence", level=2, num="6.8"),
        Heading(name="RQ.SRS.Helm.ClickHouse.Persistence", level=3, num="6.8.1"),
        Heading(name="ClickHouse Image", level=2, num="6.9"),
        Heading(name="RQ.SRS.Helm.ClickHouse.Image", level=3, num="6.9.1"),
        Heading(name="Service", level=2, num="6.10"),
        Heading(name="RQ.SRS.Helm.ClickHouse.Service", level=3, num="6.10.1"),
        Heading(name="Load Balancer Service", level=2, num="6.11"),
        Heading(name="RQ.SRS.Helm.ClickHouse.LbService", level=3, num="6.11.1"),
        Heading(name="Pod Settings", level=2, num="6.12"),
        Heading(name="RQ.SRS.Helm.ClickHouse.PodSettings", level=3, num="6.12.1"),
        Heading(name="Extra Config", level=2, num="6.13"),
        Heading(name="RQ.SRS.Helm.ClickHouse.ExtraConfig", level=3, num="6.13.1"),
        Heading(name="Init Scripts", level=2, num="6.14"),
        Heading(name="RQ.SRS.Helm.ClickHouse.InitScripts", level=3, num="6.14.1"),
        Heading(name="Keeper Configuration", level=1, num="7"),
        Heading(name="Keeper Enabled", level=2, num="7.1"),
        Heading(name="RQ.SRS.Helm.Keeper.Enabled", level=3, num="7.1.1"),
        Heading(name="Replica Count", level=2, num="7.2"),
        Heading(name="RQ.SRS.Helm.Keeper.ReplicaCount", level=3, num="7.2.1"),
        Heading(name="Keeper Image", level=2, num="7.3"),
        Heading(name="RQ.SRS.Helm.Keeper.Image", level=3, num="7.3.1"),
        Heading(name="Storage", level=2, num="7.4"),
        Heading(name="RQ.SRS.Helm.Keeper.Storage", level=3, num="7.4.1"),
        Heading(name="Resources", level=2, num="7.5"),
        Heading(name="RQ.SRS.Helm.Keeper.Resources", level=3, num="7.5.1"),
        Heading(name="Operator Configuration", level=1, num="8"),
        Heading(name="Operator Enabled", level=2, num="8.1"),
        Heading(name="RQ.SRS.Helm.Operator.Enabled", level=3, num="8.1.1"),
        Heading(name="Terminology", level=1, num="9"),
        Heading(name="Helm Chart", level=1, num="10"),
        Heading(name="Values.yaml", level=1, num="11"),
        Heading(name="Release", level=1, num="12"),
        Heading(name="CRD", level=1, num="13"),
        Heading(name="PVC", level=1, num="14"),
        Heading(name="Pod Anti-Affinity", level=1, num="15"),
    ),
    requirements=(
        RQ_SRS_Helm,
        RQ_SRS_Helm_Chart_Values,
        RQ_SRS_Helm_Metadata_NameOverride,
        RQ_SRS_Helm_Metadata_FullnameOverride,
        RQ_SRS_Helm_Metadata_NamespaceDomainPattern,
        RQ_SRS_Helm_ClickHouse_DefaultUser,
        RQ_SRS_Helm_ClickHouse_Users,
        RQ_SRS_Helm_ClickHouse_ReplicasCount,
        RQ_SRS_Helm_ClickHouse_ShardsCount,
        RQ_SRS_Helm_ClickHouse_Zones,
        RQ_SRS_Helm_ClickHouse_AntiAffinity,
        RQ_SRS_Helm_ClickHouse_Keeper,
        RQ_SRS_Helm_ClickHouse_Persistence,
        RQ_SRS_Helm_ClickHouse_Image,
        RQ_SRS_Helm_ClickHouse_Service,
        RQ_SRS_Helm_ClickHouse_LbService,
        RQ_SRS_Helm_ClickHouse_PodSettings,
        RQ_SRS_Helm_ClickHouse_ExtraConfig,
        RQ_SRS_Helm_ClickHouse_InitScripts,
        RQ_SRS_Helm_Keeper_Enabled,
        RQ_SRS_Helm_Keeper_ReplicaCount,
        RQ_SRS_Helm_Keeper_Image,
        RQ_SRS_Helm_Keeper_Storage,
        RQ_SRS_Helm_Keeper_Resources,
        RQ_SRS_Helm_Operator_Enabled,
    ),
    content="""
# QA-SRS Altinity.Cloud Anywhere Helm Charts

---

# Software Requirements Specification for Helm

---


## Table of Contents

* 1 [Introduction](#introduction)
* 2 [RQ.SRS.Helm](#rqsrshelm)
* 3 [Helm Chart Example](#helm-chart-example)
    * 3.1 [RQ.SRS.Helm.Chart.Values](#rqsrshelmchartvalues)
* 4 [Chart Metadata](#chart-metadata)
    * 4.1 [Name Override](#name-override)
        * 4.1.1 [RQ.SRS.Helm.Metadata.NameOverride](#rqsrshelmmetadatanameoverride)
    * 4.2 [Fullname Override](#fullname-override)
        * 4.2.1 [RQ.SRS.Helm.Metadata.FullnameOverride](#rqsrshelmmetadatafullnameoverride)
    * 4.3 [Namespace Domain Pattern](#namespace-domain-pattern)
        * 4.3.1 [RQ.SRS.Helm.Metadata.NamespaceDomainPattern](#rqsrshelmmetadatanamespacedomainpattern)
* 5 [ClickHouse Configuration](#clickhouse-configuration)
    * 5.1 [Default User](#default-user)
        * 5.1.1 [RQ.SRS.Helm.ClickHouse.DefaultUser](#rqsrshelmclickhousedefaultuser)
    * 5.2 [Users](#users)
        * 5.2.1 [RQ.SRS.Helm.ClickHouse.Users](#rqsrshelmclickhouseusers)
    * 5.3 [Replicas Count](#replicas-count)
        * 5.3.1 [RQ.SRS.Helm.ClickHouse.ReplicasCount](#rqsrshelmclickhousereplicascount)
    * 5.4 [Shards Count](#shards-count)
        * 5.4.1 [RQ.SRS.Helm.ClickHouse.ShardsCount](#rqsrshelmclickhouseshardscount)
    * 5.5 [Zones](#zones)
        * 5.5.1 [RQ.SRS.Helm.ClickHouse.Zones](#rqsrshelmclickhousezones)
    * 5.6 [Anti Affinity](#anti-affinity)
        * 5.6.1 [RQ.SRS.Helm.ClickHouse.AntiAffinity](#rqsrshelmclickhouseantiaffinity)
    * 5.7 [Keeper](#keeper)
        * 5.7.1 [RQ.SRS.Helm.ClickHouse.Keeper](#rqsrshelmclickhousekeeper)
    * 5.8 [Persistence](#persistence)
        * 5.8.1 [RQ.SRS.Helm.ClickHouse.Persistence](#rqsrshelmclickhousepersistence)
    * 5.9 [ClickHouse Image](#clickhouse-image)
        * 5.9.1 [RQ.SRS.Helm.ClickHouse.Image](#rqsrshelmclickhouseimage)
    * 5.10 [Service](#service)
        * 5.10.1 [RQ.SRS.Helm.ClickHouse.Service](#rqsrshelmclickhouseservice)
    * 5.11 [Load Balancer Service](#load-balancer-service)
        * 5.11.1 [RQ.SRS.Helm.ClickHouse.LbService](#rqsrshelmclickhouselbservice)
    * 5.12 [Pod Settings](#pod-settings)
        * 5.12.1 [RQ.SRS.Helm.ClickHouse.PodSettings](#rqsrshelmclickhousepodsettings)
    * 5.13 [Extra Config](#extra-config)
        * 5.13.1 [RQ.SRS.Helm.ClickHouse.ExtraConfig](#rqsrshelmclickhouseextraconfig)
    * 5.14 [Init Scripts](#init-scripts)
        * 5.14.1 [RQ.SRS.Helm.ClickHouse.InitScripts](#rqsrshelmclickhouseinitscripts)
* 6 [Keeper Configuration](#keeper-configuration)
    * 6.1 [Keeper Enabled](#keeper-enabled)
        * 6.1.1 [RQ.SRS.Helm.Keeper.Enabled](#rqsrshelmkeeperenabled)
    * 6.2 [Replica Count](#replica-count)
        * 6.2.1 [RQ.SRS.Helm.Keeper.ReplicaCount](#rqsrshelmkeeperreplicacount)
    * 6.3 [Keeper Image](#keeper-image)
        * 6.3.1 [RQ.SRS.Helm.Keeper.Image](#rqsrshelmkeeperimage)
    * 6.4 [Storage](#storage)
        * 6.4.1 [RQ.SRS.Helm.Keeper.Storage](#rqsrshelmkeeperstorage)
    * 6.5 [Resources](#resources)
        * 6.5.1 [RQ.SRS.Helm.Keeper.Resources](#rqsrshelmkeeperresources)
* 7 [Operator Configuration](#operator-configuration)
    * 7.1 [Operator Enabled](#operator-enabled)
        * 7.1.1 [RQ.SRS.Helm.Operator.Enabled](#rqsrshelmoperatorenabled)
* 8 [Terminology](#terminology)
* 9 [Helm Chart](#helm-chart)
* 10 [Values.yaml](#valuesyaml)
* 11 [Release](#release)
* 12 [CRD](#crd)
* 13 [PVC](#pvc)
* 14 [Pod Anti-Affinity](#pod-anti-affinity)

## Introduction

Altinity.Cloud Anywhere lets you take advantage of Altinity’s zero-maintenance ClickHouse SaaS platform in your own
Kubernetes cluster. Customers bring their Kubernetes (BYOK) environments, and Altinity deploys ClickHouse clusters on 
top of them using Helm charts.

This specification describes requirements related to using Helm for deploying and configuring Altinity.Cloud Anywhere 
in the customer’s infrastructure.

---



## RQ.SRS.Helm
version: 1.0

The [Helm Chart] SHALL allow users to deploy and configure ClickHouse environments in [Kubernetes] clusters.

## Helm Chart Example

### RQ.SRS.Helm.Chart.Values
version: 1.0

The Helm chart SHALL provide a `values.yaml` file where users define their desired environment configuration.

```yaml
clickhouse:
  replicasCount: 3
  shardsCount: 2
  antiAffinity: true
  persistence:
    enabled: true
    size: 100Gi
  service:
    type: ClusterIP
```

---

## Chart Metadata

### Name Override

#### RQ.SRS.Helm.Metadata.NameOverride
version: 1.0

The `values.yaml` SHALL support `nameOverride` to override the chart name.

```yaml
nameOverride: "custom-clickhouse"
```

If invalid characters are used (e.g., spaces, special characters), Helm SHALL raise a template rendering error.

### Fullname Override

#### RQ.SRS.Helm.Metadata.FullnameOverride
version: 1.0

The `values.yaml` SHALL support `fullnameOverride` to override the full release name.

```yaml
fullnameOverride: "acme-clickhouse-prod"
```

### Namespace Domain Pattern

#### RQ.SRS.Helm.Metadata.NamespaceDomainPattern
version: 1.0

The `values.yaml` SHALL support `namespaceDomainPattern` for specifying a custom Kubernetes cluster domain.

```yaml
namespaceDomainPattern: "acme.k8s.cluster.local"
```

If empty, the default `cluster.local` SHALL be used.

---

## ClickHouse Configuration

### Default User

#### RQ.SRS.Helm.ClickHouse.DefaultUser
version: 1.0

The chart SHALL configure a default ClickHouse user.

```yaml
clickhouse:
  defaultUser:
    password: "SuperSecret"
    allowExternalAccess: true
    hostIP: "0.0.0.0/0"
```

Error Handling:

* If `password` is empty → Helm SHALL reject with: *"defaultUser.password is required"*.
* If `hostIP` is invalid → Helm SHALL raise an error during CRD validation.

### Users

#### RQ.SRS.Helm.ClickHouse.Users
version: 1.0

The chart SHALL allow defining additional users.

```yaml
clickhouse:
  users:
    - name: analytics
      password_secret_name: analytics-secret
      grants:
        - "GRANT SELECT ON default.*"
```

* `name` MUST match regex `^[a-zA-Z0-9]+$`.
* If invalid → Helm SHALL raise: *"Invalid username format"*.
* Either `password_secret_name` OR `password_sha256_hex` SHALL be required.

### Replicas Count

#### RQ.SRS.Helm.ClickHouse.ReplicasCount
version: 1.0

The `replicasCount` SHALL define number of ClickHouse replicas.

```yaml
clickhouse:
  replicasCount: 3
```

* If greater than 1, `keeper.enabled` MUST be `true` or `keeper.host` MUST be provided.

Error Handling:

* If `replicasCount > 1` but Keeper not enabled → Helm SHALL raise: *"Keeper required for replicasCount > 1"*.

### Shards Count

#### RQ.SRS.Helm.ClickHouse.ShardsCount
version: 1.0

The `shardsCount` SHALL define number of shards.

```yaml
clickhouse:
  shardsCount: 2
```

If set to 0 → Helm SHALL raise: *"shardsCount must be at least 1"*.

### Zones

#### RQ.SRS.Helm.ClickHouse.Zones
version: 1.0

The `zones` SHALL define Kubernetes zones.

```yaml
clickhouse:
  zones: ["zone-a", "zone-b"]
```

If zone list does not match cluster topology → scheduling SHALL fail.

### Anti Affinity

#### RQ.SRS.Helm.ClickHouse.AntiAffinity
version: 1.0

The `antiAffinity` flag SHALL enforce pod anti-affinity.

```yaml
clickhouse:
  antiAffinity: true
```

If enabled, ClickHouse pods SHALL not run on the same node.

### Keeper

#### RQ.SRS.Helm.ClickHouse.Keeper
version: 1.0

The chart SHALL allow external or embedded Keeper.

```yaml
clickhouse:
  keeper:
    host: "keeper-service"
    port: 2181
```

If `replicasCount > 1` but Keeper is not configured, Helm SHALL raise an error.

### Persistence

#### RQ.SRS.Helm.ClickHouse.Persistence
version: 1.0

The chart SHALL support persistent volumes.

```yaml
clickhouse:
  persistence:
    enabled: true
    size: 100Gi
    accessMode: ReadWriteOnce
```

Error Handling:

* If `enabled: true` but `size` missing → Helm SHALL raise: *"persistence.size required"*.

### ClickHouse Image

#### RQ.SRS.Helm.ClickHouse.Image
version: 1.0

The chart SHALL support custom image repo, tag, and pullPolicy.

```yaml
clickhouse:
  image:
    repository: altinity/clickhouse-server
    tag: "24.3"
    pullPolicy: IfNotPresent
```

### Service

#### RQ.SRS.Helm.ClickHouse.Service
version: 1.0

The chart SHALL configure a Kubernetes service.

```yaml
clickhouse:
  service:
    type: ClusterIP
```

If invalid type is specified → Helm SHALL raise: *"Invalid service type"*.

### Load Balancer Service

#### RQ.SRS.Helm.ClickHouse.LbService
version: 1.0

The chart SHALL support LoadBalancer service.

```yaml
clickhouse:
  lbService:
    enabled: true
    loadBalancerSourceRanges: ["0.0.0.0/0"]
```

If `enabled: true` without ranges → default SHALL be `0.0.0.0/0`.

### Pod Settings

#### RQ.SRS.Helm.ClickHouse.PodSettings
version: 1.0

The chart SHALL support pod annotations, labels, security context, tolerations, etc.

```yaml
clickhouse:
  podLabels:
    app: clickhouse
```

### Extra Config

#### RQ.SRS.Helm.ClickHouse.ExtraConfig
version: 1.0

The chart SHALL allow XML config overrides.

```yaml
clickhouse:
  extraConfig: |
    <yandex>
      <merge_tree>
        <parts_to_throw_insert>300</parts_to_throw_insert>
      </merge_tree>
    </yandex>
```

### Init Scripts

#### RQ.SRS.Helm.ClickHouse.InitScripts
version: 1.0

The chart SHALL allow init scripts.

```yaml
clickhouse:
  initScripts:
    enabled: true
    configMapName: "ch-init-scripts"
```

If enabled without configMapName → Helm SHALL raise: *"initScripts.configMapName required"*.

---

## Keeper Configuration

### Keeper Enabled

#### RQ.SRS.Helm.Keeper.Enabled
version: 1.0

```yaml
keeper:
  enabled: true
```

### Replica Count

#### RQ.SRS.Helm.Keeper.ReplicaCount
version: 1.0

The `replicaCount` MUST be odd.

```yaml
keeper:
  replicaCount: 3
```

If even → Helm SHALL raise: *"Keeper replicaCount must be odd"*.

### Keeper Image

#### RQ.SRS.Helm.Keeper.Image
version: 1.0

The chart SHALL allow Keeper image repo/tag.

### Storage

#### RQ.SRS.Helm.Keeper.Storage
version: 1.0

The chart SHALL allow persistent storage for Keeper.

```yaml
keeper:
  localStorage:
    size: 20Gi
    storageClass: fast-ssd
```

### Resources

#### RQ.SRS.Helm.Keeper.Resources
version: 1.0

The chart SHALL allow CPU/memory requests and limits.

```yaml
keeper:
  resources:
    cpuRequestsMs: 500
    memoryRequestsMiB: "512Mi"
```

---

## Operator Configuration

### Operator Enabled

#### RQ.SRS.Helm.Operator.Enabled
version: 1.0

The chart SHALL allow enabling the Altinity Operator.

```yaml
operator:
  enabled: true
```

---

## Terminology

## Helm Chart

A collection of Kubernetes YAML manifests packaged with metadata and configurable values.

## Values.yaml

Configuration file where users define parameters.

## Release

A deployed instance of a Helm chart.

## CRD

Custom Resource Definition – extends Kubernetes API.

## PVC

PersistentVolumeClaim for stateful storage.

## Pod Anti-Affinity

Kubernetes scheduling constraint preventing multiple pods from running on the same node.

---
""",
)
