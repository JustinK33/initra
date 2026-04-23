package com.example.config;

public record AppConfig(String env, String databaseUrl, int port) {
    public static AppConfig fromEnvironment() {
        String env = System.getenv().getOrDefault("APP_ENV", "development");
        String databaseUrl = System.getenv().getOrDefault("DATABASE_URL", "sqlite://data/app.db");
        int port = Integer.parseInt(System.getenv().getOrDefault("PORT", "7000"));
        return new AppConfig(env, databaseUrl, port);
    }
}
