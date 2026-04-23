package com.example.routes;

import com.example.controllers.HealthController;
import io.javalin.Javalin;

public final class HealthRoutes {
    private HealthRoutes() {}

    public static void register(Javalin app, HealthController controller) {
        app.get("/health", controller::health);
    }
}
