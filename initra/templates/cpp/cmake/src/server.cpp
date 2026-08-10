#include "server.h"

#include <cstdlib>
#include <optional>
#include <string>

#include <nlohmann/json.hpp>

namespace app {
namespace {

using nlohmann::json;

std::string Lookup(const char* key, const std::string& fallback) {
  const char* value = std::getenv(key);
  if (value == nullptr || *value == '\0') {
    return fallback;
  }
  return value;
}

json ToJson(const User& user) {
  return json{{"id", user.id}, {"name", user.name}, {"email", user.email}};
}

void SendJson(httplib::Response& res, int status, const json& body) {
  res.status = status;
  res.set_content(body.dump(), "application/json");
}

void SendError(httplib::Response& res, int status, const std::string& message) {
  SendJson(res, status, json{{"error", message}});
}

// Parses an :id path param. Returns nullopt and answers 400 when it is not an int.
std::optional<int> ParseId(const httplib::Request& req, httplib::Response& res) {
  try {
    return std::stoi(req.path_params.at("id"));
  } catch (const std::exception&) {
    SendError(res, 400, "id must be an integer");
    return std::nullopt;
  }
}

// Validates a user payload, answering 400 with the reason when it is invalid.
bool ParseUserPayload(const httplib::Request& req, httplib::Response& res, std::string& name,
                      std::string& email) {
  json body = json::parse(req.body, nullptr, false);
  if (body.is_discarded() || !body.is_object()) {
    SendError(res, 400, "body must be a JSON object");
    return false;
  }

  name = body.value("name", std::string{});
  email = body.value("email", std::string{});
  if (name.size() < 2) {
    SendError(res, 400, "name must be at least 2 characters long");
    return false;
  }
  if (email.find('@') == std::string::npos) {
    SendError(res, 400, "email must be valid");
    return false;
  }
  return true;
}

}  // namespace

Config LoadConfig() {
  return Config{Lookup("PORT", "8080"), Lookup("APP_ENV", "development")};
}

void RegisterRoutes(httplib::Server& server, UserStore& store, const Config& config) {
  const std::string env = config.env;

  server.Get("/health", [env](const httplib::Request&, httplib::Response& res) {
    SendJson(res, 200, json{{"status", "ok"}, {"project", "{{project_name}}"}, {"env", env}});
  });

  server.Get("/users", [&store](const httplib::Request&, httplib::Response& res) {
    json users = json::array();
    for (const User& user : store.List()) {
      users.push_back(ToJson(user));
    }
    SendJson(res, 200, json{{"users", users}});
  });

  server.Post("/users", [&store](const httplib::Request& req, httplib::Response& res) {
    std::string name;
    std::string email;
    if (!ParseUserPayload(req, res, name, email)) {
      return;
    }
    SendJson(res, 201, ToJson(store.Create(name, email)));
  });

  server.Get("/users/:id", [&store](const httplib::Request& req, httplib::Response& res) {
    const std::optional<int> id = ParseId(req, res);
    if (!id.has_value()) {
      return;
    }
    const std::optional<User> user = store.Get(*id);
    if (!user.has_value()) {
      SendError(res, 404, "user not found");
      return;
    }
    SendJson(res, 200, ToJson(*user));
  });

  server.Put("/users/:id", [&store](const httplib::Request& req, httplib::Response& res) {
    const std::optional<int> id = ParseId(req, res);
    if (!id.has_value()) {
      return;
    }
    std::string name;
    std::string email;
    if (!ParseUserPayload(req, res, name, email)) {
      return;
    }
    const std::optional<User> user = store.Update(*id, name, email);
    if (!user.has_value()) {
      SendError(res, 404, "user not found");
      return;
    }
    SendJson(res, 200, ToJson(*user));
  });

  server.Delete("/users/:id", [&store](const httplib::Request& req, httplib::Response& res) {
    const std::optional<int> id = ParseId(req, res);
    if (!id.has_value()) {
      return;
    }
    if (!store.Delete(*id)) {
      SendError(res, 404, "user not found");
      return;
    }
    SendJson(res, 200, json{{"status", "deleted"}});
  });
}

}  // namespace app
