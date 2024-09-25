{{/*
Expand the name of the chart.
*/}}
{{- define "clickhouse-keeper.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Create a default fully qualified app name.
We truncate at 63 chars because some Kubernetes name fields are limited to this (by the DNS naming spec).
If release name contains chart name it will be used as a full name.
*/}}
{{- define "clickhouse-keeper.fullname" -}}
{{- if .Values.fullnameOverride }}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- $name := default .Chart.Name .Values.nameOverride }}
{{- if contains $name .Release.Name }}
{{- .Release.Name | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- printf "%s-%s" .Release.Name $name | trunc 63 | trimSuffix "-" }}
{{- end }}
{{- end }}
{{- end }}

{{/*
Service Name
*/}}
{{- define "clickhouse-keeper.service-name" -}}
{{- printf "%ss" (include "clickhouse-keeper.fullname" .) }}
{{- end }}

{{/*
Create chart name and version as used by the chart label.
*/}}
{{- define "clickhouse-keeper.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Persistent Volume Claim Name
*/}}
{{- define "clickhouse-keeper.claimName" -}}
{{- printf "%s-data" (include "clickhouse-keeper.fullname" .) | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Configmap Name
*/}}
{{- define "clickhouse-keeper.configMapName" -}}
{{- printf "%s-settings" (include "clickhouse-keeper.fullname" .) | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Common labels
*/}}
{{- define "clickhouse-keeper.labels" -}}
helm.sh/chart: {{ include "clickhouse-keeper.chart" . }}
{{ include "clickhouse-keeper.selectorLabels" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}

{{/*
Selector labels
*/}}
{{- define "clickhouse-keeper.selectorLabels" -}}
app.kubernetes.io/name: {{ include "clickhouse-keeper.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

{{/*
Create the name of the service account to use
*/}}
{{- define "clickhouse-keeper.serviceAccountName" -}}
{{- if .Values.serviceAccount.create }}
{{- default (include "clickhouse-keeper.fullname" .) .Values.serviceAccount.name }}
{{- else }}
{{- default "default" .Values.serviceAccount.name }}
{{- end }}
{{- end }}
