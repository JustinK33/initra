package com.example.routes;

import com.example.controllers.UserController;
import io.javalin.Javalin;

public final class UserRoutes {
    private UserRoutes() {}

    public static void register(Javalin app, UserController controller) {
        app.get("/users", controller::listUsers);
        app.get("/users/{id}", controller::getUserById);
        app.post("/users", controller::createUser);
        app.put("/users/{id}", controller::updateUser);
        app.delete("/users/{id}", controller::deleteUser);
    }
}
