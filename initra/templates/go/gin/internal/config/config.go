package config

import "os"

// Config holds the runtime settings read from the environment.
type Config struct {
	Port string
	Env  string
}

// Load reads configuration from the environment, applying defaults.
func Load() Config {
	return Config{
		Port: lookup("PORT", "8080"),
		Env:  lookup("APP_ENV", "development"),
	}
}

func lookup(key, fallback string) string {
	if value, ok := os.LookupEnv(key); ok && value != "" {
		return value
	}
	return fallback
}
