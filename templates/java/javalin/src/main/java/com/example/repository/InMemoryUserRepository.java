package com.example.repository;

import com.example.models.User;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.List;
import java.util.Optional;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.atomic.AtomicLong;

public final class InMemoryUserRepository implements UserRepository {
    private final ConcurrentHashMap<Long, User> store = new ConcurrentHashMap<>();
    private final AtomicLong sequence = new AtomicLong(0);

    @Override
    public List<User> findAll() {
        List<User> users = new ArrayList<>(store.values());
        users.sort(Comparator.comparingLong(User::id));
        return users;
    }

    @Override
    public Optional<User> findById(long id) {
        return Optional.ofNullable(store.get(id));
    }

    @Override
    public User save(User user) {
        long id = sequence.incrementAndGet();
        User created = new User(id, user.name(), user.email());
        store.put(id, created);
        return created;
    }

    @Override
    public User update(User user) {
        store.put(user.id(), user);
        return user;
    }

    @Override
    public void delete(long id) {
        store.remove(id);
    }
}
