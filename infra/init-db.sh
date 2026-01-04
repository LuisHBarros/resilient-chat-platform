#!/bin/bash
set -e

# Script para criar múltiplos bancos de dados no PostgreSQL
# Este script é executado automaticamente quando o container é iniciado pela primeira vez
# IMPORTANTE: Este script só executa se o volume do PostgreSQL for criado pela primeira vez
# Se o volume já existir, o script NÃO será executado novamente

echo "Creating databases..."

# Exportar senha para evitar prompts
export PGPASSWORD=${POSTGRES_PASSWORD:-pass}

# Criar banco chat_db se não existir
DB_EXISTS=$(psql --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" -tAc "SELECT 1 FROM pg_database WHERE datname='chat_db'")
if [ "$DB_EXISTS" != "1" ]; then
    echo "Creating database chat_db..."
    psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" -c "CREATE DATABASE chat_db;"
else
    echo "Database chat_db already exists"
fi

# Ativar extensão pgvector no banco chat_db
echo "Enabling pgvector extension on chat_db"
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "chat_db" <<-EOSQL
    CREATE EXTENSION IF NOT EXISTS vector;
EOSQL

echo "Databases created successfully!"

