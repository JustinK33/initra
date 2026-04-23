package com.example.dto;

import com.example.models.User;

public record UserResponse(long id, String name, String email) {
    public static UserResponse fromModel(User user) {
        return new UserResponse(user.id(), user.name(), user.email());
    }
}
