package com.example.utils;

import com.example.dto.CreateUserRequest;
import com.example.dto.UpdateUserRequest;
import com.example.exceptions.ValidationException;

public final class ValidationUtils {
    private ValidationUtils() {}

    public static long parseId(String rawId) {
        try {
            long value = Long.parseLong(rawId);
            if (value <= 0) {
                throw new ValidationException("id must be greater than zero");
            }
            return value;
        } catch (NumberFormatException exception) {
            throw new ValidationException("id must be a number");
        }
    }

    public static void validateCreateRequest(CreateUserRequest request) {
        if (request == null) {
            throw new ValidationException("Request body is required");
        }
        requireName(request.name());
        requireEmail(request.email());
    }

    public static void validateUpdateRequest(UpdateUserRequest request) {
        if (request == null) {
            throw new ValidationException("Request body is required");
        }
        if (request.name() == null && request.email() == null) {
            throw new ValidationException("At least one field is required for update");
        }
        if (request.name() != null) {
            requireName(request.name());
        }
        if (request.email() != null) {
            requireEmail(request.email());
        }
    }

    private static void requireName(String value) {
        if (value == null || value.trim().length() < 2) {
            throw new ValidationException("name must be at least 2 characters");
        }
    }

    private static void requireEmail(String value) {
        if (value == null || !value.contains("@")) {
            throw new ValidationException("email must be valid");
        }
    }
}
