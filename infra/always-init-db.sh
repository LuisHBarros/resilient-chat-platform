#!/bin/bash
set -e

# Script que sempre verifica e cria os bancos se necessário
# Este script pode ser executado a qualquer momento, mesmo se o volume já existir

echo "Ensuring databases exist..."

# Exportar senha para evitar prompts
export PGPASSWORD=${POSTGRES_PASSWORD:-pass}

# Criar banco chat_db se não existir
DB_EXISTS=$(psql -h db --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" -tAc "SELECT 1 FROM pg_database WHERE datname='chat_db'")
if [ "$DB_EXISTS" != "1" ]; then
    echo "Creating database chat_db..."
    psql -v ON_ERROR_STOP=1 -h db --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" -c "CREATE DATABASE chat_db;"
else
    echo "Database chat_db already exists"
fi

# Ativar extensão pgvector no banco chat_db (se não estiver ativada)
echo "Ensuring pgvector extension on chat_db"
psql -v ON_ERROR_STOP=1 -h db --username "$POSTGRES_USER" --dbname "chat_db" <<-EOSQL
    CREATE EXTENSION IF NOT EXISTS vector;
EOSQL

echo "Databases ensured successfully!"

