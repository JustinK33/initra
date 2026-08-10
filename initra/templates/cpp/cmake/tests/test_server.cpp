// Starts the real server on an ephemeral port and exercises it over HTTP.
#include <cassert>
#include <iostream>
#include <thread>

#include <httplib.h>
#include <nlohmann/json.hpp>

#include "server.h"
#include "user_store.h"

int main() {
  app::UserStore store;
  httplib::Server server;
  app::RegisterRoutes(server, store, app::Config{"0", "test"});

  const int port = server.bind_to_any_port("127.0.0.1");
  std::thread serving([&server] { server.listen_after_bind(); });
  server.wait_until_ready();

  httplib::Client client("127.0.0.1", port);

  auto health = client.Get("/health");
  assert(health && health->status == 200);
  assert(nlohmann::json::parse(health->body)["status"] == "ok");

  auto created = client.Post("/users", R"({"name":"Ada Lovelace","email":"Ada@Example.com"})",
                             "application/json");
  assert(created && created->status == 201);
  assert(nlohmann::json::parse(created->body)["email"] == "ada@example.com");

  auto listed = client.Get("/users");
  assert(listed && listed->status == 200);
  assert(nlohmann::json::parse(listed->body)["users"].size() == 1);

  auto invalid = client.Post("/users", R"({"name":"A","email":"nope"})", "application/json");
  assert(invalid && invalid->status == 400);

  auto missing = client.Get("/users/99");
  assert(missing && missing->status == 404);

  auto removed = client.Delete("/users/1");
  assert(removed && removed->status == 200);

  auto gone = client.Get("/users/1");
  assert(gone && gone->status == 404);

  server.stop();
  serving.join();

  std::cout << "server tests passed" << std::endl;
  return 0;
}
