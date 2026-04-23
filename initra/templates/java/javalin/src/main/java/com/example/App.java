package com.example;

import com.example.config.AppConfig;
import com.example.controllers.HealthController;
import com.example.controllers.UserController;
import com.example.middleware.ExceptionMapper;
import com.example.middleware.RequestLoggingMiddleware;
import com.example.repository.InMemoryUserRepository;
import com.example.repository.UserRepository;
import com.example.routes.HealthRoutes;
import com.example.routes.UserRoutes;
import com.example.services.UserService;
import io.javalin.Javalin;

public final class App {
    private App() {}

    public static void main(String[] args) {
        AppConfig config = AppConfig.fromEnvironment();
        UserRepository userRepository = new InMemoryUserRepository();
        UserService userService = new UserService(userRepository);
        HealthController healthController = new HealthController(config);
        UserController userController = new UserController(userService);

        Javalin app = Javalin.create(javalinConfig -> javalinConfig.showJavalinBanner = false);
        RequestLoggingMiddleware.register(app);
        ExceptionMapper.register(app);

        HealthRoutes.register(app, healthController);
        UserRoutes.register(app, userController);

        app.start(config.port());
    }
}
