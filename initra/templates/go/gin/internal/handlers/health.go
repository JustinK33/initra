package handlers

import (
	"net/http"

	"github.com/gin-gonic/gin"

	"{{project_name}}/internal/config"
)

// Health responds with a liveness payload.
func Health(cfg config.Config) gin.HandlerFunc {
	return func(c *gin.Context) {
		c.JSON(http.StatusOK, gin.H{
			"status":  "ok",
			"project": "{{project_name}}",
			"env":     cfg.Env,
		})
	}
}
