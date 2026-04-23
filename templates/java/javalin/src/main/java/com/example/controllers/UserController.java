package com.example.controllers;

import com.example.dto.CreateUserRequest;
import com.example.dto.UpdateUserRequest;
import com.example.dto.UserResponse;
import com.example.services.UserService;
import com.example.utils.ValidationUtils;
import io.javalin.http.Context;
import java.util.List;

public final class UserController {
    private final UserService userService;

    public UserController(UserService userService) {
        this.userService = userService;
    }

    public void listUsers(Context ctx) {
        List<UserResponse> users = userService.listUsers().stream().map(UserResponse::fromModel).toList();
        ctx.status(200).json(users);
    }

    public void getUserById(Context ctx) {
        long id = ValidationUtils.parseId(ctx.pathParam("id"));
        ctx.status(200).json(UserResponse.fromModel(userService.getUser(id)));
    }

    public void createUser(Context ctx) {
        CreateUserRequest request = ctx.bodyAsClass(CreateUserRequest.class);
        ValidationUtils.validateCreateRequest(request);
        UserResponse created = UserResponse.fromModel(userService.createUser(request));
        ctx.status(201).json(created);
    }

    public void updateUser(Context ctx) {
        long id = ValidationUtils.parseId(ctx.pathParam("id"));
        UpdateUserRequest request = ctx.bodyAsClass(UpdateUserRequest.class);
        ValidationUtils.validateUpdateRequest(request);
        UserResponse updated = UserResponse.fromModel(userService.updateUser(id, request));
        ctx.status(200).json(updated);
    }

    public void deleteUser(Context ctx) {
        long id = ValidationUtils.parseId(ctx.pathParam("id"));
        userService.deleteUser(id);
        ctx.status(204);
    }
}
