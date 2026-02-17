# Étape 1 : Builder - Compilation avec Gradle
FROM gradle:8.5-jdk21 AS builder

WORKDIR /build

# Copier les fichiers de configuration Gradle
COPY gradle gradle/
COPY gradlew .
COPY gradlew.bat .
COPY build.gradle .
COPY settings.gradle .

# Copier le code source
COPY src src/
COPY db db/

# Compiler l'application avec Gradle
RUN gradle build -x test --no-daemon

# Étape 2 : Runtime - Image légère pour exécution
FROM eclipse-temurin:21-jre-alpine

WORKDIR /app

# Copier le JAR compilé depuis l'étape builder
COPY --from=builder /build/build/libs/workshop-organizer-*.jar app.jar

# Exposer le port
EXPOSE 8080

# Commande de démarrage
ENTRYPOINT ["java", "-jar", "app.jar"]
