#!/usr/bin/env bash
set -Eeuo pipefail

ARCHIVE=""
IMAGE_ARCHIVE=""
TARGET=""
REVISION="unknown"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --archive) ARCHIVE="$2"; shift 2 ;;
    --image) IMAGE_ARCHIVE="$2"; shift 2 ;;
    --target) TARGET="$2"; shift 2 ;;
    --revision) REVISION="$2"; shift 2 ;;
    *) echo "Unknown argument: $1" >&2; exit 2 ;;
  esac
done

if [[ -z "$ARCHIVE" || -z "$TARGET" ]]; then
  echo "Usage: $0 --archive FILE --target DIRECTORY [--image FILE] [--revision SHA]" >&2
  exit 2
fi
if [[ ! -f "$ARCHIVE" ]]; then
  echo "Release archive does not exist: $ARCHIVE" >&2
  exit 2
fi
if [[ -n "$IMAGE_ARCHIVE" && ! -f "$IMAGE_ARCHIVE" ]]; then
  echo "Container image archive does not exist: $IMAGE_ARCHIVE" >&2
  exit 2
fi
if [[ "$TARGET" != /home/*/cloudorder-ops-api ]]; then
  echo "Refusing unexpected deployment target: $TARGET" >&2
  exit 2
fi
if [[ ! -f "$TARGET/.env" ]]; then
  echo "Required deployment secret file is missing: $TARGET/.env" >&2
  exit 2
fi

if docker info >/dev/null 2>&1; then
  DOCKER=(docker)
else
  DOCKER=(sudo docker)
fi

LOCK_FILE="/tmp/cloudorder-ops-api.deploy.lock"
exec 9>"$LOCK_FILE"
if ! flock -n 9; then
  echo "Another deployment is already running." >&2
  exit 1
fi

STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
WORK_DIR="$(mktemp -d /tmp/cloudorder-release.XXXXXX)"
BACKUP_DIR="${TARGET}.rollback-${STAMP}"
ROLLBACK_IMAGE="cloudorder-ops-api:rollback-${STAMP}"
CANDIDATE_IMAGE="cloudorder-ops-api:candidate-${STAMP}"
PREVIOUS_IMAGE_ID="$("${DOCKER[@]}" image inspect cloudorder-ops-api:1.0.0 --format '{{.Id}}' 2>/dev/null || true)"

cleanup() {
  rm -rf "$WORK_DIR"
  rm -f "$ARCHIVE"
  if [[ -n "$IMAGE_ARCHIVE" ]]; then
    rm -f "$IMAGE_ARCHIVE"
  fi
  "${DOCKER[@]}" image rm "$CANDIDATE_IMAGE" >/dev/null 2>&1 || true
}
trap cleanup EXIT

tar -xzf "$ARCHIVE" -C "$WORK_DIR"
NEW_SOURCE="$WORK_DIR/cloudorder-ops-api"
for required in Dockerfile docker-compose.yml requirements.txt app/main.py; do
  if [[ ! -f "$NEW_SOURCE/$required" ]]; then
    echo "Release is missing $required" >&2
    exit 1
  fi
done

cp "$TARGET/.env" "$NEW_SOURCE/.env"
if [[ -n "$PREVIOUS_IMAGE_ID" ]]; then
  "${DOCKER[@]}" tag "$PREVIOUS_IMAGE_ID" "$ROLLBACK_IMAGE"
fi

if [[ -n "$IMAGE_ARCHIVE" ]]; then
  echo "Loading CI-built container image for revision $REVISION..."
  "${DOCKER[@]}" load -i "$IMAGE_ARCHIVE"
else
  echo "Building candidate container image on the deployment host for revision $REVISION..."
  "${DOCKER[@]}" build --tag "$CANDIDATE_IMAGE" "$NEW_SOURCE"
fi

echo "Creating rollback copy at $BACKUP_DIR"
cp -a "$TARGET" "$BACKUP_DIR"

rollback() {
  trap - ERR
  echo "Deployment failed; restoring previous source and container." >&2
  rm -rf "$TARGET"
  mv "$BACKUP_DIR" "$TARGET"
  if "${DOCKER[@]}" image inspect "$ROLLBACK_IMAGE" >/dev/null 2>&1; then
    "${DOCKER[@]}" tag "$ROLLBACK_IMAGE" cloudorder-ops-api:1.0.0
  fi
  "${DOCKER[@]}" compose --project-directory "$TARGET" up -d --force-recreate --no-build
}
trap rollback ERR

find "$TARGET" -mindepth 1 -maxdepth 1 ! -name .env -exec rm -rf -- {} +
cp -a "$NEW_SOURCE"/. "$TARGET"/
if [[ -z "$IMAGE_ARCHIVE" ]]; then
  "${DOCKER[@]}" tag "$CANDIDATE_IMAGE" cloudorder-ops-api:1.0.0
fi
printf '%s\n' "$REVISION" > "$TARGET/.deployed-revision"
"${DOCKER[@]}" compose --project-directory "$TARGET" up -d --no-build

for _ in $(seq 1 30); do
  STATUS="$("${DOCKER[@]}" inspect --format '{{if .State.Health}}{{.State.Health.Status}}{{else}}{{.State.Status}}{{end}}' cloudorder-ops-api 2>/dev/null || true)"
  if [[ "$STATUS" == "healthy" ]]; then
    curl --fail --silent http://127.0.0.1:8080/health >/dev/null || true
    rm -rf "$BACKUP_DIR"
    "${DOCKER[@]}" image rm "$ROLLBACK_IMAGE" >/dev/null 2>&1 || true
    trap - ERR
    echo "Deployment succeeded: $REVISION"
    exit 0
  fi
  if [[ "$STATUS" == "unhealthy" || "$STATUS" == "exited" ]]; then
    echo "Container entered terminal status: $STATUS" >&2
    exit 1
  fi
  sleep 2
done

echo "Timed out waiting for a healthy container." >&2
exit 1
