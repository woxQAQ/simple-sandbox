{{/*
Expand the name of the chart.
*/}}
{{- define "sandbox.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Create a default fully qualified app name.
*/}}
{{- define "sandbox.fullname" -}}
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
{{- define "sandbox.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Common labels
*/}}
{{- define "sandbox.labels" -}}
helm.sh/chart: {{ include "sandbox.chart" . }}
{{ include "sandbox.selectorLabels" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}

{{/*
Selector labels
*/}}
{{- define "sandbox.selectorLabels" -}}
app.kubernetes.io/name: {{ include "sandbox.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

{{/*
Environment variables for the sandbox application
*/}}
{{- define "sandbox.envVars" -}}
- name: HOST
  value: {{ .Values.app.host | quote }}
- name: PORT
  value: {{ .Values.app.port | quote }}
- name: DEBUG
  value: {{ .Values.app.debug | quote }}
- name: VERBOSE
  value: {{ .Values.app.verbose | quote }}
{{- end }}

{{/*
Network policy ingress rules
*/}}
{{- define "sandbox.networkPolicyIngressRules" -}}
# Allow traffic from same namespace
- from:
    - namespaceSelector:
        matchLabels:
          name: {{ .Release.Namespace }}
# Allow traffic on service port
- ports:
    - protocol: TCP
      port: {{ .Values.service.port }}
{{- end }}

{{/*
Network policy egress rules
*/}}
{{- define "sandbox.networkPolicyEgressRules" -}}
# Allow DNS traffic
- to: []
  ports:
    - protocol: UDP
      port: 53
    - protocol: TCP
      port: 53
# Allow Kubernetes API traffic
- to:
    - namespaceSelector:
        matchLabels:
          kubernetes.io/metadata.name: kube-system
  ports:
    - protocol: TCP
      port: 443
    - protocol: TCP
      port: 6443
{{- end }}
