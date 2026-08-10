package router

import (
	"github.com/gin-gonic/gin"

	"{{project_name}}/internal/config"
	"{{project_name}}/internal/handlers"
	"{{project_name}}/internal/middleware"
	"{{project_name}}/internal/store"
)

// New builds the HTTP router with all routes and middleware wired up.
func New(cfg config.Config) *gin.Engine {
	engine := gin.New()
	engine.Use(gin.Recovery(), middleware.Logger())

	users := handlers.NewUsers(store.NewUserStore())

	engine.GET("/health", handlers.Health(cfg))
	engine.GET("/users", users.List)
	engine.POST("/users", users.Create)
	engine.GET("/users/:id", users.Get)
	engine.PUT("/users/:id", users.Update)
	engine.DELETE("/users/:id", users.Delete)

	return engine
}
