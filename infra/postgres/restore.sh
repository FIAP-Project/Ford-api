#!/usr/bin/env bash
# Rotina de recuperação: restaura um dump gerado por backup.sh para o
# container Postgres em execução. Destrutivo — recria o schema public
# a partir do zero (--clean --if-exists), então valide o arquivo antes.
#
# Uso: ./infra/postgres/restore.sh backups/ford-20260101T030000Z.dump
set -euo pipefail

cd "$(dirname "$0")/../.."

if [[ $# -ne 1 ]]; then
  echo "Uso: $0 <caminho-do-dump>" >&2
  exit 1
fi

DUMP_FILE="$1"
if [[ ! -f "$DUMP_FILE" ]]; then
  echo "Arquivo não encontrado: ${DUMP_FILE}" >&2
  exit 1
fi

set -a
# shellcheck disable=SC1091
source .env
set +a

docker compose cp "$DUMP_FILE" postgres:/tmp/restore.dump

docker compose exec -T postgres pg_restore \
  -U "$POSTGRES_USER" \
  -d "$POSTGRES_DB" \
  --clean --if-exists \
  /tmp/restore.dump

docker compose exec -T postgres rm /tmp/restore.dump

echo "Restore concluído a partir de ${DUMP_FILE}"
