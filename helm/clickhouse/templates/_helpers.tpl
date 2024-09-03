{{/*
Expand the name of the chart.
*/}}
{{- define "clickhouse.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Create a default fully qualified app name.
We truncate at 63 chars because some Kubernetes name fields are limited to this (by the DNS naming spec).
If release name contains chart name it will be used as a full name.
*/}}
{{- define "clickhouse.fullname" -}}
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
Create chart name and version as used by the chart label.
*/}}
{{- define "clickhouse.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Cluster Name
*/}}
{{- define "clickhouse.clustername" -}}
{{- printf "%s" .Release.Name | replace "+" "_" | trunc 15 | trimSuffix "-" }}
{{- end }}

{{/*
Pod Template Base
*/}}
{{- define "clickhouse.podTemplateBase" }}
        metadata:
          {{- with .Values.podAnnotations }}
          annotations:
            {{- toYaml . | nindent 12 }}
          {{- end }}
          labels:
            {{- include "clickhouse.labels" . | nindent 12 }}
            {{- with .Values.podLabels }}
            {{- toYaml . | nindent 12 }}
            {{- end }}
        podDistribution:
          {{- toYaml .Values.podDistribution | nindent 12 }}
        spec:
          {{- with .Values.imagePullSecrets }}
          imagePullSecrets:
            {{- toYaml . | nindent 12 }}
          {{- end }}
          securityContext:
            {{- toYaml .Values.podSecurityContext | nindent 12 }}
          containers:
            - name: {{ .Chart.Name }}
              securityContext:
                {{- toYaml .Values.securityContext | nindent 16 }}
              image: "{{ .Values.image.repository }}:{{ .Values.image.tag | default .Chart.AppVersion }}"
              imagePullPolicy: {{ .Values.image.pullPolicy }}
              {{- with .Values.livenessProbe }}
              livenessProbe:
                {{- toYaml . | nindent 16 }}
              {{- end }}
              resources:
                {{- toYaml .Values.resources | nindent 16 }}
          volumes:
          {{- with .Values.volumes }}
            {{- toYaml . | nindent 12 }}
          {{- end }}
          {{- with .Values.nodeSelector }}
          nodeSelector:
            {{- toYaml . | nindent 12 }}
          {{- end }}
          {{- with .Values.affinity }}
          affinity:
            {{- toYaml . | nindent 12 }}
          {{- end }}
          {{- with .Values.tolerations }}
          tolerations:
            {{- toYaml . | nindent 12 }}
          {{- end }}
{{- end -}}

{{/*
Pod Template Name
*/}}
{{- define "clickhouse.podTemplateName" -}}
{{- printf "%s-pod" (include "clickhouse.fullname" .) | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Service Template Name
*/}}
{{- define "clickhouse.serviceTemplateName" -}}
{{- printf "%s-service" (include "clickhouse.fullname" .) | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Data Volume Claim Template Name
*/}}
{{- define "clickhouse.volumeClaimTemplateName" -}}
{{- printf "%s-data" (include "clickhouse.fullname" .) | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Logs Volume Claim Template Name
*/}}
{{- define "clickhouse.logsVolumeClaimTemplateName" -}}
{{- printf "%s-logs" (include "clickhouse.fullname" .) | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
User Credentials Name
*/}}
{{- define "clickhouse.credentialsName" -}}
  {{- $fullname := include "clickhouse.fullname" . | replace "+" "_" | trunc 63 | trimSuffix "-" -}}
  {{- printf "%s-credentials" $fullname -}}
{{- end }}

{{/*
User Host IP
*/}}
{{- define "clickhouse.defaultUser.ip" -}}
{{- if .Values.defaultUser.allowExternalAccess -}}
0.0.0.0/0
{{- else -}}
{{- if .Values.defaultUser.hostIP -}}
{{ .Values.defaultUser.hostIP }}
{{- else -}}
127.0.0.1/32
{{- end -}}
{{- end -}}
{{- end -}}

{{/*
Keeper Host
*/}}
{{- define "clickhouse.keeper.host" -}}
  {{- if not (empty .Values.clickhouse.keeper.host) -}}
    {{ .Values.clickhouse.keeper.host }}
  {{- else -}}
    {{- if .Values.keeper.enabled -}}
      {{- include "clickhouse-keeper.fullname" (dict "Chart" (index .Subcharts "clickhouse-keeper" "Chart") "Release" .Release "Values" (index .Values "clickhouse-keeper")) -}}
    {{- else -}}
      ""
    {{- end -}}
  {{- end -}}
{{- end -}}

{{/*
Common labels
*/}}
{{- define "clickhouse.labels" -}}
helm.sh/chart: {{ include "clickhouse.chart" . }}
{{ include "clickhouse.selectorLabels" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}

{{/*
Selector labels
*/}}
{{- define "clickhouse.selectorLabels" -}}
app.kubernetes.io/name: {{ include "clickhouse.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}
