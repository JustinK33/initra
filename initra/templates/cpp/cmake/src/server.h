#pragma once

#include <string>

#include <httplib.h>

#include "user_store.h"

namespace app {

struct Config {
  std::string port;
  std::string env;
};

// Load reads configuration from the environment, applying defaults.
Config LoadConfig();

// RegisterRoutes wires /health and the /users CRUD routes onto the server.
void RegisterRoutes(httplib::Server& server, UserStore& store, const Config& config);

}  // namespace app
