package main

import (
	"context"
	"errors"
	"log"
	"net/http"
	"os"
	"os/signal"
	"syscall"
	"time"

	"{{project_name}}/internal/config"
	"{{project_name}}/internal/router"
)

func main() {
	cfg := config.Load()

	server := &http.Server{
		Addr:              ":" + cfg.Port,
		Handler:           router.New(cfg),
		ReadHeaderTimeout: 10 * time.Second,
	}

	go func() {
		log.Printf("{{project_name}} listening on http://localhost:%s (%s)", cfg.Port, cfg.Env)
		if err := server.ListenAndServe(); err != nil && !errors.Is(err, http.ErrServerClosed) {
			log.Fatalf("server error: %v", err)
		}
	}()

	quit := make(chan os.Signal, 1)
	signal.Notify(quit, syscall.SIGINT, syscall.SIGTERM)
	<-quit

	ctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
	defer cancel()
	if err := server.Shutdown(ctx); err != nil {
		log.Fatalf("shutdown error: %v", err)
	}
	log.Println("server stopped")
}
