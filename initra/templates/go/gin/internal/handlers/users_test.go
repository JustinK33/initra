package handlers_test

import (
	"bytes"
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"testing"

	"github.com/gin-gonic/gin"

	"{{project_name}}/internal/config"
	"{{project_name}}/internal/router"
)

func newTestRouter() *gin.Engine {
	gin.SetMode(gin.TestMode)
	return router.New(config.Config{Port: "8080", Env: "test"})
}

func do(t *testing.T, engine *gin.Engine, method, path string, body any) *httptest.ResponseRecorder {
	t.Helper()

	var reader *bytes.Reader
	if body != nil {
		encoded, err := json.Marshal(body)
		if err != nil {
			t.Fatalf("marshal body: %v", err)
		}
		reader = bytes.NewReader(encoded)
	} else {
		reader = bytes.NewReader(nil)
	}

	req := httptest.NewRequest(method, path, reader)
	req.Header.Set("Content-Type", "application/json")
	recorder := httptest.NewRecorder()
	engine.ServeHTTP(recorder, req)
	return recorder
}

func TestHealthReturnsOK(t *testing.T) {
	res := do(t, newTestRouter(), http.MethodGet, "/health", nil)

	if res.Code != http.StatusOK {
		t.Fatalf("expected 200, got %d", res.Code)
	}

	var payload map[string]string
	if err := json.Unmarshal(res.Body.Bytes(), &payload); err != nil {
		t.Fatalf("decode body: %v", err)
	}
	if payload["status"] != "ok" {
		t.Fatalf("expected status ok, got %q", payload["status"])
	}
}

func TestUserCRUD(t *testing.T) {
	engine := newTestRouter()

	created := do(t, engine, http.MethodPost, "/users", map[string]string{
		"name":  "Ada Lovelace",
		"email": "Ada@Example.com",
	})
	if created.Code != http.StatusCreated {
		t.Fatalf("expected 201, got %d (%s)", created.Code, created.Body)
	}

	var user struct {
		ID    int    `json:"id"`
		Email string `json:"email"`
	}
	if err := json.Unmarshal(created.Body.Bytes(), &user); err != nil {
		t.Fatalf("decode created user: %v", err)
	}
	if user.Email != "ada@example.com" {
		t.Fatalf("expected email to be lowercased, got %q", user.Email)
	}

	fetched := do(t, engine, http.MethodGet, "/users/1", nil)
	if fetched.Code != http.StatusOK {
		t.Fatalf("expected 200 for existing user, got %d", fetched.Code)
	}

	deleted := do(t, engine, http.MethodDelete, "/users/1", nil)
	if deleted.Code != http.StatusOK {
		t.Fatalf("expected 200 on delete, got %d", deleted.Code)
	}

	missing := do(t, engine, http.MethodGet, "/users/1", nil)
	if missing.Code != http.StatusNotFound {
		t.Fatalf("expected 404 after delete, got %d", missing.Code)
	}
}

func TestCreateUserRejectsInvalidPayload(t *testing.T) {
	res := do(t, newTestRouter(), http.MethodPost, "/users", map[string]string{
		"name":  "A",
		"email": "not-an-email",
	})

	if res.Code != http.StatusBadRequest {
		t.Fatalf("expected 400, got %d", res.Code)
	}
}
