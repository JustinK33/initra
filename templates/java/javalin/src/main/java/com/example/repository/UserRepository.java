package com.example.repository;

import com.example.models.User;
import java.util.List;
import java.util.Optional;

public interface UserRepository {
    List<User> findAll();
    Optional<User> findById(long id);
    User save(User user);
    User update(User user);
    void delete(long id);
}
