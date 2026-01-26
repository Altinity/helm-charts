{{/*
Validations
*/}}
{{- define "validate.clickhouse.keeper" -}}
  {{- if and (or (gt (.Values.clickhouse.replicasCount | int) 1) (not (empty .Values.clickhouse.zones))) (not (or .Values.keeper.enabled .Values.clickhouse.keeper.host)) }}
    {{- fail "When 'clickhouse.replicasCount' > 1, either 'keeper.enabled' must be true or 'clickhouse.keeper.host' must be set." }}
  {{- end -}}
{{- end -}}

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

{{- define "clickhouse.version" -}}
{{ .Values.clickhouse.image.repository }}:{{ .Values.clickhouse.image.tag | default .Chart.AppVersion }}
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
Pod Distribution
*/}}
{{- define "clickhouse.podDistribution" -}}
{{- if .Values.clickhouse.antiAffinity -}}
- type: ClickHouseAntiAffinity
  scope: {{ .Values.clickhouse.antiAffinityScope | default "ClickHouseInstallation" }}
{{- else -}}
[]
{{- end }}
{{- end }}

{{/*
Pod Template Base
*/}}
{{- define "clickhouse.podTemplateBase" }}
        metadata:
          {{- with .Values.clickhouse.podAnnotations }}
          annotations:
            {{- toYaml . | nindent 12 }}
          {{- end }}
          labels:
            {{- include "clickhouse.labels" . | nindent 12 }}
            {{- with .Values.clickhouse.podLabels }}
            {{- toYaml . | nindent 12 }}
            {{- end }}
        podDistribution:
          {{- include "clickhouse.podDistribution" . | nindent 10 }}
        spec:
          {{- with .Values.clickhouse.imagePullSecrets }}
          imagePullSecrets:
            {{- toYaml . | nindent 12 }}
          {{- end }}
          {{- if or .Values.clickhouse.serviceAccount.create .Values.clickhouse.serviceAccount.name }}
          serviceAccountName: {{ include "clickhouse.serviceAccountName" . }}
          {{- end }}
          securityContext:
            {{- toYaml .Values.clickhouse.podSecurityContext | nindent 12 }}
          containers:
            - name: {{ .Chart.Name }}
              securityContext:
                {{- toYaml .Values.clickhouse.securityContext | nindent 16 }}
              image: "{{ .Values.clickhouse.image.repository }}:{{ .Values.clickhouse.image.tag | default .Chart.AppVersion }}"
              imagePullPolicy: {{ .Values.clickhouse.image.pullPolicy }}
              ports:
                - name: http
                  containerPort: 8123
                - name: client
                  containerPort: 9000
                - name: interserver
                  containerPort: 9009
                {{- if .Values.clickhouse.extraPorts }}
                {{- toYaml .Values.clickhouse.extraPorts | nindent 16 }}
                {{- end }}
              {{- with .Values.clickhouse.livenessProbe }}
              livenessProbe:
                {{- toYaml . | nindent 16 }}
              {{- end }}
              {{- if .Values.clickhouse.initScripts.enabled }}
              env:
                {{- if .Values.clickhouse.initScripts.alwaysRun }}
                - name: CLICKHOUSE_ALWAYS_RUN_INITDB_SCRIPTS
                  value: "true"
                {{- end }}
              volumeMounts:
                - name: init-scripts-configmap
                  mountPath: /docker-entrypoint-initdb.d
              {{- end }}
              resources:
                {{- toYaml .Values.clickhouse.resources | nindent 16 }}
            {{- range .Values.clickhouse.extraContainers }}
            - name: {{ .name }}
              image: {{ .image }}
              {{- with .command }}
              command: {{ toYaml . | nindent 16 }}
              {{- end }}
              {{- with .env }}
              env: {{ toYaml . | nindent 16 }}
              {{- end }}
              {{- with .ports }}
              ports: {{ toYaml . | nindent 16 }}
              {{- end }}
              {{- with .resources }}
              resources: {{ toYaml . | nindent 16 }}
              {{- end }}
              {{- if .mounts }}
              volumeMounts:
                {{- if .mounts.data }}
                - name: {{ include "clickhouse.dataVolumeName" $ }}
                  mountPath: /var/lib/clickhouse
                {{- end }}
              {{- end }}
            {{- end }}
          {{- if or .Values.clickhouse.initScripts.enabled .Values.clickhouse.extraVolumes }}
          volumes:
            {{- if .Values.clickhouse.initScripts.enabled }}
            - name: init-scripts-configmap
              configMap:
                name: {{ .Values.clickhouse.initScripts.configMapName }}
            {{- end }}
            {{- with .Values.clickhouse.extraVolumes }}
            {{- toYaml . | nindent 12 }}
            {{- end }}
          {{- end }}
          {{- with .Values.clickhouse.nodeSelector }}
          nodeSelector:
            {{- toYaml . | nindent 12 }}
          {{- end }}
          {{- with .Values.clickhouse.affinity }}
          affinity:
            {{- toYaml . | nindent 12 }}
          {{- end }}
          {{- with .Values.clickhouse.tolerations }}
          tolerations:
            {{- toYaml . | nindent 12 }}
          {{- end }}
          {{- with .Values.clickhouse.topologySpreadConstraints }}
          topologySpreadConstraints:
            {{- toYaml . | nindent 12 }}
          {{- end }}
{{- end -}}

{{/*
Pod Template Name
*/}}
{{- define "clickhouse.podTemplateName" -}}
{{- $podDescString := printf "%s-%s" (include "clickhouse.fullname" .) (include "clickhouse.version" .) }}
{{- $podHash := $podDescString | sha256sum | trunc 8 }} 
{{- printf "%s-pod-%s" (include "clickhouse.fullname" .) $podHash | replace "+" "_" | trunc 63 | trimSuffix "-" }}
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
Data Volume Name
*/}}
{{- define "clickhouse.dataVolumeName" -}}
{{- printf "%s-%s-data" .Release.Name (.Values.nameOverride | default "clickhouse") -}}
{{- end -}}

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
{{- if .Values.clickhouse.defaultUser.allowExternalAccess -}}
0.0.0.0/0
{{- else -}}
{{- if .Values.clickhouse.defaultUser.hostIP -}}
{{ .Values.clickhouse.defaultUser.hostIP }}
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
      {{- printf "keeper-%s" (include "clickhouse.fullname" .) | replace "+" "_" | trunc 63 | trimSuffix "-" }}
    {{- else -}}
    {{- end -}}
  {{- end -}}
{{- end -}}

{{/*
Extra Config
*/}}
{{- define "clickhouse.extraConfig" -}}
  {{- if not (empty .Values.clickhouse.extraConfig) -}}
    {{ .Values.clickhouse.extraConfig }}
  {{- else -}}
  {{- end -}}
{{- end -}}
{{/*
Extra Users
*/}}
{{- define "clickhouse.extraUsers" -}}
  {{- if not (empty .Values.clickhouse.extraUsers) -}}
    {{ .Values.clickhouse.extraUsers }}
  {{- else -}}
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

{{/*
Create the name of the service account to use
*/}}
{{- define "clickhouse.serviceAccountName" -}}
{{- if .Values.clickhouse.serviceAccount.create }}
{{- default (include "clickhouse.fullname" .) .Values.clickhouse.serviceAccount.name }}
{{- else }}
{{- default "default" .Values.clickhouse.serviceAccount.name }}
{{- end }}
{{- end }}
