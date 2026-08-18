FROM maven:3.9.8-eclipse-temurin-21 AS build
WORKDIR /workspace
COPY pom.xml ./
RUN mvn -q -DskipTests dependency:go-offline
COPY src ./src
RUN mvn -q -DskipTests clean package

FROM eclipse-temurin:21-jre
WORKDIR /app
COPY --from=build /workspace/target/{{project_name}}-1.0.0-SNAPSHOT.jar /app/app.jar
EXPOSE 7000
ENTRYPOINT ["java", "-jar", "/app/app.jar"]
