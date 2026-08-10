#include "user_store.h"

#include <algorithm>
#include <cctype>

namespace app {
namespace {

std::string ToLower(std::string value) {
  std::transform(value.begin(), value.end(), value.begin(), [](unsigned char c) {
    return static_cast<char>(std::tolower(c));
  });
  return value;
}

}  // namespace

std::vector<User> UserStore::List() const {
  std::lock_guard<std::mutex> lock(mutex_);
  return users_;
}

std::optional<User> UserStore::Get(int id) const {
  std::lock_guard<std::mutex> lock(mutex_);
  for (const User& user : users_) {
    if (user.id == id) {
      return user;
    }
  }
  return std::nullopt;
}

User UserStore::Create(const std::string& name, const std::string& email) {
  std::lock_guard<std::mutex> lock(mutex_);
  User user{next_id_++, name, ToLower(email)};
  users_.push_back(user);
  return user;
}

std::optional<User> UserStore::Update(int id, const std::string& name, const std::string& email) {
  std::lock_guard<std::mutex> lock(mutex_);
  for (User& user : users_) {
    if (user.id == id) {
      user.name = name;
      user.email = ToLower(email);
      return user;
    }
  }
  return std::nullopt;
}

bool UserStore::Delete(int id) {
  std::lock_guard<std::mutex> lock(mutex_);
  const auto it = std::find_if(users_.begin(), users_.end(), [id](const User& user) {
    return user.id == id;
  });
  if (it == users_.end()) {
    return false;
  }
  users_.erase(it);
  return true;
}

}  // namespace app
