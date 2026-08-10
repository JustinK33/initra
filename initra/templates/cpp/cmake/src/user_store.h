#pragma once

#include <mutex>
#include <optional>
#include <string>
#include <vector>

namespace app {

struct User {
  int id{};
  std::string name;
  std::string email;
};

// In-memory, thread-safe user store.
// ponytail: swap for a database-backed store when you need persistence; the
// server only depends on the methods below.
class UserStore {
 public:
  std::vector<User> List() const;
  std::optional<User> Get(int id) const;
  User Create(const std::string& name, const std::string& email);
  std::optional<User> Update(int id, const std::string& name, const std::string& email);
  bool Delete(int id);

 private:
  mutable std::mutex mutex_;
  std::vector<User> users_;
  int next_id_{1};
};

}  // namespace app
