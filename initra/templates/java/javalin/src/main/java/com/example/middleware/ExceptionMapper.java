package com.example.middleware;

import com.example.exceptions.NotFoundException;
import com.example.exceptions.ValidationException;
import io.javalin.Javalin;
import java.time.Instant;

public final class ExceptionMapper {
    private ExceptionMapper() {}

    public static void register(Javalin app) {
        app.exception(ValidationException.class, (e, ctx) ->
            ctx.status(400).json(new ErrorResponse("validation_error", e.getMessage(), Instant.now().toString())));

        app.exception(NotFoundException.class, (e, ctx) ->
            ctx.status(404).json(new ErrorResponse("not_found", e.getMessage(), Instant.now().toString())));

        app.exception(Exception.class, (e, ctx) ->
            ctx.status(500).json(new ErrorResponse("internal_error", "Unexpected server error", Instant.now().toString())));
    }

    public record ErrorResponse(String code, String message, String timestamp) {}
}
