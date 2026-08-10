#include <csignal>
#include <cstdlib>
#include <iostream>
#include <string>

#include <httplib.h>

#include "server.h"
#include "user_store.h"

namespace {

httplib::Server* g_server = nullptr;

void HandleSignal(int) {
  if (g_server != nullptr) {
    g_server->stop();
  }
}

}  // namespace

int main() {
  const app::Config config = app::LoadConfig();
  app::UserStore store;
  httplib::Server server;

  g_server = &server;
  std::signal(SIGINT, HandleSignal);
  std::signal(SIGTERM, HandleSignal);

  app::RegisterRoutes(server, store, config);

  server.set_logger([](const httplib::Request& req, const httplib::Response& res) {
    std::cout << req.method << " " << req.path << " " << res.status << std::endl;
  });

  const int port = std::stoi(config.port);
  std::cout << "{{project_name}} listening on http://localhost:" << port << " (" << config.env << ")"
            << std::endl;
  if (!server.listen("0.0.0.0", port)) {
    std::cerr << "failed to bind port " << port << std::endl;
    return 1;
  }

  std::cout << "server stopped" << std::endl;
  return 0;
}
