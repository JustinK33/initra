package com.example.integration;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertTrue;

import com.example.controllers.UserController;
import com.example.middleware.ExceptionMapper;
import com.example.middleware.RequestLoggingMiddleware;
import com.example.repository.InMemoryUserRepository;
import com.example.repository.UserRepository;
import com.example.routes.UserRoutes;
import com.example.services.UserService;
import io.javalin.Javalin;
import io.javalin.testtools.JavalinTest;
import org.junit.jupiter.api.Test;
import okhttp3.Response;

class UserRoutesIntegrationTest {
    @Test
    void createAndGetUser() {
        UserRepository repository = new InMemoryUserRepository();
        UserService service = new UserService(repository);
        UserController controller = new UserController(service);

        Javalin app = Javalin.create();
        RequestLoggingMiddleware.register(app);
        ExceptionMapper.register(app);
        UserRoutes.register(app, controller);

        JavalinTest.test(app, (server, client) -> {
            try (Response createResponse = client.post("/users", "{\"name\":\"Taylor\",\"email\":\"taylor@example.com\"}")) {
                assertEquals(201, createResponse.code());
            }

            try (Response listResponse = client.get("/users")) {
                assertEquals(200, listResponse.code());
                assertTrue(listResponse.body().string().contains("Taylor"));
            }
        });
    }
}
