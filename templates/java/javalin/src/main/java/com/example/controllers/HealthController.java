package com.example.controllers;

import com.example.config.AppConfig;
import io.javalin.http.Context;
import java.time.Instant;

public final class HealthController {
    private final AppConfig config;

    public HealthController(AppConfig config) {
        this.config = config;
    }

    public void health(Context ctx) {
        ctx.status(200).json(new HealthResponse("ok", config.appName(), config.env(), Instant.now().toString()));
    }

    public record HealthResponse(String status, String appName, String env, String timestamp) {}
}
