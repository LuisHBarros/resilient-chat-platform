#!/bin/bash
set -e

# Script para garantir que os bancos de dados existam
# Este script pode ser executado manualmente ou via cron se necessário

echo "Ensuring databases exist..."

# Criar banco chat_db se não existir
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    DO \$\$
    BEGIN
        IF NOT EXISTS (SELECT FROM pg_database WHERE datname = 'chat_db') THEN
            CREATE DATABASE chat_db;
            RAISE NOTICE 'Database chat_db created';
        ELSE
            RAISE NOTICE 'Database chat_db already exists';
        END IF;
    END
    \$\$;
EOSQL

# Ativar extensão pgvector no banco chat_db (se não estiver ativada)
echo "Ensuring pgvector extension on chat_db"
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "chat_db" <<-EOSQL
    CREATE EXTENSION IF NOT EXISTS vector;
EOSQL

echo "Databases ensured successfully!"

