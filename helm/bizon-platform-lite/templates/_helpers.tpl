{{/*
Expand the name of the chart.
*/}}
{{- define "bizon-platform-lite.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Create a default fully qualified app name.
*/}}
{{- define "bizon-platform-lite.fullname" -}}
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
{{- define "bizon-platform-lite.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Common labels
*/}}
{{- define "bizon-platform-lite.labels" -}}
helm.sh/chart: {{ include "bizon-platform-lite.chart" . }}
{{ include "bizon-platform-lite.selectorLabels" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}

{{/*
Selector labels
*/}}
{{- define "bizon-platform-lite.selectorLabels" -}}
app.kubernetes.io/name: {{ include "bizon-platform-lite.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

{{/*
API labels
*/}}
{{- define "bizon-platform-lite.api.labels" -}}
{{ include "bizon-platform-lite.labels" . }}
app.kubernetes.io/component: api
{{- end }}

{{/*
API selector labels
*/}}
{{- define "bizon-platform-lite.api.selectorLabels" -}}
{{ include "bizon-platform-lite.selectorLabels" . }}
app.kubernetes.io/component: api
{{- end }}

{{/*
Worker labels
*/}}
{{- define "bizon-platform-lite.worker.labels" -}}
{{ include "bizon-platform-lite.labels" . }}
app.kubernetes.io/component: worker
{{- end }}

{{/*
Worker selector labels
*/}}
{{- define "bizon-platform-lite.worker.selectorLabels" -}}
{{ include "bizon-platform-lite.selectorLabels" . }}
app.kubernetes.io/component: worker
{{- end }}

{{/*
UI labels
*/}}
{{- define "bizon-platform-lite.ui.labels" -}}
{{ include "bizon-platform-lite.labels" . }}
app.kubernetes.io/component: ui
{{- end }}

{{/*
UI selector labels
*/}}
{{- define "bizon-platform-lite.ui.selectorLabels" -}}
{{ include "bizon-platform-lite.selectorLabels" . }}
app.kubernetes.io/component: ui
{{- end }}

{{/*
PostgreSQL labels
*/}}
{{- define "bizon-platform-lite.postgresql.labels" -}}
{{ include "bizon-platform-lite.labels" . }}
app.kubernetes.io/component: postgresql
{{- end }}

{{/*
PostgreSQL selector labels
*/}}
{{- define "bizon-platform-lite.postgresql.selectorLabels" -}}
{{ include "bizon-platform-lite.selectorLabels" . }}
app.kubernetes.io/component: postgresql
{{- end }}

{{/*
Create the name of the service account to use
*/}}
{{- define "bizon-platform-lite.serviceAccountName" -}}
{{- if .Values.serviceAccount.create }}
{{- default (include "bizon-platform-lite.fullname" .) .Values.serviceAccount.name }}
{{- else }}
{{- default "default" .Values.serviceAccount.name }}
{{- end }}
{{- end }}

{{/*
PostgreSQL host
*/}}
{{- define "bizon-platform-lite.postgresql.host" -}}
{{- if .Values.postgresql.enabled }}
{{- printf "%s-postgresql" (include "bizon-platform-lite.fullname" .) }}
{{- else }}
{{- .Values.externalDatabase.host }}
{{- end }}
{{- end }}

{{/*
PostgreSQL port
*/}}
{{- define "bizon-platform-lite.postgresql.port" -}}
{{- if .Values.postgresql.enabled }}
{{- 5432 }}
{{- else }}
{{- .Values.externalDatabase.port }}
{{- end }}
{{- end }}

{{/*
PostgreSQL database name
*/}}
{{- define "bizon-platform-lite.postgresql.database" -}}
{{- if .Values.postgresql.enabled }}
{{- .Values.postgresql.auth.database }}
{{- else }}
{{- .Values.externalDatabase.database }}
{{- end }}
{{- end }}

{{/*
PostgreSQL username
*/}}
{{- define "bizon-platform-lite.postgresql.username" -}}
{{- if .Values.postgresql.enabled }}
{{- .Values.postgresql.auth.username }}
{{- else }}
{{- .Values.externalDatabase.username }}
{{- end }}
{{- end }}

{{/*
PostgreSQL secret name
*/}}
{{- define "bizon-platform-lite.postgresql.secretName" -}}
{{- if .Values.postgresql.enabled }}
{{- if .Values.postgresql.auth.existingSecret }}
{{- .Values.postgresql.auth.existingSecret }}
{{- else }}
{{- printf "%s-postgresql" (include "bizon-platform-lite.fullname" .) }}
{{- end }}
{{- else }}
{{- if .Values.externalDatabase.existingSecret }}
{{- .Values.externalDatabase.existingSecret }}
{{- else }}
{{- printf "%s-external-db" (include "bizon-platform-lite.fullname" .) }}
{{- end }}
{{- end }}
{{- end }}

{{/*
Database URL (for asyncpg)
*/}}
{{- define "bizon-platform-lite.databaseUrl" -}}
postgresql+asyncpg://$(DB_USERNAME):$(DB_PASSWORD)@{{ include "bizon-platform-lite.postgresql.host" . }}:{{ include "bizon-platform-lite.postgresql.port" . }}/{{ include "bizon-platform-lite.postgresql.database" . }}
{{- end }}

{{/*
Encryption key secret name
*/}}
{{- define "bizon-platform-lite.encryptionKeySecretName" -}}
{{- if .Values.security.existingEncryptionKeySecret }}
{{- .Values.security.existingEncryptionKeySecret }}
{{- else }}
{{- printf "%s-secrets" (include "bizon-platform-lite.fullname" .) }}
{{- end }}
{{- end }}

{{/*
Admin password secret name
*/}}
{{- define "bizon-platform-lite.adminPasswordSecretName" -}}
{{- if .Values.security.existingAdminPasswordSecret }}
{{- .Values.security.existingAdminPasswordSecret }}
{{- else }}
{{- printf "%s-secrets" (include "bizon-platform-lite.fullname" .) }}
{{- end }}
{{- end }}

{{/*
Git token secret name
*/}}
{{- define "bizon-platform-lite.gitTokenSecretName" -}}
{{- if .Values.gitSync.existingTokenSecret }}
{{- .Values.gitSync.existingTokenSecret }}
{{- else }}
{{- printf "%s-secrets" (include "bizon-platform-lite.fullname" .) }}
{{- end }}
{{- end }}

{{/*
CORS allowed origins as comma-separated string
*/}}
{{- define "bizon-platform-lite.corsAllowedOrigins" -}}
{{- if kindIs "slice" .Values.config.corsAllowedOrigins }}
{{- join "," .Values.config.corsAllowedOrigins }}
{{- else }}
{{- .Values.config.corsAllowedOrigins }}
{{- end }}
{{- end }}

{{/*
Image pull secrets
*/}}
{{- define "bizon-platform-lite.imagePullSecrets" -}}
{{- with .Values.global.imagePullSecrets }}
imagePullSecrets:
{{- toYaml . | nindent 2 }}
{{- end }}
{{- end }}
