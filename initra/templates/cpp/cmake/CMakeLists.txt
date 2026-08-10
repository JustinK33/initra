cmake_minimum_required(VERSION 3.20)
project({{project_name}} CXX)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_EXPORT_COMPILE_COMMANDS ON)

include(FetchContent)

# The first configure downloads these; later builds reuse the cache.
FetchContent_Declare(
  httplib
  GIT_REPOSITORY https://github.com/yhirose/cpp-httplib.git
  GIT_TAG v0.15.3
  GIT_SHALLOW TRUE
)
FetchContent_Declare(
  nlohmann_json
  GIT_REPOSITORY https://github.com/nlohmann/json.git
  GIT_TAG v3.11.3
  GIT_SHALLOW TRUE
)
FetchContent_MakeAvailable(httplib nlohmann_json)

# Application logic lives in a library so tests can link it directly.
add_library({{project_name}}_lib STATIC
  src/server.cpp
  src/user_store.cpp
)
target_include_directories({{project_name}}_lib PUBLIC src)
target_link_libraries({{project_name}}_lib PUBLIC httplib::httplib nlohmann_json::nlohmann_json)

add_executable({{project_name}} src/main.cpp)
target_link_libraries({{project_name}} PRIVATE {{project_name}}_lib)

enable_testing()
add_subdirectory(tests)
