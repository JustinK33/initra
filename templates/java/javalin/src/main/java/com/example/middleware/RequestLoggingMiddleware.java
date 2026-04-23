package com.example.middleware;

import io.javalin.Javalin;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public final class RequestLoggingMiddleware {
    private static final Logger logger = LoggerFactory.getLogger(RequestLoggingMiddleware.class);

    private RequestLoggingMiddleware() {}

    public static void register(Javalin app) {
        app.before(ctx -> logger.info("{} {}", ctx.method(), ctx.path()));
    }
}
