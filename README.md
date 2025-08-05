# Altinity Helm Charts for ClickHouse®

Helm charts for use with the Altinity Operator for ClickHouse®

## Running ClickHouse on Kubernetes with the Altinity Operator
A complete Kubernetes deployment of ClickHouse includes:

 - The Altinity Operator for ClickHouse
 - The Altinity Operator CRDs
 - A `ClickHouseInstallation` Custom Resource defining your ClickHouse cluster settings
 - A `ClickHouseKeeperInstallation` Custom Resource defining your Keeper deployment (optional for single-node instances)
 - A custom storage class (optional) - we recommend gp3 in production.

For convenience, the [ClickHouse](./charts/clickhouse) chart in this repo includes the [Operator Helm Chart](https://github.com/Altinity/clickhouse-operator/tree/master/deploy/helm/clickhouse-operator) as a dependency. 

These samples demonstrate straightforward Helm charts that can be used to deploy ClickHouse and ClickHouse Keeper. The examples are intended as starting points for more complex configurations and do not cover all possible uses cases.

For more complex configurations, follow the [Installation Guide](https://docs.altinity.com/altinitykubernetesoperator/quickstartinstallation/) from the documentation to install the Operator and create a custom `ClickHouseInstallation` resource.

**Installing the Operator first provides better control when uninstalling clusters.**

> Please refer to the Altinity Operator project instructions for details on operator upgrade with Helm, including running custom resource definition files independently.

## Helm Charts

- **[clickhouse](./charts/clickhouse/)**: All-in-one chart to deploy a ClickHouse cluster (and optionally Keeper and the Altinity Operator)
- **[clickhouse-eks](./charts/clickhouse-eks/)**: An EKS-specific chart for high-availability ClickHouse clusters. 

## Community

These charts are a community effort sponsored by Altinity. The best way to reach us or ask questions is:

* Join the [Altinity Slack](https://altinity.com/slack) - Chat with the developers and other users
* Log an [issue on GitHub](https://github.com/Altinity/helm-charts/issues) - Ask questions, log bugs and feature requests

## Contributing
We welcome contributions from the community! If you encounter issues or have improvements to suggest, please log an issue or submit a PR.

## Legal
All code, unless specified otherwise, is licensed under the [Apache-2.0](LICENSE) license.
Copyright (c) 2025 Altinity, Inc.
Altinity.Cloud®, and Altinity Stable® are registered trademarks of Altinity, Inc. ClickHouse® is a registered trademark of ClickHouse, Inc.; Altinity is not affiliated with or associated with ClickHouse, Inc. Kubernetes, MySQL, and PostgreSQL are trademarks and property of their respective owners.

## Commercial Support

Altinity is the primary maintainer of the operator. It is the basis of Altinity.Cloud and
is also used in self-managed installations. Altinity offers a range of 
services related to ClickHouse and analytic applications on Kubernetes. 

- [Official website](https://altinity.com/) - Get a high level overview of Altinity and our offerings.
- [Altinity.Cloud](https://altinity.com/cloud-database/) - Run ClickHouse in our cloud or yours.
- [Altinity Support](https://altinity.com/support/) - Get Enterprise-class support for ClickHouse.
- [Slack](https://altinity.com/slack) - Talk directly with ClickHouse users and Altinity devs.
- [Contact us](https://hubs.la/Q020sH3Z0) - Contact Altinity with your questions or issues.
- [Free consultation](https://hubs.la/Q020sHkv0) - Get a free consultation with a ClickHouse expert today.
