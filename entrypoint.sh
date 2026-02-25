#!/bin/sh
set -e

# Attendre que la base PostgreSQL soit disponible
echo "Attente de disponibilité de PostgreSQL..."
while ! pg_isready -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" -U "$POSTGRES_USER" -d "$POSTGRES_DB"; do
  echo "PostgreSQL n'est pas encore disponible, nouvelle tentative dans 2 secondes..."
  sleep 2
done

echo "PostgreSQL est maintenant disponible! Démarrage de l'application..."

# Lancer l'application
exec java -jar app.jar
