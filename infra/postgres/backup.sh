#!/usr/bin/env bash
# Rotina de backup: dump lógico completo do Postgres via pg_dump, rodando
# dentro do container já em execução (docker compose). Gera um arquivo
# comprimido em ./backups/, um por execução, timestamped.
#
# Uso: ./infra/postgres/backup.sh
# Cron sugerido (host): 0 3 * * * cd /path/to/Ford-api && ./infra/postgres/backup.sh
set -euo pipefail

cd "$(dirname "$0")/../.."

set -a
# shellcheck disable=SC1091
source .env
set +a

BACKUP_DIR="backups"
TIMESTAMP="$(date -u +%Y%m%dT%H%M%SZ)"
BACKUP_FILE="${BACKUP_DIR}/ford-${TIMESTAMP}.dump"

mkdir -p "$BACKUP_DIR"

docker compose exec -T postgres pg_dump \
  -U "$POSTGRES_USER" \
  -d "$POSTGRES_DB" \
  --format=custom \
  --file=/tmp/backup.dump

docker compose cp postgres:/tmp/backup.dump "$BACKUP_FILE"
docker compose exec -T postgres rm /tmp/backup.dump

echo "Backup gravado em ${BACKUP_FILE}"
