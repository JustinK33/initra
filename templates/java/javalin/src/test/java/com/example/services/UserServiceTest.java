package com.example.services;

import static org.junit.jupiter.api.Assertions.assertEquals;

import com.example.dto.CreateUserRequest;
import com.example.repository.InMemoryUserRepository;
import com.example.repository.UserRepository;
import org.junit.jupiter.api.Test;

class UserServiceTest {
    @Test
    void createAndListUsers() {
        UserRepository repository = new InMemoryUserRepository();
        UserService service = new UserService(repository);

        service.createUser(new CreateUserRequest("Alex", "alex@example.com"));
        service.createUser(new CreateUserRequest("Sam", "sam@example.com"));

        assertEquals(2, service.listUsers().size());
    }
}
