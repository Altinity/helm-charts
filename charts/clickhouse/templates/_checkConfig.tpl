{{/*
Configuration validation templates following GitLab pattern.
See: https://docs.gitlab.com/charts/development/checkconfig/

All templates follow naming convention: clickhouse.checkConfig.*
*/}}

{{/* Main aggregator template - collects all validation messages */}}
{{- define "clickhouse.checkConfig" -}}
{{- $messages := list -}}

{{/* Add individual check templates here */}}
{{- $messages = append $messages (include "clickhouse.checkConfig.keeper.required" .) -}}
{{- $messages = append $messages (include "clickhouse.checkConfig.keeper.oddReplicas" .) -}}

{{/* Filter empty messages and fail if any errors */}}
{{- $messages = without $messages "" -}}
{{- if $messages }}
{{- fail (printf "\n\nCONFIGURATION ERRORS:\n%s" (join "\n" $messages)) -}}
{{- end -}}
{{- end -}}

{{/*
clickhouse.checkConfig.keeper.required
Validates that keeper is configured when running multiple replicas.
*/}}
{{- define "clickhouse.checkConfig.keeper.required" -}}
{{- if and (or (gt (.Values.clickhouse.replicasCount | int) 1) (not (empty .Values.clickhouse.zones))) (not (or .Values.keeper.enabled .Values.clickhouse.keeper.host)) -}}
clickhouse: When 'clickhouse.replicasCount' > 1 or 'clickhouse.zones' is set, either 'keeper.enabled' must be true or 'clickhouse.keeper.host' must be set.
{{- end -}}
{{- end -}}

{{/*
clickhouse.checkConfig.keeper.oddReplicas
Validates that keeper replica count is an odd number for proper quorum.
*/}}
{{- define "clickhouse.checkConfig.keeper.oddReplicas" -}}
{{- if .Values.keeper.enabled -}}
{{- $count := .Values.keeper.replicaCount | int -}}
{{- if eq (mod $count 2) 0 -}}
keeper: The 'keeper.replicaCount' must be an odd number (1, 3, 5, etc.) for proper quorum. Current value: {{ $count }}
{{- end -}}
{{- end -}}
{{- end -}}
