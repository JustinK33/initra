package com.example;

import com.example.config.AppConfig;
import com.example.db.DatabaseClient;
import io.javalin.Javalin;

public final class App {
    private App() {}

    public static void main(String[] args) {
        AppConfig config = AppConfig.fromEnvironment();
        DatabaseClient db = new DatabaseClient(config.databaseUrl());

        Javalin app = Javalin.create();
        app.get("/", ctx -> ctx.json(new HealthResponse("ok", "{{project_name}}", config.env(), db.url())));
        app.start(config.port());
    }

    public record HealthResponse(String status, String project, String env, String databaseUrl) {}
}
