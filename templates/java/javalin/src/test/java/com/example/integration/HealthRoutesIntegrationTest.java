package com.example.integration;

import static org.junit.jupiter.api.Assertions.assertEquals;

import com.example.config.AppConfig;
import com.example.controllers.HealthController;
import com.example.middleware.ExceptionMapper;
import com.example.middleware.RequestLoggingMiddleware;
import com.example.routes.HealthRoutes;
import io.javalin.Javalin;
import io.javalin.testtools.JavalinTest;
import org.junit.jupiter.api.Test;
import okhttp3.Response;

class HealthRoutesIntegrationTest {
    @Test
    void healthEndpointReturns200() {
        AppConfig config = new AppConfig("{{project_name}}", "test", 0);
        HealthController healthController = new HealthController(config);
        Javalin app = Javalin.create();
        RequestLoggingMiddleware.register(app);
        ExceptionMapper.register(app);
        HealthRoutes.register(app, healthController);

        JavalinTest.test(app, (server, client) -> {
            try (Response response = client.get("/health")) {
                assertEquals(200, response.code());
            }
        });
    }
}
