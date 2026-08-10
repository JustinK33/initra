package handlers

import (
	"errors"
	"net/http"
	"strconv"

	"github.com/gin-gonic/gin"

	"{{project_name}}/internal/models"
	"{{project_name}}/internal/store"
)

// Users bundles the handlers that operate on the user store.
type Users struct {
	store *store.UserStore
}

// NewUsers returns handlers backed by the given store.
func NewUsers(s *store.UserStore) *Users {
	return &Users{store: s}
}

// List handles GET /users.
func (h *Users) List(c *gin.Context) {
	c.JSON(http.StatusOK, gin.H{"users": h.store.List()})
}

// Get handles GET /users/:id.
func (h *Users) Get(c *gin.Context) {
	id, ok := parseID(c)
	if !ok {
		return
	}

	user, err := h.store.Get(id)
	if err != nil {
		respondStoreError(c, err)
		return
	}
	c.JSON(http.StatusOK, user)
}

// Create handles POST /users.
func (h *Users) Create(c *gin.Context) {
	var req models.CreateUserRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}
	c.JSON(http.StatusCreated, h.store.Create(req.Name, req.Email))
}

// Update handles PUT /users/:id.
func (h *Users) Update(c *gin.Context) {
	id, ok := parseID(c)
	if !ok {
		return
	}

	var req models.UpdateUserRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	user, err := h.store.Update(id, req.Name, req.Email)
	if err != nil {
		respondStoreError(c, err)
		return
	}
	c.JSON(http.StatusOK, user)
}

// Delete handles DELETE /users/:id.
func (h *Users) Delete(c *gin.Context) {
	id, ok := parseID(c)
	if !ok {
		return
	}

	if err := h.store.Delete(id); err != nil {
		respondStoreError(c, err)
		return
	}
	c.JSON(http.StatusOK, gin.H{"status": "deleted"})
}

func parseID(c *gin.Context) (int, bool) {
	id, err := strconv.Atoi(c.Param("id"))
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "id must be an integer"})
		return 0, false
	}
	return id, true
}

func respondStoreError(c *gin.Context, err error) {
	if errors.Is(err, store.ErrNotFound) {
		c.JSON(http.StatusNotFound, gin.H{"error": err.Error()})
		return
	}
	c.JSON(http.StatusInternalServerError, gin.H{"error": "internal error"})
}
