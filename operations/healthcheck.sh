#!/usr/bin/env bash
set -euo pipefail

DISK_WARN_PERCENT="${DISK_WARN_PERCENT:-80}"
MEMORY_WARN_MB="${MEMORY_WARN_MB:-2048}"

timestamp="$(date --iso-8601=seconds)"
disk_used="$(df -P / | awk 'NR==2 {gsub(/%/, "", $5); print $5}')"
memory_available_mb="$(awk '/MemAvailable/ {printf "%d", $2/1024}' /proc/meminfo)"
onyx_http="$(curl -sS -o /dev/null -w '%{http_code}' --max-time 5 http://127.0.0.1/api/health || true)"
ops_status="$(docker inspect cloudorder-ops-api --format '{{if .State.Health}}{{.State.Health.Status}}{{else}}{{.State.Status}}{{end}}' 2>/dev/null || echo missing)"
bad_containers="$(docker ps -a --filter 'name=onyx-' --format '{{.Names}} {{.Status}}' | awk '!/ Up / {print}' | paste -sd ';' -)"

status="ok"
reasons=()
if (( disk_used >= DISK_WARN_PERCENT )); then
  status="warning"
  reasons+=("disk_usage_high")
fi
if (( memory_available_mb < MEMORY_WARN_MB )); then
  status="warning"
  reasons+=("memory_low")
fi
if [[ "$onyx_http" != "200" ]]; then
  status="critical"
  reasons+=("onyx_health_failed")
fi
if [[ "$ops_status" != "healthy" ]]; then
  status="critical"
  reasons+=("ops_api_unhealthy")
fi
if [[ -n "$bad_containers" ]]; then
  status="critical"
  reasons+=("container_not_running")
fi

reason_json="$(printf '%s\n' "${reasons[@]:-}" | awk 'NF {printf "%s\"%s\"", sep, $0; sep=","}')"
printf '{"timestamp":"%s","status":"%s","disk_used_percent":%s,"memory_available_mb":%s,"onyx_http":%s,"ops_api":"%s","reasons":[%s]}\n' \
  "$timestamp" "$status" "$disk_used" "$memory_available_mb" "${onyx_http:-0}" "$ops_status" "$reason_json"

[[ "$status" != "critical" ]]

