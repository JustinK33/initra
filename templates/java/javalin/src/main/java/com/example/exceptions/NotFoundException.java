package com.example.exceptions;

public final class NotFoundException extends ApiException {
    public NotFoundException(String message) {
        super(message);
    }
}
