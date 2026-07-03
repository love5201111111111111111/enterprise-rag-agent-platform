#!/usr/bin/env bash
set -euo pipefail

BACKUP_ROOT="${BACKUP_ROOT:-/home/ubuntu/onyx_backups/postgres}"
RETENTION_DAYS="${RETENTION_DAYS:-7}"
CONTAINER="${POSTGRES_CONTAINER:-onyx-relational_db-1}"
timestamp="$(date +%Y%m%d_%H%M%S)"
target="${BACKUP_ROOT}/onyx_${timestamp}.sql.gz"

mkdir -p "$BACKUP_ROOT"
chmod 700 "$(dirname "$BACKUP_ROOT")" "$BACKUP_ROOT"

lock_file="${BACKUP_ROOT}/.backup.lock"
exec 9>"$lock_file"
flock -n 9 || { echo "backup already running" >&2; exit 1; }

tmp="${target}.tmp"
trap 'rm -f "$tmp"' EXIT

docker exec "$CONTAINER" pg_dump -U postgres -d postgres --no-owner --no-privileges | gzip -9 > "$tmp"
test -s "$tmp"
gzip -t "$tmp"
mv "$tmp" "$target"
chmod 600 "$target"

find "$BACKUP_ROOT" -maxdepth 1 -type f -name 'onyx_*.sql.gz' -mtime "+$RETENTION_DAYS" -delete

size_bytes="$(stat -c '%s' "$target")"
sha256="$(sha256sum "$target" | awk '{print $1}')"
printf '{"backup":"%s","size_bytes":%s,"sha256":"%s","retention_days":%s}\n' \
  "$target" "$size_bytes" "$sha256" "$RETENTION_DAYS"

