package com.example.services;

import com.example.dto.CreateUserRequest;
import com.example.dto.UpdateUserRequest;
import com.example.exceptions.NotFoundException;
import com.example.models.User;
import com.example.repository.UserRepository;
import java.util.List;

public final class UserService {
    private final UserRepository userRepository;

    public UserService(UserRepository userRepository) {
        this.userRepository = userRepository;
    }

    public List<User> listUsers() {
        return userRepository.findAll();
    }

    public User getUser(long id) {
        return userRepository.findById(id).orElseThrow(() -> new NotFoundException("User not found: " + id));
    }

    public User createUser(CreateUserRequest request) {
        User user = new User(0L, request.name().trim(), request.email().trim().toLowerCase());
        return userRepository.save(user);
    }

    public User updateUser(long id, UpdateUserRequest request) {
        User existing = getUser(id);
        String nextName = request.name() == null ? existing.name() : request.name().trim();
        String nextEmail = request.email() == null ? existing.email() : request.email().trim().toLowerCase();
        return userRepository.update(new User(existing.id(), nextName, nextEmail));
    }

    public void deleteUser(long id) {
        getUser(id);
        userRepository.delete(id);
    }
}
