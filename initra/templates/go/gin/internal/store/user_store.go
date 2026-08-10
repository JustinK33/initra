package store

import (
	"errors"
	"strings"
	"sync"

	"{{project_name}}/internal/models"
)

// ErrNotFound is returned when a user id does not exist.
var ErrNotFound = errors.New("user not found")

// UserStore is an in-memory, concurrency-safe user store.
// ponytail: swap this for a database-backed implementation when you need one;
// the handlers only depend on the methods below.
type UserStore struct {
	mu     sync.RWMutex
	users  []models.User
	nextID int
}

// NewUserStore returns an empty store.
func NewUserStore() *UserStore {
	return &UserStore{nextID: 1}
}

// List returns a copy of every stored user.
func (s *UserStore) List() []models.User {
	s.mu.RLock()
	defer s.mu.RUnlock()

	out := make([]models.User, len(s.users))
	copy(out, s.users)
	return out
}

// Get returns the user with the given id, or ErrNotFound.
func (s *UserStore) Get(id int) (models.User, error) {
	s.mu.RLock()
	defer s.mu.RUnlock()

	for _, user := range s.users {
		if user.ID == id {
			return user, nil
		}
	}
	return models.User{}, ErrNotFound
}

// Create stores a new user and returns it with its assigned id.
func (s *UserStore) Create(name, email string) models.User {
	s.mu.Lock()
	defer s.mu.Unlock()

	user := models.User{ID: s.nextID, Name: name, Email: strings.ToLower(email)}
	s.nextID++
	s.users = append(s.users, user)
	return user
}

// Update replaces the name and email of an existing user.
func (s *UserStore) Update(id int, name, email string) (models.User, error) {
	s.mu.Lock()
	defer s.mu.Unlock()

	for i := range s.users {
		if s.users[i].ID == id {
			s.users[i].Name = name
			s.users[i].Email = strings.ToLower(email)
			return s.users[i], nil
		}
	}
	return models.User{}, ErrNotFound
}

// Delete removes a user by id.
func (s *UserStore) Delete(id int) error {
	s.mu.Lock()
	defer s.mu.Unlock()

	for i := range s.users {
		if s.users[i].ID == id {
			s.users = append(s.users[:i], s.users[i+1:]...)
			return nil
		}
	}
	return ErrNotFound
}
