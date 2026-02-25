#!/bin/sh
set -e

# Variables d'environnement (définies dans docker-compose.yml)
POSTGRES_HOST="${POSTGRES_HOST:-db}"
POSTGRES_PORT="${POSTGRES_PORT:-5432}"
POSTGRES_USER="${POSTGRES_USER:-workshops_user}"
POSTGRES_DB="${POSTGRES_DB:-workshopsdb}"

echo "Attente de disponibilité de PostgreSQL sur ${POSTGRES_HOST}:${POSTGRES_PORT}..."

# Attendre que la base PostgreSQL soit disponible
max_attempts=30
attempt=1
while [ $attempt -le $max_attempts ]; do
  if pg_isready -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" -U "$POSTGRES_USER"; then
    echo "PostgreSQL est maintenant disponible!"
    break
  fi
  
  if [ $attempt -eq $max_attempts ]; then
    echo "Timeout: PostgreSQL n'a pas répondu après $max_attempts tentatives"
    exit 1
  fi
  
  echo "PostgreSQL n'est pas encore disponible (tentative $attempt/$max_attempts)..."
  sleep 2
  attempt=$((attempt + 1))
done

echo "Démarrage de l'application..."

# Lancer l'application
exec java -jar app.jar

