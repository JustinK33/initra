package com.example.config;

import java.io.IOException;
import java.io.InputStream;
import java.util.Properties;

public record AppConfig(String appName, String env, int port) {
    public static AppConfig fromEnvironment() {
        Properties properties = new Properties();
        try (InputStream in = AppConfig.class.getClassLoader().getResourceAsStream("application.properties")) {
            if (in != null) {
                properties.load(in);
            }
        } catch (IOException ignored) {
            // Fall back to defaults and env vars.
        }

        String appName = get("APP_NAME", "app.name", "{{project_name}}", properties);
        String env = get("APP_ENV", "app.env", "development", properties);
        int port = Integer.parseInt(get("APP_PORT", "app.port", "7000", properties));

        return new AppConfig(appName, env, port);
    }

    private static String get(String envName, String propertyName, String fallback, Properties properties) {
        String fromEnv = System.getenv(envName);
        if (fromEnv != null && !fromEnv.isBlank()) {
            return fromEnv;
        }
        return properties.getProperty(propertyName, fallback);
    }
}
