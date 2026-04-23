package com.example.exceptions;

public final class ValidationException extends ApiException {
    public ValidationException(String message) {
        super(message);
    }
}
