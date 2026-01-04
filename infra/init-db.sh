#!/bin/bash
set -e

# Script para criar múltiplos bancos de dados no PostgreSQL
# Este script é executado automaticamente quando o container é iniciado pela primeira vez

echo "Creating databases..."

# Criar banco chat_db se não existir
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    DO \$\$
    BEGIN
        IF NOT EXISTS (SELECT FROM pg_database WHERE datname = 'chat_db') THEN
            CREATE DATABASE chat_db;
        END IF;
    END
    \$\$;
EOSQL

# Criar banco keycloak_db se não existir
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    DO \$\$
    BEGIN
        IF NOT EXISTS (SELECT FROM pg_database WHERE datname = 'keycloak_db') THEN
            CREATE DATABASE keycloak_db;
        END IF;
    END
    \$\$;
EOSQL

# Ativar extensão pgvector no banco chat_db
echo "Enabling pgvector extension on chat_db"
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "chat_db" <<-EOSQL
    CREATE EXTENSION IF NOT EXISTS vector;
EOSQL

echo "Databases created successfully!"

